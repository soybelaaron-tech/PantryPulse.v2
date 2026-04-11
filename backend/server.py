from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, UploadFile, File, Header, Query
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
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

# ========== HELPER FUNCTIONS ==========
def parse_ai_json(response_text: str):
    """Parse AI response that may contain markdown code fences."""
    clean = response_text.strip()
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()
    return json.loads(clean)


def build_recipe_filters(req, user: dict) -> str:
    """Build filter string from recipe request and user profile."""
    filter_map = {
        req.max_time: lambda v: f"Must be ready in under {v} minutes.",
        req.budget: lambda v: f"Budget level: {v}.",
        req.skill_level: lambda v: f"Skill level: {v}.",
        req.calorie_target: lambda v: f"Target around {v} calories per serving.",
        req.cuisine: lambda v: f"Cuisine preference: {v}.",
        req.meal_type: lambda v: f"Meal type: {v}.",
    }
    filters = [fn(val) for val, fn in filter_map.items() if val]
    if req.dietary_restrictions:
        filters.append(f"Dietary restrictions: {', '.join(req.dietary_restrictions)}.")
    user_allergies = user.get("allergies", [])
    if user_allergies:
        filters.append(f"User is allergic to: {', '.join(user_allergies)}. AVOID these completely.")
    user_dietary = user.get("dietary_preferences", [])
    if user_dietary:
        filters.append(f"User dietary preferences: {', '.join(user_dietary)}.")
    return "\n".join(filters) if filters else "No special filters."


def build_user_constraints(user: dict) -> str:
    """Build constraint string from user profile for meal planning."""
    constraints = []
    allergies = user.get("allergies", [])
    dietary = user.get("dietary_preferences", [])
    cal_target = user.get("calorie_target")
    if allergies:
        constraints.append(f"Allergies (AVOID completely): {', '.join(allergies)}")
    if dietary:
        constraints.append(f"Dietary preferences: {', '.join(dietary)}")
    if cal_target:
        constraints.append(f"Target ~{cal_target} calories per day")
    return "\n".join(constraints) if constraints else "No special constraints."


def parse_expiry_date(date_str: str) -> Optional[datetime]:
    """Safely parse an expiry date string to datetime."""
    try:
        exp = datetime.fromisoformat(date_str)
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return exp
    except (ValueError, TypeError):
        return None


def classify_expiry(item: dict, days_left: int) -> Optional[dict]:
    """Classify an item's expiry urgency and build notification dict."""
    name = item["name"]
    if days_left < 0:
        return {**item, "days_left": days_left, "urgency": "expired", "message": f"{name} has expired!"}
    if days_left == 0:
        return {**item, "days_left": 0, "urgency": "today", "message": f"{name} expires today!"}
    if days_left <= 2:
        return {**item, "days_left": days_left, "urgency": "critical", "message": f"{name} expires in {days_left} day{'s' if days_left > 1 else ''}!"}
    if days_left <= 5:
        return {**item, "days_left": days_left, "urgency": "warning", "message": f"{name} expires in {days_left} days"}
    return None


def find_pantry_match(ing_name: str, pantry: list) -> Optional[dict]:
    """Find a pantry item matching ingredient name (exact then partial, case-insensitive)."""
    lower = ing_name.lower()
    for item in pantry:
        if item["name"].lower() == lower:
            return item
    for item in pantry:
        if lower in item["name"].lower() or item["name"].lower() in lower:
            return item
    return None


BARCODE_CATEGORY_MAP = {
    "meat": "protein", "fish": "protein", "chicken": "protein", "beef": "protein", "pork": "protein",
    "milk": "dairy", "cheese": "dairy", "yogurt": "dairy", "butter": "dairy", "cream": "dairy",
    "vegetable": "vegetable", "salad": "vegetable", "tomato": "vegetable",
    "fruit": "fruit", "apple": "fruit", "banana": "fruit", "berry": "fruit", "orange": "fruit",
    "bread": "grain", "pasta": "grain", "rice": "grain", "cereal": "grain", "flour": "grain",
    "spice": "spice", "herb": "spice", "pepper": "spice",
    "sauce": "condiment", "ketchup": "condiment", "mustard": "condiment", "dressing": "condiment",
    "beverage": "beverage", "juice": "beverage", "soda": "beverage", "water": "beverage", "coffee": "beverage", "tea": "beverage",
    "snack": "snack", "chip": "snack", "cookie": "snack", "candy": "snack", "chocolate": "snack",
}


