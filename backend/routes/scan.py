from fastapi import APIRouter, Request, UploadFile, File
import uuid
import base64
import json
import logging
import requests

from core.database import db
from core.auth import get_current_user
from core.llm import create_llm_chat, parse_ai_json
from core.storage import put_object, APP_NAME
from core.helpers import classify_barcode_category, BARCODE_CATEGORY_MAP

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["scan"])


# ========== PHOTO SCAN ==========

@router.post("/scan/photo")
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


# ========== RECEIPT SCAN (ENHANCED) ==========

RECEIPT_SYSTEM_PROMPT = """You are an expert receipt OCR and grocery item extraction system.
Your task is to extract EVERY food and grocery item from receipt images, even when:
- Text is blurry, faded, or partially cut off
- Items use store-specific abbreviations (e.g. "BNLS CHKN BRST" = Boneless Chicken Breast, "ORG WHL MLK" = Organic Whole Milk)
- Items have SKU/PLU codes next to them
- Prices are on a separate column
- Items span multiple lines
- The receipt is wrinkled, skewed, or photographed at an angle

Rules:
1. Expand ALL abbreviations into full, readable item names
2. Classify each item into a food category
3. Extract the price if visible (as a number, no $ sign)
4. Estimate quantity from the receipt (look for "x2", "QTY 3", weight entries like "1.5 LB")
5. Skip non-food items (bags, tax, coupons, loyalty cards, subtotals, change)
6. For weight-priced items (meat, produce), extract the weight as quantity
7. If you can partially read an item, make your best guess at the full name
Always respond with valid JSON only, no markdown."""

RECEIPT_USER_PROMPT = """Carefully read this grocery receipt image and extract ALL food/grocery items.

For each item, provide:
- "name": Full readable name (expand abbreviations like BNLS=Boneless, CHKN=Chicken, ORG=Organic, WHL=Whole, GRN=Green, YLW=Yellow, BLK=Black, WHT=White, SM=Small, LG=Large, FRZ=Frozen, FF=Fat Free, LF=Low Fat, RF=Reduced Fat)
- "category": One of protein/dairy/vegetable/fruit/grain/spice/condiment/beverage/snack/frozen/bakery/other
- "price": Numeric price if visible (e.g. 3.99), or null
- "quantity": Quantity with unit if visible (e.g. "2 lbs", "1"), or null

Respond in this exact JSON format:
{
  "items": [
    {"name": "Boneless Chicken Breast", "category": "protein", "price": 8.99, "quantity": "2.5 lbs"},
    {"name": "Organic Whole Milk", "category": "dairy", "price": 4.49, "quantity": "1 gal"}
  ],
  "store_name": "store name if visible, or null",
  "total": "receipt total amount as number if visible, or null"
}

Be thorough - extract every single food item you can identify, even partially visible ones."""


@router.post("/scan/receipt")
async def scan_receipt(request: Request, file: UploadFile = File(...)):
    user = await get_current_user(request)
    from emergentintegrations.llm.chat import UserMessage, ImageContent
    data = await file.read()
    b64 = base64.b64encode(data).decode("utf-8")

    # Store the receipt image
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    storage_path = f"{APP_NAME}/receipts/{user['user_id']}/{uuid.uuid4()}.{ext}"
    try:
        put_object(storage_path, data, file.content_type or "image/jpeg")
    except Exception as e:
        logger.warning(f"Receipt storage failed: {e}")

    # First pass with enhanced prompt
    chat = await create_llm_chat("receipt", RECEIPT_SYSTEM_PROMPT)
    user_msg = UserMessage(
        text=RECEIPT_USER_PROMPT,
        file_contents=[ImageContent(image_base64=b64)]
    )
    response = await chat.send_message(user_msg)
    try:
        result = parse_ai_json(response)
    except json.JSONDecodeError:
        result = None

    # If first pass returned no items, retry with a simpler fallback prompt
    if not result or not result.get("items"):
        logger.info("Receipt first pass empty, retrying with fallback prompt")
        chat2 = await create_llm_chat("receipt_retry", "You extract food items from images of receipts. Always respond with valid JSON only.")
        fallback_msg = UserMessage(
            text="""This is a grocery receipt. List every food item you can see.
Return JSON: {"items": [{"name": "item", "category": "other", "price": null, "quantity": null}], "store_name": null, "total": null}""",
            file_contents=[ImageContent(image_base64=b64)]
        )
        response2 = await chat2.send_message(fallback_msg)
        try:
            result = parse_ai_json(response2)
        except json.JSONDecodeError:
            return {"items": [], "store_name": None, "total": None, "raw": response2[:300]}

    # Post-process: normalize item names and categories
    items = result.get("items", [])
    for item in items:
        # Ensure name is title-cased and clean
        name = item.get("name", "").strip()
        if name.isupper():
            name = name.title()
        item["name"] = name

        # Normalize price to float or null
        price = item.get("price")
        if price is not None:
            try:
                item["price"] = round(float(str(price).replace("$", "").replace(",", "")), 2)
            except (ValueError, TypeError):
                item["price"] = None

    return result


