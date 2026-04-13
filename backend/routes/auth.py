from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse
import uuid
import requests
import logging
from datetime import datetime, timezone, timedelta

from core.database import db
from core.auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, set_auth_cookies,
    get_current_user, check_brute_force, record_failed_attempt,
    JWT_SECRET, JWT_ALGORITHM,
)
import jwt as pyjwt
from models.schemas import AuthRegister, AuthLogin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


# --- Standard Email/Password Auth ---

@router.post("/register")
async def register_user(body: AuthRegister):
    email = body.email.strip().lower()
    if not email or not body.password:
        raise HTTPException(status_code=400, detail="Email and password required")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_doc = {
        "user_id": user_id, "email": email, "name": body.name.strip(),
        "password_hash": hash_password(body.password),
        "picture": None, "auth_type": "email",
        "allergies": [], "dietary_preferences": [], "skill_level": "beginner",
        "default_servings": 2, "calorie_target": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    resp_data = {"user_id": user_id, "email": email, "name": body.name.strip(), "picture": None}
    resp = JSONResponse(content=resp_data)
    set_auth_cookies(resp, access_token, refresh_token)
    return resp


@router.post("/login")
async def login_user(body: AuthLogin, request: Request):
    email = body.email.strip().lower()
    ip = request.client.host if request.client else "unknown"
    identifier = f"{ip}:{email}"
    await check_brute_force(identifier)
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user or not user.get("password_hash"):
        await record_failed_attempt(identifier)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(body.password, user["password_hash"]):
        await record_failed_attempt(identifier)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    await db.login_attempts.delete_one({"identifier": identifier})
    access_token = create_access_token(user["user_id"], email)
    refresh_token = create_refresh_token(user["user_id"])
    resp_data = {"user_id": user["user_id"], "email": email, "name": user.get("name", ""), "picture": user.get("picture")}
    resp = JSONResponse(content=resp_data)
    set_auth_cookies(resp, access_token, refresh_token)
    return resp


@router.post("/refresh")
async def refresh_token(request: Request):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"user_id": payload["sub"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        new_access = create_access_token(payload["sub"], user["email"])
        resp = JSONResponse(content={"message": "Token refreshed"})
        resp.set_cookie(key="access_token", value=new_access, httponly=True, secure=True, samesite="none", max_age=900, path="/")
        return resp
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


# --- Google OAuth Session Exchange ---

async def get_or_create_user(email, name, picture):
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    if existing_user:
        await db.users.update_one({"email": email}, {"$set": {"name": name, "picture": picture}})
        return existing_user["user_id"]
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    await db.users.insert_one({
        "user_id": user_id, "email": email, "name": name, "picture": picture,
        "allergies": [], "dietary_preferences": [], "skill_level": "beginner",
        "default_servings": 2, "calorie_target": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    return user_id


@router.post("/session")
async def exchange_session(request: Request, response: Response):
    body = await request.json()
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    try:
        resp = requests.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")
    email, name, picture = data.get("email"), data.get("name"), data.get("picture")
    session_token = data.get("session_token")
    user_id = await get_or_create_user(email, name, picture)
    await db.user_sessions.insert_one({
        "user_id": user_id, "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    resp = JSONResponse(content={"user_id": user_id, "email": email, "name": name, "picture": picture})
    resp.set_cookie(key="session_token", value=session_token, httponly=True, secure=True, samesite="none", path="/", max_age=7*24*60*60)
    return resp


@router.get("/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    return user


@router.post("/logout")
async def logout(request: Request):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    resp = JSONResponse(content={"message": "Logged out"})
    resp.delete_cookie(key="session_token", path="/", secure=True, samesite="none")
    resp.delete_cookie(key="access_token", path="/", secure=True, samesite="none")
    resp.delete_cookie(key="refresh_token", path="/", secure=True, samesite="none")
    return resp
