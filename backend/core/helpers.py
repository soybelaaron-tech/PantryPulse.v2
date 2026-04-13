from datetime import datetime, timezone
from typing import Optional
import logging
import requests

logger = logging.getLogger(__name__)

# ========== RECIPE & MEAL PLAN HELPERS ==========

def build_recipe_filters(req, user: dict) -> str:
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


# ========== EXPIRY / PANTRY HELPERS ==========

def parse_expiry_date(date_str: str) -> Optional[datetime]:
    try:
        exp = datetime.fromisoformat(date_str)
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return exp
    except (ValueError, TypeError):
        return None


def classify_expiry(item: dict, days_left: int) -> Optional[dict]:
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
    lower = ing_name.lower()
    for item in pantry:
        if item["name"].lower() == lower:
            return item
    for item in pantry:
        if lower in item["name"].lower() or item["name"].lower() in lower:
            return item
    return None


# ========== BARCODE CATEGORY MAP ==========

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
    cat_str = " ".join(categories_tags).lower()
    for keyword, cat_val in BARCODE_CATEGORY_MAP.items():
        if keyword in cat_str:
            return cat_val
    return "other"
