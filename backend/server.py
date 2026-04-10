from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, UploadFile, File, Header, Query
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
import base64
import requests
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone, timedelta

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Emergent LLM Key
EMERGENT_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Object Storage
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
APP_NAME = "pantry-pulse"
storage_key = None

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== OBJECT STORAGE ==========
def init_storage():
    global storage_key
    if storage_key:
        return storage_key
    resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
    resp.raise_for_status()
    storage_key = resp.json()["storage_key"]
    return storage_key

def put_object(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data, timeout=120
    )
    resp.raise_for_status()
    return resp.json()

def get_object(path: str):
    key = init_storage()
    resp = requests.get(f"{STORAGE_URL}/objects/{path}", headers={"X-Storage-Key": key}, timeout=60)
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")

# ========== MODELS ==========
class UserProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    allergies: List[str] = []
    dietary_preferences: List[str] = []
    skill_level: str = "beginner"
    default_servings: int = 2
    calorie_target: Optional[int] = None
    created_at: str = ""

class PantryItemCreate(BaseModel):
    name: str
    category: str = "other"
    quantity: Optional[str] = None
    unit: Optional[str] = None
    expiry_date: Optional[str] = None
    notes: Optional[str] = None

class PantryItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[str] = None
    unit: Optional[str] = None
    expiry_date: Optional[str] = None
    notes: Optional[str] = None

class RecipeGenerateRequest(BaseModel):
    ingredients: List[str] = []
    max_time: Optional[int] = None
    budget: Optional[str] = None
    skill_level: Optional[str] = None
    dietary_restrictions: List[str] = []
    servings: int = 2
    calorie_target: Optional[int] = None
    cuisine: Optional[str] = None
    meal_type: Optional[str] = None

class GroceryRequest(BaseModel):
    pantry_ingredients: List[str] = []
    preferences: List[str] = []
    budget: Optional[str] = None

