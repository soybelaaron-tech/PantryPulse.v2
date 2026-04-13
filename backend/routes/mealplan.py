from fastapi import APIRouter, HTTPException, Request
import uuid
import json
import logging
from datetime import datetime, timezone

from core.database import db
from core.auth import get_current_user
from core.llm import create_llm_chat, parse_ai_json
from core.helpers import build_user_constraints
from models.schemas import MealPlanEntry

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/mealplan", tags=["mealplan"])


async def save_meal_plan_entries(uid: str, meal_plan: list):
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


@router.get("")
async def get_meal_plan(request: Request):
    user = await get_current_user(request)
    plan = await db.meal_plans.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(100)
    return plan


@router.post("")
async def add_meal_plan_entry(entry: MealPlanEntry, request: Request):
    user = await get_current_user(request)
    doc = {
        "entry_id": f"meal_{uuid.uuid4().hex[:12]}",
        "user_id": user["user_id"],
        "day": entry.day, "meal_type": entry.meal_type,
        "recipe": entry.recipe,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.meal_plans.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.delete("/{entry_id}")
async def delete_meal_plan_entry(entry_id: str, request: Request):
    user = await get_current_user(request)
    result = await db.meal_plans.delete_one({"entry_id": entry_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"message": "Deleted"}


@router.delete("")
async def clear_meal_plan(request: Request):
    user = await get_current_user(request)
    await db.meal_plans.delete_many({"user_id": user["user_id"]})
    return {"message": "Meal plan cleared"}


@router.post("/generate")
async def generate_meal_plan(request: Request):
    user = await get_current_user(request)
    from emergentintegrations.llm.chat import UserMessage
    uid = user["user_id"]
    pantry_items = await db.pantry_items.find({"user_id": uid}, {"_id": 0, "name": 1}).to_list(200)
    pantry_str = ", ".join([i["name"] for i in pantry_items]) if pantry_items else "limited pantry"
    body = await request.json()
    days = body.get("days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    skill = user.get("skill_level", "beginner")
    servings = user.get("default_servings", 2)
    constraints_str = build_user_constraints(user)
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
    chat = await create_llm_chat("mealplan", "You are a meal planning expert. Create balanced, practical weekly meal plans. Always respond with valid JSON only.")
    response = await chat.send_message(UserMessage(text=prompt))
    try:
        result = parse_ai_json(response)
    except json.JSONDecodeError:
        logger.error(f"Meal plan parse error: {response[:200]}")
        result = {"meal_plan": [], "shopping_list": [], "error": "Failed to parse AI response"}
    if result.get("meal_plan"):
        await save_meal_plan_entries(uid, result["meal_plan"])
    return result
