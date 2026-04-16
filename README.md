# Pantry Pulse

AI-powered cooking assistant that turns your ingredients into delicious meals. Track your pantry, scan barcodes and receipts, generate recipes with GPT-5.2, plan weekly meals, and order groceries.

## Quick Start (Docker)

The fastest way to run the full app:

```bash
git clone <your-repo-url>
cd pantry-pulse
```

**1. Set up your environment variables:**

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and fill in your keys:

```
MONGO_URL=mongodb://mongodb:27017
DB_NAME=pantry_pulse
EMERGENT_LLM_KEY=your_emergent_key_here
STRIPE_API_KEY=your_stripe_key_here
JWT_SECRET=your_random_secret_here
ADMIN_EMAIL=admin@pantrypulse.com
ADMIN_PASSWORD=YourAdminPassword123!
```

**2. Run with Docker Compose:**

```bash
docker compose up --build
```

Open **http://localhost:8001** — the app is ready.

---

## Manual Setup (without Docker)

### Prerequisites

- Node.js 18+
- Python 3.11+
- MongoDB running locally on port 27017

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # Edit with your keys
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend

```bash
cd frontend
yarn install
```

Create `frontend/.env`:
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

```bash
yarn start
```

Open **http://localhost:3000**

---

## Features

- **AI Recipe Generator** — Enter ingredients, get 8 creative recipes powered by GPT-5.2
- **Pantry Tracking** — Full CRUD with categories, expiry dates, and Quick Add for common items
- **Barcode Scanner** — Camera scanning + manual entry with 3 fallback APIs (Open Food Facts v2, v0, UPC Item DB)
- **Receipt Scanner** — Upload grocery receipt photos, AI extracts all items with abbreviation expansion
- **Photo Scanner** — Snap a photo of food, AI identifies ingredients
- **Meal Planner** — AI-generated weekly meal plans based on your pantry and preferences
- **Grocery Cart** — Smart suggestions + Stripe checkout for ordering fees
- **Cook This** — One-click to deduct recipe ingredients from your pantry
- **Expiry Notifications** — Get alerted before food goes bad
- **Dual Auth** — Email/password (JWT) + Google OAuth

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Tailwind CSS, Shadcn/UI, Framer Motion |
| Backend | FastAPI (modular routers), Motor (async MongoDB) |
| Database | MongoDB |
| AI | GPT-5.2 via Emergent Integrations |
| Auth | JWT (httpOnly cookies) + Google OAuth |
| Payments | Stripe |
| Barcode | Open Food Facts + UPC Item DB |

## Project Structure

```
├── backend/
│   ├── server.py          # App entrypoint
│   ├── core/              # Database, auth, LLM, storage, helpers
│   ├── models/            # Pydantic schemas
│   ├── routes/            # API routers (auth, pantry, recipes, scan, grocery, mealplan, profile)
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/    # Navbar, UI components
│   │   ├── context/       # Auth context
│   │   └── pages/         # All page components
│   └── public/
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGO_URL` | MongoDB connection string | Yes |
| `DB_NAME` | Database name | Yes |
| `EMERGENT_LLM_KEY` | Emergent universal key for GPT-5.2 | Yes |
| `JWT_SECRET` | Secret for JWT token signing | Yes |
| `STRIPE_API_KEY` | Stripe secret key for payments | Yes |
| `ADMIN_EMAIL` | Seeded admin account email | No |
| `ADMIN_PASSWORD` | Seeded admin account password | No |

## License

MIT
