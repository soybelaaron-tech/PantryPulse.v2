from fastapi import APIRouter, Request
from datetime import datetime, timezone

from core.database import db
from core.auth import get_current_user
from core.helpers import parse_expiry_date, classify_expiry

router = APIRouter(prefix="/api", tags=["profile"])


@router.get("/profile")
async def get_profile(request: Request):
    user = await get_current_user(request)
    return user


@router.put("/profile")
async def update_profile(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    allowed = ["allergies", "dietary_preferences", "skill_level", "default_servings", "calorie_target", "name"]
    update_data = {k: v for k, v in body.items() if k in allowed}
    if update_data:
        await db.users.update_one({"user_id": user["user_id"]}, {"$set": update_data})
    updated = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
    return updated


@router.get("/stats")
async def get_stats(request: Request):
    user = await get_current_user(request)
    uid = user["user_id"]
    pantry_count = await db.pantry_items.count_documents({"user_id": uid})
    saved_count = await db.saved_recipes.count_documents({"user_id": uid})
    expiring_items = await db.pantry_items.find(
        {"user_id": uid, "expiry_date": {"$ne": None}}, {"_id": 0}
    ).to_list(500)
    now = datetime.now(timezone.utc)
    expiring_soon = []
    for item in expiring_items:
        exp = parse_expiry_date(item.get("expiry_date", ""))
        if not exp:
            continue
        days_left = (exp - now).days
        if 0 <= days_left <= 3:
            item["days_left"] = days_left
            expiring_soon.append(item)
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


@router.get("/notifications/expiring")
async def get_expiring_notifications(request: Request):
    user = await get_current_user(request)
    uid = user["user_id"]
    items = await db.pantry_items.find(
        {"user_id": uid, "expiry_date": {"$ne": None}}, {"_id": 0}
    ).to_list(500)
    now = datetime.now(timezone.utc)
    notifications = []
    for item in items:
        exp = parse_expiry_date(item.get("expiry_date", ""))
        if not exp:
            continue
        days_left = (exp - now).days
        notification = classify_expiry(item, days_left)
        if notification:
            notification.pop("_id", None)
            notifications.append(notification)
    notifications.sort(key=lambda x: x["days_left"])
    return {"notifications": notifications, "count": len(notifications)}
