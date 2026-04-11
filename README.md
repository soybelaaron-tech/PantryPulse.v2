# Pantry Pulse

**AI-Powered Cooking Assistant** — Turn your ingredients into delicious meals with AI recipe generation, pantry tracking, barcode scanning, meal planning, and smart grocery ordering.

## Features

- **AI Recipe Generator** — Enter ingredients and get personalized recipes powered by OpenAI GPT-5.2. Filter by cook time, budget, skill level, dietary restrictions, servings, calories, cuisine, and meal type.
- **Quick-Add Ingredients** — 80+ common ingredients organized in 7 categories (Proteins, Vegetables, Fruits, Dairy, Grains, Pantry Staples, Spices) for one-tap adding.
- **Pantry Tracker** — Track all your ingredients with categories, quantities, expiry dates, and notes. Search and filter by category.
- **Barcode Scanner** — Scan product barcodes via camera (html5-qrcode) with automatic product lookup via Open Food Facts API. Manual entry fallback.
- **Photo & Receipt Scanning** — Upload photos of food items or grocery receipts. AI vision identifies and categorizes items for instant pantry adding.
- **Weekly Meal Planner** — AI generates 7-day meal plans (breakfast, lunch, dinner) based on your pantry, preferences, and dietary needs. Includes auto-generated shopping lists.
- **Smart Grocery Cart** — AI suggests items with estimated prices. Add to cart, choose a store (Instacart, Walmart, ShopRite, Amazon Fresh, Target), and checkout.
- **Stripe Checkout** — $2.50 service fee per order. After payment, items auto-add to pantry and user is deep-linked to their chosen store.
- **Expiry Notifications** — Notification bell with color-coded alerts for expiring items. Browser push notification support.
- **User Profiles** — Google OAuth login. Set allergies, dietary preferences, skill level, serving size, and calorie targets. AI respects all preferences.
- **Saved Recipes** — Bookmark and manage your favorite generated recipes.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React, Tailwind CSS, Shadcn/UI, Framer Motion, Phosphor Icons, html5-qrcode |
| **Backend** | Python FastAPI, Motor (async MongoDB) |
| **Database** | MongoDB |
| **AI** | OpenAI GPT-5.2 (text + vision) via Emergent Integrations |
| **Payments** | Stripe via Emergent Integrations |
| **Auth** | Google OAuth via Emergent Auth |
| **Storage** | Emergent Object Storage (photo uploads) |
| **Barcode API** | Open Food Facts |

## Project Structure

```
/app
├── backend/
│   ├── server.py          # FastAPI application (all API routes)
│   ├── .env               # Environment variables
│   └── requirements.txt   # Python dependencies
├── frontend/
│   ├── public/            # Static assets
│   ├── src/
│   │   ├── App.js         # Main app with routing
│   │   ├── context/
│   │   │   └── AuthContext.js
│   │   ├── components/
│   │   │   ├── Navbar.js
│   │   │   ├── NotificationBell.js
│   │   │   ├── ProtectedRoute.js
│   │   │   └── ui/        # Shadcn/UI components
│   │   └── pages/
│   │       ├── Landing.js
│   │       ├── AuthCallback.js
│   │       ├── Dashboard.js
│   │       ├── Pantry.js
│   │       ├── RecipeGenerator.js
│   │       ├── SavedRecipes.js
│   │       ├── Scanner.js
│   │       ├── MealPlanner.js
│   │       ├── GroceryList.js
│   │       └── Profile.js
│   ├── .env               # Frontend environment variables
│   ├── package.json
│   └── tailwind.config.js
└── README.md
```

## Environment Variables

### Backend (`/backend/.env`)
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=pantry_pulse
EMERGENT_LLM_KEY=your_emergent_llm_key
STRIPE_API_KEY=your_stripe_key
```

### Frontend (`/frontend/.env`)
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Setup
```bash
cd frontend
yarn install
yarn start
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/session` | Exchange OAuth session |
| GET | `/api/auth/me` | Get current user |
| POST | `/api/auth/logout` | Logout |
| GET/POST | `/api/pantry` | List/add pantry items |
| POST | `/api/pantry/bulk` | Bulk add items |
| PUT/DELETE | `/api/pantry/{id}` | Update/delete item |
| POST | `/api/recipes/generate` | AI recipe generation |
| GET/POST | `/api/recipes/saved` | List/save recipes |
| DELETE | `/api/recipes/saved/{id}` | Delete saved recipe |
| POST | `/api/scan/photo` | AI photo scanning |
| POST | `/api/scan/receipt` | AI receipt scanning |
| GET | `/api/barcode/{code}` | Barcode product lookup |
| GET/POST/DELETE | `/api/mealplan` | Meal plan CRUD |
| POST | `/api/mealplan/generate` | AI meal plan generation |
| POST | `/api/grocery/suggestions-priced` | AI grocery suggestions |
| GET/POST/DELETE | `/api/cart` | Shopping cart CRUD |
| POST | `/api/cart/checkout` | Stripe checkout |
| GET | `/api/cart/checkout/status/{id}` | Payment status |
| GET/PUT | `/api/profile` | User profile |
| GET | `/api/notifications/expiring` | Expiry notifications |
| GET | `/api/stats` | Dashboard stats |

## License

MIT License - see [LICENSE](LICENSE) for details.
