# Pantry Pulse - Product Requirements Document

## Problem Statement
People often have ingredients at home but no idea what to make. Existing tools show recipes that don't match or generate AI dishes that feel disconnected. Pantry Pulse solves this by taking ingredients you have and showing recipes based on those ingredients using AI.

## Core Features
- Pantry tracking with CRUD operations and category-based organization
- AI recipe generation via GPT-5.2 based on available ingredients
- Barcode scanning (camera + manual) with multi-API fallback (Open Food Facts v2/v0 + UPC Item DB)
- Photo scanning for ingredient identification (AI vision)
- Receipt scanning for bulk ingredient addition
- Meal planning (weekly auto-generation)
- Grocery cart with Stripe checkout for ordering fees
- "Cook This" feature that deducts used ingredients from pantry
- Push notifications for expiring pantry items
- Quick Add common ingredients to pantry with one click
- Standard email/password authentication + Google OAuth

## Tech Stack
- Frontend: React 19, Tailwind CSS, Shadcn UI, Framer Motion, Phosphor Icons
- Backend: FastAPI, Motor (async MongoDB driver)
- Database: MongoDB
- AI: GPT-5.2 via Emergent Integrations
- Auth: JWT (httpOnly cookies) + Emergent Google OAuth
- Payments: Stripe
- Barcode: Open Food Facts API + UPC Item DB

## Architecture
```
/app/
├── backend/
│   ├── server.py              # Main FastAPI application (all endpoints)
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/        # Navbar, NotificationBell, ProtectedRoute, ui/
│   │   ├── context/           # AuthContext.js
│   │   ├── pages/             # Landing, Dashboard, Pantry, RecipeGenerator, SavedRecipes, Scanner, GroceryList, Profile, MealPlanner, AuthCallback
│   │   ├── App.js, App.css, index.css
│   │   └── index.js
│   ├── package.json
│   └── tailwind.config.js
├── memory/
│   ├── PRD.md
│   └── test_credentials.md
├── README.md, LICENSE, .gitignore
```

## DB Schema
- **users**: {user_id, email, name, picture, password_hash, auth_type, role, allergies, dietary_preferences, skill_level, default_servings, calorie_target, created_at}
- **user_sessions**: {user_id, session_token, expires_at, created_at} (Google OAuth)
- **pantry_items**: {item_id, user_id, name, category, quantity, unit, expiry_date, notes, created_at}
- **saved_recipes**: {saved_id, user_id, title, ingredients, instructions, prep_time, image_url, calories, tags, saved_at}
- **meal_plans**: {entry_id, user_id, day, meal_type, recipe, created_at}
- **cart_items**: {cart_item_id, user_id, name, category, quantity, estimated_price, created_at}
- **payment_transactions**: {transaction_id, user_id, session_id, amount, currency, payment_status, store_id, cart_items, metadata, created_at}
- **login_attempts**: {identifier, attempts, last_attempt, locked_until} (brute force protection)

## What's Implemented (Complete)
- [x] Initial application scaffolding & styling
- [x] Emergent Google OAuth integration
- [x] Pantry CRUD & AI Recipe Generation via GPT-5.2
- [x] App renamed from "Fridge to Table" to "Pantry Pulse"
- [x] Quick-select common ingredient buttons in Recipe Generator
- [x] Barcode scanning via html5-qrcode & Open Food Facts API
- [x] Push notifications for expiring pantry items
- [x] Meal Planner (Weekly auto-generation & CRUD)
- [x] Grocery Cart & Stripe checkout
- [x] GitHub-ready files: README.md, LICENSE, .gitignore
- [x] "Cook This" button deducts ingredients from pantry
- [x] Code refactoring (React hooks, Python complexity)
- [x] Standard email/password JWT authentication (Apr 13, 2026)
- [x] Quick Add common items feature in Pantry (Apr 13, 2026)
- [x] Improved barcode scanner with multi-API fallback (Apr 13, 2026)

## Backlog
- [ ] P1: Receipt photo scanning improvements (robust vision parsing)
- [ ] P2: Refactor server.py into FastAPI routers
- [ ] P2: Emergent Auth portal display name fix (lower priority since standard auth exists)
