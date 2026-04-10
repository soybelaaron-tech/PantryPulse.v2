# Pantry Pulse - AI-Powered Recipe Generator

## Problem Statement
People have ingredients at home but no idea what to make. Existing tools show recipes that don't match or generate generic AI dishes. This leads to wasted food, repetitive meals, and frustration.

## Target Audience
- College students (budget-conscious, limited skills)
- Young professionals (want variety, learning to cook)
- Home cooks (reduce waste, try new things)

## Core Features Implemented (Apr 10, 2026)
- Google OAuth (Emergent Auth) for user accounts
- AI Recipe Generation (OpenAI GPT-5.2) with filters: time, budget, skill, dietary, servings, calories, cuisine, meal type
- Quick-add common ingredient buttons (categorized: Proteins, Vegetables, Fruits, Dairy, Grains, Pantry Staples, Spices)
- Pantry Tracker with categories, expiry dates, search/filter
- Photo scanning (AI vision identifies food items)
- Receipt scanning (AI reads grocery receipts)
- Smart Grocery Suggestions (AI-powered)
- Saved Recipes management
- User Profile with allergies, dietary preferences, skill level, calorie targets
- Dashboard with bento grid, expiring soon alerts, quick actions
- Responsive design with Organic & Earthy theme

## Architecture
- Backend: FastAPI + MongoDB (motor) + emergentintegrations
- Frontend: React + Tailwind + Shadcn/UI + Framer Motion + Phosphor Icons
- AI: OpenAI GPT-5.2 via Emergent LLM Key
- Storage: Emergent Object Storage for photo uploads
- Auth: Emergent-managed Google OAuth

## What's Been Implemented
- Full backend with 15+ API endpoints
- 9 frontend pages (Landing, Dashboard, Pantry, Recipes, Saved, Scanner, Grocery, Profile, AuthCallback)
- Navbar with responsive mobile menu
- All AI features connected (recipe gen, photo scan, receipt scan, grocery suggestions)

## Backlog
- P1: Meal planning / weekly planner
- P1: Expiration date notifications/reminders
- P2: Recipe sharing / social features
- P2: Barcode scanning (camera-based)
- P2: Cooking timers within recipe view
- P3: Taste learning / personalized recommendations over time
- P3: Leftover transformation mode
