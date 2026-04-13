from fastapi import APIRouter, HTTPException, Request
import os
import uuid
import json
import logging
from datetime import datetime, timezone

from core.database import db
from core.auth import get_current_user
from core.llm import create_llm_chat, parse_ai_json
from models.schemas import GroceryRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["grocery"])

STORE_LINKS = {
    "instacart": {"name": "Instacart", "base_url": "https://www.instacart.com/store/search_v3/search?search_term="},
    "walmart": {"name": "Walmart", "base_url": "https://www.walmart.com/search?q="},
    "shoprite": {"name": "ShopRite", "base_url": "https://www.shoprite.com/sm/pickup/rsid/3000/search?q="},
    "amazon_fresh": {"name": "Amazon Fresh", "base_url": "https://www.amazon.com/s?k="},
    "target": {"name": "Target", "base_url": "https://www.target.com/s?searchTerm="},
}
SERVICE_FEE = 2.50
STRIPE_KEY = os.environ.get("STRIPE_API_KEY")


# ========== GROCERY SUGGESTIONS ==========

@router.post("/grocery/suggestions")
async def get_grocery_suggestions(req: GroceryRequest, request: Request):
    user = await get_current_user(request)
    from emergentintegrations.llm.chat import UserMessage
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
    chat = await create_llm_chat("grocery", "You are a smart grocery shopping assistant. Suggest practical, budget-conscious grocery items. Always respond with valid JSON only.")
    response = await chat.send_message(UserMessage(text=prompt))
    try:
        return parse_ai_json(response)
    except json.JSONDecodeError:
        return {"suggestions": [], "meal_plan_preview": response[:300]}


@router.post("/grocery/suggestions-priced")
async def get_grocery_suggestions_priced(req: GroceryRequest, request: Request):
    user = await get_current_user(request)
    from emergentintegrations.llm.chat import UserMessage
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
    chat = await create_llm_chat("grocery_p", "You are a smart grocery shopping assistant. Suggest practical items with realistic USD prices. Always respond with valid JSON only.")
    response = await chat.send_message(UserMessage(text=prompt))
    try:
        return parse_ai_json(response)
    except json.JSONDecodeError:
        return {"suggestions": [], "meal_plan_preview": response[:300]}


# ========== CART ==========

@router.get("/cart")
async def get_cart(request: Request):
    user = await get_current_user(request)
    items = await db.cart_items.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(100)
    subtotal = sum(item.get("estimated_price", 0) for item in items)
    return {"items": items, "subtotal": round(subtotal, 2), "service_fee": SERVICE_FEE, "total": round(subtotal + SERVICE_FEE, 2), "item_count": len(items)}


@router.post("/cart/add")
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


@router.post("/cart/add-bulk")
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


@router.delete("/cart/{cart_item_id}")
async def remove_from_cart(cart_item_id: str, request: Request):
    user = await get_current_user(request)
    result = await db.cart_items.delete_one({"cart_item_id": cart_item_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Removed"}


@router.delete("/cart")
async def clear_cart(request: Request):
    user = await get_current_user(request)
    await db.cart_items.delete_many({"user_id": user["user_id"]})
    return {"message": "Cart cleared"}


@router.get("/stores")
async def get_stores(request: Request):
    return {"stores": [{"id": k, "name": v["name"], "base_url": v["base_url"]} for k, v in STORE_LINKS.items()]}


# ========== STRIPE CHECKOUT ==========

@router.post("/cart/checkout")
async def create_checkout(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    origin_url = body.get("origin_url", "")
    store_id = body.get("store_id", "instacart")
    if not origin_url:
        raise HTTPException(status_code=400, detail="origin_url required")
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
        amount=SERVICE_FEE, currency="usd",
        success_url=success_url, cancel_url=cancel_url,
        metadata={
            "user_id": user["user_id"], "store_id": store_id,
            "item_count": str(len(cart_items)), "subtotal": str(round(subtotal, 2)),
            "type": "grocery_order"
        }
    )
    session = await stripe.create_checkout_session(checkout_req)
    await db.payment_transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "user_id": user["user_id"], "session_id": session.session_id,
        "amount": SERVICE_FEE, "currency": "usd", "payment_status": "initiated",
        "store_id": store_id,
        "cart_items": [{"name": i["name"], "category": i.get("category"), "estimated_price": i.get("estimated_price", 0)} for i in cart_items],
        "metadata": {"item_count": len(cart_items), "subtotal": round(subtotal, 2)},
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    return {"url": session.url, "session_id": session.session_id}


@router.get("/cart/checkout/status/{session_id}")
async def check_checkout_status(session_id: str, request: Request):
    user = await get_current_user(request)
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe = StripeCheckout(api_key=STRIPE_KEY, webhook_url=webhook_url)
    status = await stripe.get_checkout_status(session_id)
    txn = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if txn and txn.get("payment_status") != "paid":
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"payment_status": status.payment_status, "status": status.status, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        if status.payment_status == "paid":
            for item in txn.get("cart_items", []):
                await db.pantry_items.insert_one({
                    "item_id": f"item_{uuid.uuid4().hex[:12]}",
                    "user_id": user["user_id"],
                    "name": item["name"], "category": item.get("category", "other"),
                    "quantity": None, "unit": None, "expiry_date": None,
                    "notes": "Added via grocery order",
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
            await db.cart_items.delete_many({"user_id": user["user_id"]})
    return {
        "status": status.status, "payment_status": status.payment_status,
        "amount_total": status.amount_total, "currency": status.currency,
        "store_id": txn.get("store_id") if txn else None,
        "items_added": len(txn.get("cart_items", [])) if txn and status.payment_status == "paid" else 0
    }


@router.post("/webhook/stripe")
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
