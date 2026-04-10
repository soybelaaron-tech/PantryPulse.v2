# Pantry Pulse - AI-Powered Recipe Generator

## Problem Statement
People have ingredients at home but no idea what to make. This app combines real recipe accuracy with AI creativity.

## Features Implemented
### Core (Phase 1 - Apr 10, 2026)
- Google OAuth (Emergent Auth)
- AI Recipe Generation (GPT-5.2) with filters
- Quick-add common ingredient buttons (7 categories, 80+ ingredients)
- Pantry Tracker with categories, expiry dates, search/filter
- Photo/Receipt scanning (AI vision)
- Smart Grocery Suggestions
- Saved Recipes, User Profile

### Phase 2 (Apr 10, 2026)
- Barcode scanning via camera (html5-qrcode + Open Food Facts)
- Expiry notification system (bell + browser push)
- Weekly meal planner (AI-generated 7-day plans)

### Phase 3 (Apr 10, 2026) - Monetization
- **Grocery Cart System** — Add AI-suggested items to cart with estimated prices
- **Stripe Checkout** — $2.50 flat service fee per order
- **Store Integration** — Deep links to Instacart, Walmart, ShopRite, Amazon Fresh, Target
- **Auto-Pantry Add** — After payment, cart items auto-added to pantry inventory
- Payment transactions tracked in `payment_transactions` collection

## Revenue Model
- $2.50 service fee per grocery order
- Value prop: AI-curated shopping list + one-click store redirect

## Architecture
- Backend: FastAPI + MongoDB + emergentintegrations + Stripe + Open Food Facts
- Frontend: React + Tailwind + Shadcn/UI + Framer Motion + html5-qrcode
- AI: OpenAI GPT-5.2 via Emergent LLM Key
- Payments: Stripe via emergentintegrations

## Backlog
- P2: Recipe sharing / social features
- P2: Cooking timers within recipe view
- P3: Taste learning / personalized recommendations
- P3: Leftover transformation mode
- P3: Export meal plan as PDF
