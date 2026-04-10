# Pantry Pulse - AI-Powered Recipe Generator

## Problem Statement
People have ingredients at home but no idea what to make. This app combines real recipe accuracy with AI creativity.

## Features Implemented (Apr 10, 2026)
### Core (Phase 1)
- Google OAuth (Emergent Auth)
- AI Recipe Generation (GPT-5.2) with filters: time, budget, skill, dietary, servings, calories, cuisine, meal type
- Quick-add common ingredient buttons (7 categories, 80+ ingredients)
- Pantry Tracker with categories, expiry dates, search/filter
- Photo scanning (AI vision)
- Receipt scanning (AI vision)
- Smart Grocery Suggestions (AI)
- Saved Recipes management
- User Profile with allergies, dietary preferences, skill level, calorie targets
- Dashboard with bento grid

### Phase 2 (Apr 10, 2026)
- **Barcode scanning via camera** - html5-qrcode library + Open Food Facts API lookup + manual entry
- **Expiry notification system** - Notification bell in navbar, in-app dropdown, browser push notifications, auto-polling every 5 min
- **Weekly meal planner** - AI-generated 7-day plans (breakfast/lunch/dinner), weekly calendar view, shopping list for plan, save meals to favorites, mobile day-by-day navigation

## Architecture
- Backend: FastAPI + MongoDB + emergentintegrations + Open Food Facts API
- Frontend: React + Tailwind + Shadcn/UI + Framer Motion + Phosphor Icons + html5-qrcode
- AI: OpenAI GPT-5.2 via Emergent LLM Key
- Storage: Emergent Object Storage
- Auth: Emergent Google OAuth

## Backlog
- P2: Recipe sharing / social features
- P2: Cooking timers within recipe view
- P3: Taste learning / personalized recommendations over time
- P3: Leftover transformation mode
- P3: Export meal plan as PDF / share