# ========== AUTH HELPERS ==========
async def get_current_user(request: Request):
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header[7:]
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    expires_at = session["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ========== AUTH ROUTES ==========
@api_router.post("/auth/session")
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
    email = data.get("email")
    name = data.get("name")
    picture = data.get("picture")
    session_token = data.get("session_token")
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    if existing_user:
        user_id = existing_user["user_id"]
        await db.users.update_one({"email": email}, {"$set": {"name": name, "picture": picture}})
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        await db.users.insert_one({
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "allergies": [],
            "dietary_preferences": [],
            "skill_level": "beginner",
            "default_servings": 2,
            "calorie_target": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    resp = JSONResponse(content={
        "user_id": user_id, "email": email, "name": name, "picture": picture
    })
    resp.set_cookie(
        key="session_token", value=session_token,
        httponly=True, secure=True, samesite="none",
        path="/", max_age=7*24*60*60
    )
    return resp

@api_router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    return user

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    resp = JSONResponse(content={"message": "Logged out"})
    resp.delete_cookie(key="session_token", path="/", secure=True, samesite="none")
    return resp

# ========== PANTRY ROUTES ==========
@api_router.get("/pantry")
async def get_pantry(request: Request):
    user = await get_current_user(request)
    items = await db.pantry_items.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(500)
    return items

@api_router.post("/pantry")
async def add_pantry_item(item: PantryItemCreate, request: Request):
    user = await get_current_user(request)
    doc = {
        "item_id": f"item_{uuid.uuid4().hex[:12]}",
        "user_id": user["user_id"],
        "name": item.name,
        "category": item.category,
        "quantity": item.quantity,
        "unit": item.unit,
        "expiry_date": item.expiry_date,
        "notes": item.notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.pantry_items.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api_router.post("/pantry/bulk")
async def add_pantry_items_bulk(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    items = body.get("items", [])
    added = []
    for item in items:
        doc = {
            "item_id": f"item_{uuid.uuid4().hex[:12]}",
            "user_id": user["user_id"],
            "name": item.get("name", "Unknown"),
            "category": item.get("category", "other"),
            "quantity": item.get("quantity"),
            "unit": item.get("unit"),
            "expiry_date": item.get("expiry_date"),
            "notes": item.get("notes"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.pantry_items.insert_one(doc)
        doc.pop("_id", None)
        added.append(doc)
    return {"added": added, "count": len(added)}

@api_router.put("/pantry/{item_id}")
async def update_pantry_item(item_id: str, item: PantryItemUpdate, request: Request):
    user = await get_current_user(request)
    update_data = {k: v for k, v in item.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await db.pantry_items.update_one(
        {"item_id": item_id, "user_id": user["user_id"]}, {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    updated = await db.pantry_items.find_one({"item_id": item_id}, {"_id": 0})
    return updated

@api_router.delete("/pantry/{item_id}")
async def delete_pantry_item(item_id: str, request: Request):
    user = await get_current_user(request)
    result = await db.pantry_items.delete_one({"item_id": item_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Deleted"}

# ========== RECIPE GENERATION ==========
@api_router.post("/recipes/generate")
async def generate_recipes(req: RecipeGenerateRequest, request: Request):
    user = await get_current_user(request)
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    ingredients_str = ", ".join(req.ingredients) if req.ingredients else "whatever is available"
    filters = []
    if req.max_time:
        filters.append(f"Must be ready in under {req.max_time} minutes.")
    if req.budget:
        filters.append(f"Budget level: {req.budget}.")
    if req.skill_level:
        filters.append(f"Skill level: {req.skill_level}.")
    if req.dietary_restrictions:
        filters.append(f"Dietary restrictions: {', '.join(req.dietary_restrictions)}.")
    if req.calorie_target:
        filters.append(f"Target around {req.calorie_target} calories per serving.")
    if req.cuisine:
        filters.append(f"Cuisine preference: {req.cuisine}.")
    if req.meal_type:
        filters.append(f"Meal type: {req.meal_type}.")
    user_allergies = user.get("allergies", [])
    if user_allergies:
        filters.append(f"User is allergic to: {', '.join(user_allergies)}. AVOID these completely.")
    user_dietary = user.get("dietary_preferences", [])
    if user_dietary:
        filters.append(f"User dietary preferences: {', '.join(user_dietary)}.")
    filters_str = "\n".join(filters) if filters else "No special filters."
    prompt = f"""Generate exactly 3 recipes using these ingredients: {ingredients_str}

Servings: {req.servings}

Filters:
{filters_str}

For each recipe, respond in this exact JSON format (no markdown, no extra text):
[
  {{
    "title": "Recipe Name",
    "description": "Brief appetizing description",
    "prep_time": 10,
    "cook_time": 20,
    "total_time": 30,
    "servings": {req.servings},
    "difficulty": "easy",
    "calories_per_serving": 350,
    "ingredients_used": ["ingredient1", "ingredient2"],
    "ingredients_needed": ["extra ingredient if any"],
    "instructions": ["Step 1...", "Step 2...", "Step 3..."],
    "tips": "A helpful cooking tip",
    "cuisine": "Italian",
    "meal_type": "dinner",
    "tags": ["quick", "budget-friendly"]
  }}
]

Be creative but practical. Use real cooking techniques. If some ingredients are missing, suggest minimal additions."""

    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"recipe_{uuid.uuid4().hex[:8]}",
        system_message="You are a world-class chef and recipe creator. Generate practical, delicious recipes. Always respond with valid JSON only, no markdown formatting."
    )
    chat.with_model("openai", "gpt-5.2")
    user_msg = UserMessage(text=prompt)
    response = await chat.send_message(user_msg)
    import json
    try:
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()
        recipes = json.loads(clean)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse recipe JSON: {response[:200]}")
        recipes = [{"title": "AI Generated Recipe", "description": response[:200], "instructions": [response], "ingredients_used": req.ingredients, "ingredients_needed": [], "total_time": 30, "servings": req.servings, "difficulty": "medium", "calories_per_serving": 0, "tips": "", "cuisine": "", "meal_type": "", "tags": [], "prep_time": 0, "cook_time": 0}]
    for recipe in recipes:
        recipe["recipe_id"] = f"rec_{uuid.uuid4().hex[:12]}"
    return {"recipes": recipes}

# ========== SAVED RECIPES ==========
@api_router.get("/recipes/saved")
async def get_saved_recipes(request: Request):
    user = await get_current_user(request)
    recipes = await db.saved_recipes.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(100)
    return recipes

@api_router.post("/recipes/save")
async def save_recipe(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    recipe = body.get("recipe", {})
    recipe["saved_id"] = f"saved_{uuid.uuid4().hex[:12]}"
    recipe["user_id"] = user["user_id"]
    recipe["saved_at"] = datetime.now(timezone.utc).isoformat()
    await db.saved_recipes.insert_one(recipe)
    recipe.pop("_id", None)
    return recipe

@api_router.delete("/recipes/saved/{saved_id}")
async def delete_saved_recipe(saved_id: str, request: Request):
    user = await get_current_user(request)
    result = await db.saved_recipes.delete_one({"saved_id": saved_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return {"message": "Deleted"}

# ========== SCAN ROUTES ==========
@api_router.post("/scan/photo")
async def scan_photo(request: Request, file: UploadFile = File(...)):
    user = await get_current_user(request)
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
    data = await file.read()
    b64 = base64.b64encode(data).decode("utf-8")
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    storage_path = f"{APP_NAME}/uploads/{user['user_id']}/{uuid.uuid4()}.{ext}"
    try:
        put_object(storage_path, data, file.content_type or "image/jpeg")
    except Exception as e:
        logger.warning(f"Storage upload failed: {e}")
    image_content = ImageContent(image_base64=b64)
    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"scan_{uuid.uuid4().hex[:8]}",
        system_message="You are a food identification expert. Identify food items and ingredients from images. Always respond with valid JSON only."
    )
    chat.with_model("openai", "gpt-5.2")
    user_msg = UserMessage(
        text="""Identify all food items and ingredients visible in this image.
Respond in this exact JSON format:
{
  "items": [
    {"name": "item name", "category": "protein/dairy/vegetable/fruit/grain/spice/condiment/other", "quantity": "estimated quantity or null"}
  ],
  "confidence": "high/medium/low"
}""",
        file_contents=[image_content]
    )
    response = await chat.send_message(user_msg)
    import json
    try:
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()
        result = json.loads(clean)
    except json.JSONDecodeError:
        result = {"items": [], "confidence": "low", "raw": response[:300]}
    return result

@api_router.post("/scan/receipt")
async def scan_receipt(request: Request, file: UploadFile = File(...)):
    user = await get_current_user(request)
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
    data = await file.read()
    b64 = base64.b64encode(data).decode("utf-8")
    image_content = ImageContent(image_base64=b64)
    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"receipt_{uuid.uuid4().hex[:8]}",
        system_message="You are a receipt reading expert. Extract food items from grocery receipts. Always respond with valid JSON only."
    )
    chat.with_model("openai", "gpt-5.2")
    user_msg = UserMessage(
        text="""Read this grocery receipt and extract all food items.
Respond in this exact JSON format:
{
  "items": [
    {"name": "item name", "category": "protein/dairy/vegetable/fruit/grain/spice/condiment/beverage/snack/other", "price": "price or null", "quantity": "quantity or null"}
  ],
  "store_name": "store name or null",
  "total": "total amount or null"
}""",
        file_contents=[image_content]
    )
    response = await chat.send_message(user_msg)
    import json
    try:
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()
        result = json.loads(clean)
    except json.JSONDecodeError:
        result = {"items": [], "store_name": None, "total": None, "raw": response[:300]}
    return result

# ========== GROCERY SUGGESTIONS ==========
@api_router.post("/grocery/suggestions")
async def get_grocery_suggestions(req: GroceryRequest, request: Request):
    user = await get_current_user(request)
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    pantry_str = ", ".join(req.pantry_ingredients) if req.pantry_ingredients else "mostly empty pantry"
    prefs = ", ".join(req.preferences) if req.preferences else "no specific preferences"
    prompt = f"""Given a pantry with: {pantry_str}
User preferences: {prefs}
Budget: {req.budget or "moderate"}
User allergies: {', '.join(user.get('allergies', [])) or 'none'}

Suggest grocery items to buy that would complement existing ingredients and enable multiple meals.
Respond in this exact JSON format:
{{
  "suggestions": [
    {{
      "name": "item name",
      "category": "protein/dairy/vegetable/fruit/grain/spice/condiment/other",
      "reason": "why to buy this",
      "recipes_enabled": ["recipe name 1", "recipe name 2"],
      "estimated_cost": "low/medium/high",
      "priority": "high/medium/low"
    }}
  ],
  "meal_plan_preview": "Brief description of meals possible with these additions"
}}"""
    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"grocery_{uuid.uuid4().hex[:8]}",
        system_message="You are a smart grocery shopping assistant. Suggest practical, budget-conscious grocery items. Always respond with valid JSON only."
    )
    chat.with_model("openai", "gpt-5.2")
    user_msg = UserMessage(text=prompt)
    response = await chat.send_message(user_msg)
    import json
    try:
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()
        result = json.loads(clean)
    except json.JSONDecodeError:
        result = {"suggestions": [], "meal_plan_preview": response[:300]}
    return result

# ========== PROFILE ROUTES ==========
@api_router.get("/profile")
async def get_profile(request: Request):
    user = await get_current_user(request)
    return user

@api_router.put("/profile")
async def update_profile(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    allowed = ["allergies", "dietary_preferences", "skill_level", "default_servings", "calorie_target", "name"]
    update_data = {k: v for k, v in body.items() if k in allowed}
    if update_data:
        await db.users.update_one({"user_id": user["user_id"]}, {"$set": update_data})
    updated = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
    return updated

# ========== STATS ==========
@api_router.get("/stats")
async def get_stats(request: Request):
    user = await get_current_user(request)
    uid = user["user_id"]
    pantry_count = await db.pantry_items.count_documents({"user_id": uid})
    saved_count = await db.saved_recipes.count_documents({"user_id": uid})
    expiring_items = await db.pantry_items.find(
        {"user_id": uid, "expiry_date": {"$ne": None}}, {"_id": 0}
    ).to_list(500)
    expiring_soon = []
    now = datetime.now(timezone.utc)
    for item in expiring_items:
        try:
            exp = datetime.fromisoformat(item["expiry_date"])
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if (exp - now).days <= 3 and (exp - now).days >= 0:
                item["days_left"] = (exp - now).days
                expiring_soon.append(item)
        except (ValueError, TypeError):
            pass
    categories = {}
    items = await db.pantry_items.find({"user_id": uid}, {"_id": 0}).to_list(500)
    for item in items:
        cat = item.get("category", "other")
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "pantry_count": pantry_count,
        "saved_recipes_count": saved_count,
        "expiring_soon": expiring_soon,
        "categories": categories
    }

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    try:
        init_storage()
        logger.info("Object storage initialized")
    except Exception as e:
        logger.warning(f"Storage init failed (non-critical): {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
