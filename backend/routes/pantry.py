from fastapi import APIRouter, HTTPException, Request
import uuid
from datetime import datetime, timezone

from core.database import db
from core.auth import get_current_user
from models.schemas import PantryItemCreate, PantryItemUpdate

router = APIRouter(prefix="/api/pantry", tags=["pantry"])


@router.get("")
async def get_pantry(request: Request):
    user = await get_current_user(request)
    items = await db.pantry_items.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(500)
    return items


@router.post("")
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


@router.post("/bulk")
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


@router.put("/{item_id}")
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


@router.delete("/{item_id}")
async def delete_pantry_item(item_id: str, request: Request):
    user = await get_current_user(request)
    result = await db.pantry_items.delete_one({"item_id": item_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Deleted"}