# ========== BARCODE LOOKUP ==========

@router.get("/barcode/{code}")
async def lookup_barcode(code: str, request: Request):
    await get_current_user(request)

    # Try Open Food Facts v2 API first
    try:
        resp = requests.get(
            f"https://world.openfoodfacts.net/api/v2/product/{code}",
            params={"fields": "product_name,generic_name,brands,categories_tags,quantity,image_front_small_url,nutriscore_grade,nutriments"},
            timeout=10,
            headers={"User-Agent": "PantryPulse/1.0 (pantrypulse@app.com)"}
        )
        data = resp.json()
        if data.get("status") == "success" or data.get("status") == 1:
            product = data.get("product", {})
            name = product.get("product_name") or product.get("generic_name") or ""
            if name:
                category = classify_barcode_category(product.get("categories_tags", []))
                return {
                    "found": True, "name": name,
                    "brand": product.get("brands", ""),
                    "category": category,
                    "quantity": product.get("quantity", ""),
                    "image_url": product.get("image_front_small_url", ""),
                    "nutriscore": product.get("nutriscore_grade", ""),
                    "calories": product.get("nutriments", {}).get("energy-kcal_100g", ""),
                }
    except Exception as e:
        logger.warning(f"Open Food Facts v2 error: {e}")

    # Fallback: try v0 API
    try:
        resp = requests.get(
            f"https://world.openfoodfacts.org/api/v0/product/{code}.json",
            timeout=10,
            headers={"User-Agent": "PantryPulse/1.0 (pantrypulse@app.com)"}
        )
        data = resp.json()
        if data.get("status") == 1:
            product = data.get("product", {})
            name = product.get("product_name") or product.get("generic_name") or "Unknown Product"
            category = classify_barcode_category(product.get("categories_tags", []))
            return {
                "found": True, "name": name,
                "brand": product.get("brands", ""),
                "category": category,
                "quantity": product.get("quantity", ""),
                "image_url": product.get("image_front_small_url", ""),
                "nutriscore": product.get("nutriscore_grade", ""),
                "calories": product.get("nutriments", {}).get("energy-kcal_100g", ""),
            }
    except Exception as e:
        logger.warning(f"Open Food Facts v0 error: {e}")

    # Fallback: try UPC item database
    try:
        resp = requests.get(
            f"https://api.upcitemdb.com/prod/trial/lookup?upc={code}",
            timeout=10,
            headers={"User-Agent": "PantryPulse/1.0"}
        )
        data = resp.json()
        upc_items = data.get("items", [])
        if upc_items:
            item = upc_items[0]
            name = item.get("title", "Unknown Product")
            category = item.get("category", "other").lower()
            for keyword, cat_val in BARCODE_CATEGORY_MAP.items():
                if keyword in category or keyword in name.lower():
                    category = cat_val
                    break
            else:
                category = "other"
            return {
                "found": True, "name": name,
                "brand": item.get("brand", ""),
                "category": category,
                "quantity": "",
                "image_url": (item.get("images", []) or [""])[0],
                "nutriscore": "",
                "calories": "",
            }
    except Exception as e:
        logger.warning(f"UPC item DB error: {e}")

    return {"found": False, "code": code}
