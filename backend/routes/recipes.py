from fastapi import APIRouter, HTTPException, Request
import uuid
import json
import logging
from datetime import datetime, timezone

from core.database import db
from core.auth import get_current_user
from core.llm import create_llm_chat, parse_ai_json
from core.helpers import build_recipe_filters, find_pantry_match
from models.schemas import RecipeGenerateRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/recipes", tags=["recipes"])


@router.post("/generate")
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


@router.get("/saved")
async def get_saved_recipes(request: Request):
    user = await get_current_user(request)
    recipes = await db.saved_recipes.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(100)
    return recipes


@router.post("/save")
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


@router.delete("/saved/{saved_id}")
async def delete_saved_recipe(saved_id: str, request: Request):
    user = await get_current_user(request)
    result = await db.saved_recipes.delete_one({"saved_id": saved_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return {"message": "Deleted"}


@router.post("/cook")
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