def classify_barcode_category(categories_tags: list) -> str:
    """Map Open Food Facts category tags to our categories."""
    cat_str = " ".join(categories_tags).lower()
    for keyword, cat_val in BARCODE_CATEGORY_MAP.items():
        if keyword in cat_str:
            return cat_val
    return "other"


async def create_llm_chat(session_prefix: str, system_message: str):
    """Create and configure an LLM chat instance."""
    from emergentintegrations.llm.chat import LlmChat
    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"{session_prefix}_{uuid.uuid4().hex[:8]}",
        system_message=system_message
    )
    chat.with_model("openai", "gpt-5.2")
    return chat


async def get_or_create_user(email, name, picture):
    """Find existing user or create a new one. Returns user_id."""
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


async def save_meal_plan_entries(uid: str, meal_plan: list):
    """Persist AI-generated meal plan entries to DB."""
    await db.meal_plans.delete_many({"user_id": uid})
    for day_plan in meal_plan:
        for meal in day_plan.get("meals", []):
            doc = {
                "entry_id": f"meal_{uuid.uuid4().hex[:12]}",
                "user_id": uid,
                "day": day_plan["day"],
                "meal_type": meal.get("meal_type", ""),
                "recipe": meal,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.meal_plans.insert_one(doc)


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
    from emergentintegrations.llm.chat import UserMessage
    ingredients_str = ", ".join(req.ingredients) if req.ingredients else "whatever is available"
    filters_str = build_recipe_filters(req, user)
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

    chat = await create_llm_chat("recipe", "You are a world-class chef and recipe creator. Generate practical, delicious recipes. Always respond with valid JSON only, no markdown formatting.")
    response = await chat.send_message(UserMessage(text=prompt))
    try:
        recipes = parse_ai_json(response)
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

# ========== COOK RECIPE (DEDUCT INGREDIENTS) ==========
@api_router.post("/recipes/cook")
async def cook_recipe(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    ingredients_used = body.get("ingredients_used", [])
    if not ingredients_used:
        return {"removed": [], "not_found": [], "message": "No ingredients to deduct"}
    uid = user["user_id"]
    pantry = await db.pantry_items.find({"user_id": uid}, {"_id": 0}).to_list(500)
    removed, not_found = [], []
    for ing_name in ingredients_used:
        match = find_pantry_match(ing_name, pantry)
        if match:
            await db.pantry_items.delete_one({"item_id": match["item_id"], "user_id": uid})
            pantry = [p for p in pantry if p["item_id"] != match["item_id"]]
            removed.append(match["name"])
        else:
            not_found.append(ing_name)
    return {"removed": removed, "not_found": not_found, "message": f"Removed {len(removed)} items from pantry"}

# ========== SCAN ROUTES ==========
@api_router.post("/scan/photo")
async def scan_photo(request: Request, file: UploadFile = File(...)):
    user = await get_current_user(request)
    from emergentintegrations.llm.chat import UserMessage, ImageContent
    data = await file.read()
    b64 = base64.b64encode(data).decode("utf-8")
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    storage_path = f"{APP_NAME}/uploads/{user['user_id']}/{uuid.uuid4()}.{ext}"
    try:
        put_object(storage_path, data, file.content_type or "image/jpeg")
    except Exception as e:
        logger.warning(f"Storage upload failed: {e}")
    chat = await create_llm_chat("scan", "You are a food identification expert. Identify food items and ingredients from images. Always respond with valid JSON only.")
    user_msg = UserMessage(
        text="""Identify all food items and ingredients visible in this image.
Respond in this exact JSON format:
{
  "items": [
    {"name": "item name", "category": "protein/dairy/vegetable/fruit/grain/spice/condiment/other", "quantity": "estimated quantity or null"}
  ],
  "confidence": "high/medium/low"
}""",
        file_contents=[ImageContent(image_base64=b64)]
    )
    response = await chat.send_message(user_msg)
    try:
        return parse_ai_json(response)
    except json.JSONDecodeError:
        return {"items": [], "confidence": "low", "raw": response[:300]}

@api_router.post("/scan/receipt")
async def scan_receipt(request: Request, file: UploadFile = File(...)):
    user = await get_current_user(request)
    from emergentintegrations.llm.chat import UserMessage, ImageContent
    data = await file.read()
    b64 = base64.b64encode(data).decode("utf-8")
    chat = await create_llm_chat("receipt", "You are a receipt reading expert. Extract food items from grocery receipts. Always respond with valid JSON only.")
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
        file_contents=[ImageContent(image_base64=b64)]
    )
    response = await chat.send_message(user_msg)
    try:
        return parse_ai_json(response)
    except json.JSONDecodeError:
        return {"items": [], "store_name": None, "total": None, "raw": response[:300]}

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

# ========== BARCODE LOOKUP ==========
@api_router.get("/barcode/{code}")
async def lookup_barcode(code: str, request: Request):
    user = await get_current_user(request)
    try:
        resp = requests.get(
            f"https://world.openfoodfacts.org/api/v0/product/{code}.json",
            timeout=10,
            headers={"User-Agent": "PantryPulse/1.0"}
        )
        data = resp.json()
        if data.get("status") == 1:
            product = data.get("product", {})
            name = product.get("product_name") or product.get("generic_name") or "Unknown Product"
            categories_tags = product.get("categories_tags", [])
            category = "other"
            cat_map = {
                "meat": "protein", "fish": "protein", "chicken": "protein", "beef": "protein", "pork": "protein",
                "milk": "dairy", "cheese": "dairy", "yogurt": "dairy", "butter": "dairy", "cream": "dairy",
                "vegetable": "vegetable", "salad": "vegetable", "tomato": "vegetable",
                "fruit": "fruit", "apple": "fruit", "banana": "fruit", "berry": "fruit", "orange": "fruit",
                "bread": "grain", "pasta": "grain", "rice": "grain", "cereal": "grain", "flour": "grain",
                "spice": "spice", "herb": "spice", "pepper": "spice",
                "sauce": "condiment", "ketchup": "condiment", "mustard": "condiment", "dressing": "condiment",
                "beverage": "beverage", "juice": "beverage", "soda": "beverage", "water": "beverage", "coffee": "beverage", "tea": "beverage",
                "snack": "snack", "chip": "snack", "cookie": "snack", "candy": "snack", "chocolate": "snack",
            }
            cat_str = " ".join(categories_tags).lower()
            for keyword, cat_val in cat_map.items():
                if keyword in cat_str:
                    category = cat_val
                    break
            return {
                "found": True,
                "name": name,
                "brand": product.get("brands", ""),
                "category": category,
                "quantity": product.get("quantity", ""),
                "image_url": product.get("image_front_small_url", ""),
                "nutriscore": product.get("nutriscore_grade", ""),
                "calories": product.get("nutriments", {}).get("energy-kcal_100g", ""),
            }
        else:
            return {"found": False, "code": code}
    except Exception as e:
        logger.error(f"Barcode lookup error: {e}")
        return {"found": False, "code": code, "error": str(e)}

# ========== NOTIFICATIONS ==========
@api_router.get("/notifications/expiring")
async def get_expiring_notifications(request: Request):
    user = await get_current_user(request)
    uid = user["user_id"]
    items = await db.pantry_items.find(
        {"user_id": uid, "expiry_date": {"$ne": None}}, {"_id": 0}
    ).to_list(500)
    now = datetime.now(timezone.utc)
    notifications = []
    for item in items:
        try:
            exp = datetime.fromisoformat(item["expiry_date"])
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            days_left = (exp - now).days
            if days_left < 0:
                notifications.append({**item, "days_left": days_left, "urgency": "expired", "message": f"{item['name']} has expired!"})
            elif days_left == 0:
                notifications.append({**item, "days_left": 0, "urgency": "today", "message": f"{item['name']} expires today!"})
            elif days_left <= 2:
                notifications.append({**item, "days_left": days_left, "urgency": "critical", "message": f"{item['name']} expires in {days_left} day{'s' if days_left > 1 else ''}!"})
            elif days_left <= 5:
                notifications.append({**item, "days_left": days_left, "urgency": "warning", "message": f"{item['name']} expires in {days_left} days"})
        except (ValueError, TypeError):
            pass
    # Remove any _id that might sneak through via spread
    for n in notifications:
        n.pop("_id", None)
    notifications.sort(key=lambda x: x["days_left"])
    return {"notifications": notifications, "count": len(notifications)}

# ========== MEAL PLANNER ==========
class MealPlanEntry(BaseModel):
    day: str
    meal_type: str
    recipe: dict

@api_router.get("/mealplan")
async def get_meal_plan(request: Request):
    user = await get_current_user(request)
    uid = user["user_id"]
    plan = await db.meal_plans.find({"user_id": uid}, {"_id": 0}).to_list(100)
    return plan

@api_router.post("/mealplan")
async def add_meal_plan_entry(entry: MealPlanEntry, request: Request):
    user = await get_current_user(request)
    doc = {
        "entry_id": f"meal_{uuid.uuid4().hex[:12]}",
        "user_id": user["user_id"],
        "day": entry.day,
        "meal_type": entry.meal_type,
        "recipe": entry.recipe,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.meal_plans.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api_router.delete("/mealplan/{entry_id}")
async def delete_meal_plan_entry(entry_id: str, request: Request):
    user = await get_current_user(request)
    result = await db.meal_plans.delete_one({"entry_id": entry_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"message": "Deleted"}

@api_router.delete("/mealplan")
async def clear_meal_plan(request: Request):
    user = await get_current_user(request)
    await db.meal_plans.delete_many({"user_id": user["user_id"]})
    return {"message": "Meal plan cleared"}

@api_router.post("/mealplan/generate")
async def generate_meal_plan(request: Request):
    user = await get_current_user(request)
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    uid = user["user_id"]
    pantry_items = await db.pantry_items.find({"user_id": uid}, {"_id": 0, "name": 1}).to_list(200)
    pantry_str = ", ".join([i["name"] for i in pantry_items]) if pantry_items else "limited pantry"
    body = await request.json()
    days = body.get("days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    allergies = user.get("allergies", [])
    dietary = user.get("dietary_preferences", [])
    skill = user.get("skill_level", "beginner")
    servings = user.get("default_servings", 2)
    cal_target = user.get("calorie_target")
    constraints = []
    if allergies:
        constraints.append(f"Allergies (AVOID completely): {', '.join(allergies)}")
    if dietary:
        constraints.append(f"Dietary preferences: {', '.join(dietary)}")
    if cal_target:
        constraints.append(f"Target ~{cal_target} calories per day")
    constraints_str = "\n".join(constraints) if constraints else "No special constraints."
    prompt = f"""Create a weekly meal plan for these days: {', '.join(days)}
Available pantry ingredients: {pantry_str}
Skill level: {skill}
Servings per meal: {servings}

Constraints:
{constraints_str}

For each day, provide breakfast, lunch, and dinner. Respond in this exact JSON format (no markdown):
{{
  "meal_plan": [
    {{
      "day": "Monday",
      "meals": [
        {{
          "meal_type": "breakfast",
          "title": "Recipe Name",
          "description": "Brief description",
          "total_time": 15,
          "calories_per_serving": 350,
          "ingredients_used": ["from pantry"],
          "ingredients_needed": ["need to buy"],
          "instructions": ["Step 1", "Step 2"]
        }}
      ]
    }}
  ],
  "shopping_list": ["items needed that aren't in pantry"],
  "estimated_weekly_calories": 14000
}}"""
    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"mealplan_{uuid.uuid4().hex[:8]}",
        system_message="You are a meal planning expert. Create balanced, practical weekly meal plans. Always respond with valid JSON only."
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
        logger.error(f"Meal plan parse error: {response[:200]}")
        result = {"meal_plan": [], "shopping_list": [], "error": "Failed to parse AI response"}
    # Save each meal entry to DB
    if result.get("meal_plan"):
        await db.meal_plans.delete_many({"user_id": uid})
        for day_plan in result["meal_plan"]:
            for meal in day_plan.get("meals", []):
                doc = {
                    "entry_id": f"meal_{uuid.uuid4().hex[:12]}",
                    "user_id": uid,
                    "day": day_plan["day"],
                    "meal_type": meal.get("meal_type", ""),
                    "recipe": meal,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.meal_plans.insert_one(doc)
    return result

# ========== GROCERY CART ==========
STORE_LINKS = {
    "instacart": {"name": "Instacart", "base_url": "https://www.instacart.com/store/search_v3/search?search_term=", "logo": "https://upload.wikimedia.org/wikipedia/commons/9/9f/Instacart_logo_and_wordmark.svg"},
    "walmart": {"name": "Walmart", "base_url": "https://www.walmart.com/search?q=", "logo": "https://upload.wikimedia.org/wikipedia/commons/c/ca/Walmart_logo.svg"},
    "shoprite": {"name": "ShopRite", "base_url": "https://www.shoprite.com/sm/pickup/rsid/3000/search?q=", "logo": ""},
    "amazon_fresh": {"name": "Amazon Fresh", "base_url": "https://www.amazon.com/s?k=", "logo": ""},
    "target": {"name": "Target", "base_url": "https://www.target.com/s?searchTerm=", "logo": ""},
}

SERVICE_FEE = 2.50

@api_router.get("/cart")
async def get_cart(request: Request):
    user = await get_current_user(request)
    items = await db.cart_items.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(100)
    subtotal = sum(item.get("estimated_price", 0) for item in items)
    return {"items": items, "subtotal": round(subtotal, 2), "service_fee": SERVICE_FEE, "total": round(subtotal + SERVICE_FEE, 2), "item_count": len(items)}

@api_router.post("/cart/add")
async def add_to_cart(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    doc = {
        "cart_item_id": f"cart_{uuid.uuid4().hex[:12]}",
        "user_id": user["user_id"],
        "name": body.get("name", ""),
        "category": body.get("category", "other"),
        "quantity": body.get("quantity", 1),
        "estimated_price": body.get("estimated_price", 0),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.cart_items.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api_router.post("/cart/add-bulk")
async def add_to_cart_bulk(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    items = body.get("items", [])
    added = []
    for item in items:
        doc = {
            "cart_item_id": f"cart_{uuid.uuid4().hex[:12]}",
            "user_id": user["user_id"],
            "name": item.get("name", ""),
            "category": item.get("category", "other"),
            "quantity": item.get("quantity", 1),
            "estimated_price": item.get("estimated_price", 0),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.cart_items.insert_one(doc)
        doc.pop("_id", None)
        added.append(doc)
    return {"added": added, "count": len(added)}

@api_router.delete("/cart/{cart_item_id}")
async def remove_from_cart(cart_item_id: str, request: Request):
    user = await get_current_user(request)
    result = await db.cart_items.delete_one({"cart_item_id": cart_item_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Removed"}

@api_router.delete("/cart")
async def clear_cart(request: Request):
    user = await get_current_user(request)
    await db.cart_items.delete_many({"user_id": user["user_id"]})
    return {"message": "Cart cleared"}

@api_router.get("/stores")
async def get_stores(request: Request):
    return {"stores": [{"id": k, "name": v["name"], "base_url": v["base_url"]} for k, v in STORE_LINKS.items()]}

# ========== STRIPE CHECKOUT ==========
STRIPE_KEY = os.environ.get("STRIPE_API_KEY")

@api_router.post("/cart/checkout")
async def create_checkout(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    origin_url = body.get("origin_url", "")
    store_id = body.get("store_id", "instacart")
    if not origin_url:
        raise HTTPException(status_code=400, detail="origin_url required")
    # Get cart items
    cart_items = await db.cart_items.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(100)
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    subtotal = sum(item.get("estimated_price", 0) for item in cart_items)
    from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe = StripeCheckout(api_key=STRIPE_KEY, webhook_url=webhook_url)
    success_url = f"{origin_url}/grocery?session_id={{CHECKOUT_SESSION_ID}}&status=success"
    cancel_url = f"{origin_url}/grocery?status=cancelled"
    checkout_req = CheckoutSessionRequest(
        amount=SERVICE_FEE,
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": user["user_id"],
            "store_id": store_id,
            "item_count": str(len(cart_items)),
            "subtotal": str(round(subtotal, 2)),
            "type": "grocery_order"
        }
    )
    session = await stripe.create_checkout_session(checkout_req)
    # Create payment transaction record
    await db.payment_transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "user_id": user["user_id"],
        "session_id": session.session_id,
        "amount": SERVICE_FEE,
        "currency": "usd",
        "payment_status": "initiated",
        "store_id": store_id,
        "cart_items": [{"name": i["name"], "category": i.get("category"), "estimated_price": i.get("estimated_price", 0)} for i in cart_items],
        "metadata": {"item_count": len(cart_items), "subtotal": round(subtotal, 2)},
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    return {"url": session.url, "session_id": session.session_id}

@api_router.get("/cart/checkout/status/{session_id}")
async def check_checkout_status(session_id: str, request: Request):
    user = await get_current_user(request)
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe = StripeCheckout(api_key=STRIPE_KEY, webhook_url=webhook_url)
    status = await stripe.get_checkout_status(session_id)
    # Update transaction
    txn = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if txn and txn.get("payment_status") != "paid":
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"payment_status": status.payment_status, "status": status.status, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        # If paid, add cart items to pantry and clear cart
        if status.payment_status == "paid":
            cart_items = txn.get("cart_items", [])
            for item in cart_items:
                await db.pantry_items.insert_one({
                    "item_id": f"item_{uuid.uuid4().hex[:12]}",
                    "user_id": user["user_id"],
                    "name": item["name"],
                    "category": item.get("category", "other"),
                    "quantity": None,
                    "unit": None,
                    "expiry_date": None,
                    "notes": "Added via grocery order",
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
            # Clear the cart
            await db.cart_items.delete_many({"user_id": user["user_id"]})
    return {
        "status": status.status,
        "payment_status": status.payment_status,
        "amount_total": status.amount_total,
        "currency": status.currency,
        "store_id": txn.get("store_id") if txn else None,
        "items_added": len(txn.get("cart_items", [])) if txn and status.payment_status == "paid" else 0
    }

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe = StripeCheckout(api_key=STRIPE_KEY, webhook_url=webhook_url)
    body = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    try:
        event = await stripe.handle_webhook(body, sig)
        if event.payment_status == "paid" and event.session_id:
            txn = await db.payment_transactions.find_one({"session_id": event.session_id})
            if txn and txn.get("payment_status") != "paid":
                await db.payment_transactions.update_one(
                    {"session_id": event.session_id},
                    {"$set": {"payment_status": "paid", "status": "complete", "event_id": event.event_id, "updated_at": datetime.now(timezone.utc).isoformat()}}
                )
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return {"received": True}

# ========== GROCERY SUGGESTIONS WITH PRICES ==========
@api_router.post("/grocery/suggestions-priced")
async def get_grocery_suggestions_priced(req: GroceryRequest, request: Request):
    user = await get_current_user(request)
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    pantry_str = ", ".join(req.pantry_ingredients) if req.pantry_ingredients else "mostly empty pantry"
    prefs = ", ".join(req.preferences) if req.preferences else "no specific preferences"
    prompt = f"""Given a pantry with: {pantry_str}
User preferences: {prefs}
Budget: {req.budget or "moderate"}
User allergies: {', '.join(user.get('allergies', [])) or 'none'}

Suggest 8-12 grocery items to buy with REALISTIC estimated prices in USD.
Respond in this exact JSON format (no markdown):
{{
  "suggestions": [
    {{
      "name": "item name",
      "category": "protein/dairy/vegetable/fruit/grain/spice/condiment/other",
      "reason": "brief reason to buy",
      "estimated_price": 3.99,
      "recipes_enabled": ["recipe 1", "recipe 2"],
      "priority": "high/medium/low"
    }}
  ],
  "meal_plan_preview": "Brief description of meals possible with these additions"
}}"""
    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"grocery_p_{uuid.uuid4().hex[:8]}",
        system_message="You are a smart grocery shopping assistant. Suggest practical items with realistic USD prices. Always respond with valid JSON only."
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
