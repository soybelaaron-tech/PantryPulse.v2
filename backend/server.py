from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import os
import uuid
import logging
from datetime import datetime, timezone

from core.database import db, client
from core.auth import hash_password, verify_password
from core.storage import init_storage

from routes.auth import router as auth_router
from routes.pantry import router as pantry_router
from routes.recipes import router as recipes_router
from routes.scan import router as scan_router
from routes.grocery import router as grocery_router
from routes.mealplan import router as mealplan_router
from routes.profile import router as profile_router

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Include all routers
app.include_router(auth_router)
app.include_router(pantry_router)
app.include_router(recipes_router)
app.include_router(scan_router)
app.include_router(grocery_router)
app.include_router(mealplan_router)
app.include_router(profile_router)

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
    # Create indexes
    try:
        await db.users.create_index("email", unique=True)
        await db.login_attempts.create_index("identifier")
        logger.info("MongoDB indexes created")
    except Exception as e:
        logger.warning(f"Index creation: {e}")
    # Seed admin user
    try:
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@pantrypulse.com")
        admin_password = os.environ.get("ADMIN_PASSWORD", "PantryPulse2024!")
        existing = await db.users.find_one({"email": admin_email}, {"_id": 0})
        if not existing:
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            await db.users.insert_one({
                "user_id": user_id, "email": admin_email,
                "password_hash": hash_password(admin_password),
                "name": "Admin", "picture": None, "auth_type": "email",
                "role": "admin", "allergies": [], "dietary_preferences": [],
                "skill_level": "beginner", "default_servings": 2, "calorie_target": None,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            logger.info(f"Admin user seeded: {admin_email}")
        elif existing and not verify_password(admin_password, existing.get("password_hash", "")):
            await db.users.update_one(
                {"email": admin_email},
                {"$set": {"password_hash": hash_password(admin_password)}}
            )
            logger.info("Admin password updated")
    except Exception as e:
        logger.warning(f"Admin seed: {e}")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
