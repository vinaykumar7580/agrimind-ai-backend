# 🌱 AgriMind AI — Smart Crop Intelligence Platform


## 🌾 Overview

**AgriMind AI** is a full-stack agricultural intelligence platform that empowers Indian farmers with AI-powered tools. Upload a photo of your crop or soil and instantly get:

- 🔬 **Crop disease diagnosis** with treatment plans
- 🪨 **Soil NPK & pH analysis** with fertilizer recommendations
- 🌤️ **Weather-based farm advisory**
- 📈 **Live mandi prices** from Agmarknet (via data.gov.in)
- 🤖 **Conversational AI assistant** with agricultural expertise
- 🌍 **Farmer community** to share knowledge and experiences

The platform uses a **3-step agentic AI pipeline**: vision model analysis → RAG knowledge retrieval → structured LLM synthesis — powered by **Google Gemini**.

---

## ✨ Features

### 🔬 Crop Analysis
- Upload crop photos for instant AI diagnosis
- Identifies 50+ diseases with confidence scores
- Detects pest infestations and nutrient deficiencies
- Provides step-by-step treatment plans with exact product names and dosages
- Health scoring (0–100) and yield impact estimation
- The diagnosis is based only on what the vision model sees, never guessed from your location
- Scan history with search, status counts and CSV export

### 🪨 Soil Analysis
- Visual soil analysis from photos
- NPK (Nitrogen, Phosphorus, Potassium) estimation
- pH level assessment with correction advice
- Organic matter and moisture content analysis
- Crop suitability recommendations

### 🌤️ Weather Intelligence
- Real-time weather from OpenWeatherMap API
- 5-day forecast in 3-hour steps, with rain probability
- AI-generated farm advisory based on weather conditions
- Growing Degree Days (GDD) for today
- Irrigation and spraying schedule recommendations
- Without an API key, sample weather is returned and marked `is_mock: true` (no advisory is generated for it)

### 📈 Market Prices
- Live daily prices for 10 tracked crops from Agmarknet mandis (via data.gov.in)
- Only real prices are shown: a crop with no price today is left out
- Change % compares the same mandi day to day
- MSP (Minimum Support Price) comparison
- AI-powered 30-day price forecast, cached for 6 hours
- Top gainer/loser tracking
- Category filtering (Cereals, Oilseeds, Vegetables, Pulses, etc.)

### 🤖 AI Chat Assistant
- Context-aware responses using your latest scan data
- RAG-powered answers from agricultural knowledge base
- Personalized advice based on your farm profile and location
- Full conversation history stored per user (newest messages kept when paging)
- If Gemini is unavailable, nothing is saved, so history never holds a question without an answer

### 👥 Community
- Share farming stories, tips, and questions, with an optional image
- Like and bookmark posts, and view your saved posts
- Trending topics and top contributor leaderboard
- Categories: Disease Control, Yield Tip, Question, Market Tip, Success Story, Farming Tip

### 🔐 Authentication
- Phone number + password authentication (no OTP)
- JWT-based session management
- 3-step signup with farm profile setup
- Forgot password with 2-step reset flow

---

## 🛠️ Tech Stack

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| Next.js | 15 | React framework with App Router |
| Tailwind CSS | v4 | Utility-first styling |
| Sonner | latest | Toast notifications |
| Lucide React | 0.383 | Icon library |
| Framer Motion | latest | Animations |

### Backend
| Technology | Version | Purpose |
|---|---|---|
| Python | 3.11+ (3.12 on Render) | Backend language |
| FastAPI | 0.115+ | Async REST API framework |
| SQLAlchemy | 2.0 | ORM for MySQL |
| PyMySQL | 1.1 | MySQL driver |
| faiss-cpu | 1.12+ | Vector database for RAG |
| Passlib + bcrypt | 1.7 | Password hashing |
| python-jose | 3.4+ | JWT token management |
| httpx / requests | 0.28+ / 2.32+ | HTTP clients (weather, mandi prices) |
| Pillow | 11+ | Image processing |
| google-genai | 1.0+ | Gemini API client |
| tenacity | 9+ | Retries when Gemini is overloaded |

### AI / ML
| Technology | Purpose |
|---|---|
| Google Gemini | Hosted LLM for text generation, diagnosis and chat |
| Gemini Vision | Crop/soil image analysis |
| all-MiniLM-L6-v2 | Local text embeddings for RAG (fastembed / ONNX, no PyTorch) |
| FAISS | Vector similarity search |

### External Data
| Source | Purpose |
|---|---|
| OpenWeatherMap | Current weather and 5-day forecast |
| data.gov.in (Agmarknet) | Daily mandi prices |

### Database
| Technology | Purpose |
|---|---|
| MySQL 8.0 (local) / TiDB Cloud (deployed) | Primary relational database |
| FAISS | Vector store for RAG knowledge base |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    NEXT.JS FRONTEND (Port 3000)              │
│  Dashboard · History · Market · Community · Auth Pages       │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API (JWT Auth)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND (Port 8000)                │
│                                                              │
│  ┌─────────┐  ┌──────┐  ┌────────┐  ┌────────┐  ┌───────┐  │
│  │  Auth   │  │ Scan │  │  Chat  │  │ Market │  │Weather│  │
│  │ Router  │  │Router│  │ Router │  │ Router │  │Router │  │
│  └────┬────┘  └──┬───┘  └───┬────┘  └───┬────┘  └───┬───┘  │
│       │          │          │            │            │      │
│  ┌────▼──────────▼──────────▼────────────▼────────────▼───┐ │
│  │                   AGENT ORCHESTRATOR                    │ │
│  │                                                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐  │ │
│  │  │  Crop Agent │  │  Soil Agent │  │ Market Agent  │  │ │
│  │  │  (Gemini    │  │  (Gemini    │  │  (Gemini)     │  │ │
│  │  │  + RAG)     │  │  + RAG)     │  └───────────────┘  │ │
│  │  └──────┬──────┘  └──────┬──────┘                      │ │
│  │         │                │                              │ │
│  │  ┌──────▼────────────────▼──────────────────────────┐  │ │
│  │  │                 RAG PIPELINE                      │  │ │
│  │  │  Query → FAISS Search → Context Injection      │  │ │
│  │  └───────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────┬───────────────────────────────────────┘
                       │
        ┌──────────────┴──┬─────────────────┬──────────────────┐
        ▼                 ▼                 ▼                  ▼
┌────────────────┐ ┌──────────────┐ ┌────────────────┐ ┌────────────────┐
│ MySQL / TiDB   │ │ Gemini API   │ │ OpenWeatherMap │ │ data.gov.in    │
│                │ │              │ │                │ │ (Agmarknet)    │
│ • users        │ │ • Text, chat │ │ • Current      │ │ • Daily mandi  │
│ • scans        │ │ • Vision     │ │ • 5-day        │ │   prices       │
│ • chat_messages│ └──────────────┘ │   forecast     │ └────────────────┘
│ • community_   │                  └────────────────┘
│   posts        │
│ • post_likes   │
│ • post_        │
│   bookmarks    │
│ • market_prices│
│ • weather_logs │
└────────────────┘
       +
┌─────────────────┐
│      FAISS      │
│  (Vector Store) │
│                 │
│ • Disease docs  │
│ • Soil docs     │
│ • Market docs   │
│ • Farm calendar │
└─────────────────┘
```

### Agentic AI Pipeline (3-Step)

```
Image Upload
     │
     ▼
┌─────────────────────────────┐
│  STEP 1: Vision Analysis    │
│  Model: Gemini              │
│  → Identifies crop/disease  │
│  → Describes visual symptoms│
└──────────────┬──────────────┘
               │  Vision text output
               ▼
┌─────────────────────────────┐
│  STEP 2: RAG Retrieval      │
│  Store: FAISS               │
│  → Similarity search on     │
│    vision output            │
│  → Returns top 3-4 relevant │
│    knowledge documents      │
└──────────────┬──────────────┘
               │  Context documents
               ▼
┌─────────────────────────────┐
│  STEP 3: LLM Synthesis      │
│  Model: Gemini              │
│  → Combines vision + RAG    │
│  → Outputs structured JSON  │
│  → Disease, treatment,      │
│    health score, findings   │
└─────────────────────────────┘
```

---

## 📁 Project Structure

```
agrimind/
│
├── 📱 FRONTEND (agrimind-frontend/)
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx                 # Dashboard (main)
│   │   │   ├── layout.tsx               # Root layout + Toaster
│   │   │   ├── globals.css              # Design system & animations
│   │   │   ├── login/
│   │   │   │   └── page.tsx             # Login page
│   │   │   ├── signup/
│   │   │   │   └── page.tsx             # 3-step signup
│   │   │   ├── forgot-password/
│   │   │   │   └── page.tsx             # Password reset
│   │   │   ├── history/
│   │   │   │   └── page.tsx             # Scan history
│   │   │   ├── market/
│   │   │   │   └── page.tsx             # Market prices
│   │   │   └── community/
│   │   │       └── page.tsx             # Community feed + Share modal
│   │   │
│   │   └── components/
│   │       ├── Navbar.tsx               # Navigation with active links
│   │       ├── UploadPanel.tsx          # Drag-drop image upload + scan ring
│   │       ├── CropAnalysisPanel.tsx    # Crop diagnosis results
│   │       ├── SoilPanel.tsx            # Soil nutrient analysis
│   │       ├── WeatherPanel.tsx         # Weather + 5-day forecast
│   │       ├── MarketPanel.tsx          # Live mandi prices
│   │       └── ChatPanel.tsx            # AI chat interface
│   │
│   ├── package.json
│   ├── tailwind.config.ts
│   └── next.config.ts
│
└── 🐍 BACKEND (agrimind-backend/)
    ├── main.py                          # FastAPI app + lifespan
    ├── config.py                        # Pydantic settings
    ├── database.py                      # SQLAlchemy engine + session
    ├── models.py                        # ORM models (8 tables)
    ├── auth.py                          # JWT + bcrypt auth
    │
    ├── agents/
    │   ├── crop_agent.py                # Vision → RAG → Crop diagnosis
    │   ├── soil_agent.py                # Vision → RAG → Soil analysis
    │   ├── weather_agent.py             # OpenWeather + AI advisory
    │   ├── market_agent.py              # data.gov.in mandi prices + AI forecast
    │   └── orchestrator.py             # Chat agent with full context
    │
    ├── rag/
    │   ├── knowledge_base.py            # 15 agricultural documents
    │   └── vector_store.py              # FAISS init + search (fastembed)
    │
    ├── faiss_store/                     # Saved FAISS index + documents
    │
    ├── scripts/
    │   └── update_prices.py             # Saves mandi prices to the DB (run from India)
    │
    ├── routers/
    │   ├── auth_router.py               # /auth/* endpoints
    │   ├── scan_router.py               # /scan/* endpoints
    │   ├── chat_router.py               # /chat/* endpoints
    │   ├── market_router.py             # /market/* endpoints
    │   ├── weather_router.py            # /weather/* endpoints
    │   └── community_router.py          # /community/* endpoints
    │
    ├── services/
    │   ├── gemini_service.py            # LLM + vision + embedding calls
    │   └── image_service.py            # Image save/resize/serve
    │
    ├── requirements.txt
    ├── render.yaml                      # Render deployment blueprint
    ├── .env                             # Local settings (git-ignored)
    └── .env.prices                      # Cloud DB settings for update_prices.py (git-ignored)
```

---

## 🚀 Getting Started

### Prerequisites

Make sure you have the following installed:

| Tool | Version | Download |
|---|---|---|
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| Python | 3.11+ | [python.org](https://python.org) |
| MySQL | 8.0+ | [mysql.com](https://mysql.com) |
| Git | any | [git-scm.com](https://git-scm.com) |

---

### Frontend Setup

```bash
# 1. Create Next.js project
npx create-next-app@latest agrimind-ai-frontend \
  --typescript --tailwind --eslint --app \
  --src-dir --import-alias "@/*"

cd agrimind-ai-frontend

# 2. Install dependencies
npm install lucide-react sonner framer-motion

# 3. Copy all component files from this repo into src/

# 4. Run development server
npm run dev
```

Frontend runs at: **http://localhost:3000**

---

### Backend Setup

```bash
# 1. Create virtual environment
cd agrimind-ai-backend
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows PowerShell)
venv\Scripts\Activate.ps1

# Activate (Windows Git Bash)
source venv/Scripts/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env with your MySQL credentials and API keys
#    (see Environment Variables below)

# 4. Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: **http://localhost:8000**
API Docs at: **http://localhost:8000/docs**

The first start downloads the embedding model (about 90 MB) into `.fastembed_cache/`. Later starts are fast.

---

### Gemini Setup

1. Create an API key at [Google AI Studio](https://aistudio.google.com/apikey).
2. Set it as `GEMINI_API_KEY` in your `.env` file (see [Environment Variables](#-environment-variables)).

### Mandi Price Setup (data.gov.in)

1. Sign in at [data.gov.in](https://data.gov.in). Accounts are created through JanParichay, the Government of India's single sign-on.
2. Generate an API key from your account page.
3. Set it as `DATA_GOV_API_KEY` in your `.env` file.

Locally, the backend fetches prices at startup and every 6 hours. data.gov.in only accepts requests from India, so a deployed backend works differently: see [Mandi prices on the deployed backend](#mandi-prices-on-the-deployed-backend).

---

### Database Setup

```bash
# 1. Login to MySQL
mysql -u root -p

# 2. Create database
CREATE DATABASE agrimind CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 3. Create user (optional but recommended)
CREATE USER 'agrimind_user'@'localhost' IDENTIFIED BY 'strong_password_here';
GRANT ALL PRIVILEGES ON agrimind.* TO 'agrimind_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# 4. Tables are auto-created when you start the FastAPI server
# SQLAlchemy runs Base.metadata.create_all() on startup
```

### Database Schema

```sql
-- 8 tables auto-created by SQLAlchemy

users              -- Farmer accounts with profile data
scans              -- Crop & soil scan results with AI analysis
chat_messages      -- Conversation history per user
community_posts    -- Farmer stories, tips, questions
post_likes         -- Which user liked which post
post_bookmarks     -- Which user saved which post
market_prices      -- Daily mandi price per crop and mandi (price history)
weather_logs       -- Weather data and farm advisories
```

---

## 🔧 Environment Variables

Create a `.env` file in the backend root:

```env
# ── Application ──────────────────────────────
APP_SECRET_KEY=your-super-secret-key-minimum-32-chars
APP_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080        # 7 days

# ── MySQL Database ────────────────────────────
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=agrimind_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=agrimind
MYSQL_SSL=false                          # true for cloud MySQL (TiDB Cloud, Aiven)

# ── CORS ──────────────────────────────────────
# Frontend URLs allowed to call the API, comma-separated
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# ── Gemini ────────────────────────────────────
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.6-flash            # Text model
GEMINI_VISION_MODEL=gemini-3.6-flash     # Vision model

# ── OpenWeatherMap (free tier) ────────────────
# Get free API key at: https://openweathermap.org/api
OPENWEATHER_API_KEY=your_openweather_api_key

# ── data.gov.in (live mandi prices) ───────────
DATA_GOV_API_KEY=your_data_gov_api_key
# true on servers outside India: serve prices saved by scripts/update_prices.py
MARKET_PRICES_FROM_DB=false
```

---

## 📡 API Reference

### Authentication

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/auth/signup` | Register new farmer account | ❌ |
| POST | `/auth/login` | Login with phone + password | ❌ |
| POST | `/auth/reset-password` | Reset password by phone number | ❌ |
| GET | `/auth/me` | Get current user profile | ✅ |
| PUT | `/auth/me` | Update user profile | ✅ |

### Scan Analysis

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/scan/analyze` | Upload image for AI analysis | ✅ |
| GET | `/scan/history` | Scans for current user, newest first | ✅ |
| GET | `/scan/stats` | Counts: total, healthy, treated, pending | ✅ |
| GET | `/scan/export` | Download all scans as CSV | ✅ |
| GET | `/scan/{scan_id}` | Get single scan details | ✅ |
| PUT | `/scan/{scan_id}/status` | Update scan status (`healthy`, `treated`, `pending`) | ✅ |

**POST `/scan/analyze` — Form Data:**
```
file:      image file (JPG/PNG, max 10MB)
scan_type: "crop" or "soil"
location:  "Field A" (optional)
```

**GET `/scan/history` — Query params:** `?skip=0&limit=20&scan_type=crop&search=tomato` (`search` matches crop, disease, location and soil type)

### Chat

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/chat/message` | Send message to AI assistant | ✅ |
| GET | `/chat/history` | Get conversation history | ✅ |
| DELETE | `/chat/history` | Clear chat history | ✅ |

**POST `/chat/message` — JSON Body:**
```json
{
  "message": "What disease is affecting my tomato?",
  "scan_id": 42
}
```

**GET `/chat/history` — Query params:** `?skip=0&limit=50`. Returns the newest `limit` messages, oldest first. `skip=50` gives the 50 messages before those, for a "load older messages" button.

### Market

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/market/prices` | Latest live price per tracked crop | ❌ |
| GET | `/market/forecast` | AI 30-day price forecast | ❌ |
| GET | `/market/summary` | Market summary stats | ❌ |

**GET `/market/prices` — Query params:** `?category=Cereals&state=Maharashtra`

Only crops with a real price are returned, so the list can be shorter than 10, or empty right after startup. Each item:
```json
{
  "name": "Wheat", "variety": "Other", "category": "Cereals",
  "price": 2900, "market": "Washim(Ansing)", "state": "Maharashtra",
  "date": "2026-11-12",
  "prev": 2850, "prev_date": "2026-11-11",
  "change": 1.8, "trend": "up",
  "msp": 2275, "msp_diff": 27.5
}
```
Prices are ₹/quintal (`modal_price`). `change` compares with `prev_date` at the same mandi, which isn't always yesterday because mandis skip days. With no earlier price, `prev` and `prev_date` are `null` and `change` is `0`.

**GET `/market/forecast` — Query params:** `?crops=Tomato,Onion,Wheat` (default). Crops without a live price are skipped, and returns `[]` if none have one.

**GET `/market/summary`:** `best_performer`, `worst_performer` and `average_price` are `null` when there are no prices yet.

### Weather

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/weather/` | Current weather + forecast + advisory | ✅ |
| GET | `/weather/advisory` | AI farm advisory only | ✅ |

**Query params:** `?district=Nashik&state=Maharashtra` (defaults to the user's profile, then Pune)

**Response fields to know:**
- `is_mock`: `true` when OpenWeatherMap couldn't be reached (or has no key) and sample weather is returned. The advisory is then empty.
- `location`: the place the weather is for, e.g. `"Bhandara, Maharashtra"`.
- `forecast`: up to 40 entries, one every 3 hours (5 days). Empty if the forecast call failed.
- `current.rain_chance`: from the first forecast entry; `null` if the forecast is unavailable.
- `advisory`: empty when the weather is sample data or Gemini is unavailable.

### Community

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/community/posts` | Get community posts | Optional |
| POST | `/community/posts` | Create new post | ✅ |
| POST | `/community/posts/{id}/like` | Like or unlike a post | ✅ |
| POST | `/community/posts/{id}/bookmark` | Save or unsave a post | ✅ |
| DELETE | `/community/posts/{id}` | Delete own post | ✅ |
| GET | `/community/stats` | Members, states, posts today, trending tags, top contributors | ❌ |

**GET `/community/posts` — Query params:** `?tag=Disease+Control&search=tomato&skip=0&limit=20&saved=false` (`limit` max 50; `saved=true` needs login)

**POST `/community/posts` — Form Data:** `title` (5–255 chars), `body` (20+ chars), `tag` (one of the categories above), optional `emoji`, `post_tags` (JSON list) and `image`.

### Errors

| Status | Meaning |
|---|---|
| 401 | Missing or invalid token |
| 422 | Missing or invalid parameters |
| 503 | Gemini is overloaded. `detail` says to try again; retry after a moment |

---

## 🤖 AI Agents

### Crop Agent (`agents/crop_agent.py`)

Runs a **3-step agentic pipeline** for crop disease detection:

```
1. Gemini Vision →  Describe what's visible in the image
2. FAISS RAG  →  Retrieve top-3 matching disease documents
3. Gemini        →  Synthesize structured JSON diagnosis
```

The synthesis step takes the crop and every symptom only from the vision description. Location is used only to tailor treatment advice. If the vision response is empty or cut off, the scan fails with a 503 instead of returning a guessed diagnosis.

**Output includes:**
- Crop name and scientific name
- Disease identification with confidence %
- Health score (0–100)
- Severity (none / low / medium / high)
- Findings list with type and description
- Step-by-step treatment plan with urgency
- Prevention recommendations

### Soil Agent (`agents/soil_agent.py`)

Same 3-step pipeline for soil samples:

```
1. Gemini Vision →  Analyze color, texture, moisture
2. FAISS RAG  →  Retrieve soil type knowledge
3. Gemini        →  Generate NPK + pH report JSON
```

**Output includes:**
- Soil type classification (Alluvial, Black Cotton, Red Laterite, etc.)
- NPK values with status and ideal ranges
- pH value with correction advice
- Overall health score
- Crop suitability recommendations

### Weather Agent (`agents/weather_agent.py`)

```
OpenWeatherMap API  →  Current conditions + 5-day forecast (3-hour steps)
Gemini              →  AI farm advisory based on weather
```

**Output includes:**
- Real-time temperature, humidity, wind, visibility
- 5-day forecast with rain probability
- AI-generated farm advisory (spray timing, irrigation, warnings)
- Growing Degree Days (GDD) calculation
- `is_mock` and `location`, so the frontend can flag sample data and show which place it is

### Market Agent (`agents/market_agent.py`)

```
data.gov.in (Agmarknet)  →  Today's mandi records (fetched every 6 hours)
Mandi selection          →  One price per tracked crop
market_prices table      →  Daily history, so change % has a real previous price
Gemini + RAG             →  30-day AI price forecast (cached 6 hours)
```

**How a crop's mandi is chosen**, first match wins:
1. A mandi with stored history for that crop, most recently used first. This keeps the change % comparing the same market.
2. The crop's preferred mandi (e.g. Lasalgaon for onion).
3. The median-priced mandi in the crop's home state. Some states report far more mandis than others, which would skew a national median.
4. The median-priced mandi nationally.

**Things to know:**
- Requests send `User-Agent: AgriMind/1.0`; data.gov.in's firewall answers Python's default user agent with a 502.
- data.gov.in only accepts requests from India. With `MARKET_PRICES_FROM_DB=true`, the agent never calls it and serves the latest prices saved in the database instead.
- Sugarcane is tracked but usually absent: it's sold to mills at a fixed price rather than in mandis.
- MSP and category come from the agent's crop list, because the feed doesn't include them.

### Chat Orchestrator (`agents/orchestrator.py`)

```
User message
    + RAG (top-3 agricultural documents)
    + Latest scan context (crop/soil results)
    + User farm profile (location, crops, land)
    + Last 6 conversation messages
         ↓
    Gemini
         ↓
    Personalized agricultural response
```

---

## 📚 RAG Knowledge Base

FAISS is seeded with **15 agricultural documents** across 4 categories:

### 🦠 Crop Disease Documents (8 docs)
- Early Blight in Tomato (Alternaria solani)
- Late Blight in Potato/Tomato (Phytophthora infestans)
- Powdery Mildew in Wheat (Blumeria graminis)
- Yellow Mosaic Virus in Soybean
- Red Rot in Sugarcane
- Nitrogen Deficiency symptoms and correction
- Phosphorus Deficiency symptoms and correction
- Aphid infestation management

### 🪨 Soil Documents (3 docs)
- Alluvial Soil characteristics and management
- Black Cotton Soil (Regur) characteristics
- Ideal pH ranges for 10+ major crops

### 📈 Market Documents (2 docs)
- Onion price seasonality patterns in India
- MSP policy — Kharif & Rabi 2025-26 prices

### 🗓️ Farming Calendar Documents (2 docs)
- Kharif crop calendar (June–October)
- Rabi crop calendar (October–April)

> The index is saved in `faiss_store/` and loaded at startup. It's only rebuilt when that folder is missing, so after adding documents to `rag/knowledge_base.py`, delete `faiss_store/` and restart, then commit the new index.

---

## 🖥️ Pages & Screens

| Route | Page | Description |
|---|---|---|
| `/` | Dashboard | Upload panel + 5-tab insight panel |
| `/login` | Login | Phone + password sign in |
| `/signup` | Sign Up | 3-step: Account → Farm Details → Review |
| `/forgot-password` | Forgot Password | 2-step: Find Account → New Password → Success |
| `/history` | Scan History | Filterable list of all past scans |
| `/market` | Market Prices | Live mandi prices + AI forecast |
| `/community` | Community | Posts feed + Share Story modal |

### Dashboard Tabs
| Tab | Content |
|---|---|
| Crop Analysis | AI diagnosis, findings, treatment plan |
| Weather | Current conditions, 5-day forecast, GDD |
| Soil | NPK bars, health score, recommendations |
| Market | Crop price table, top movers |
| AI Chat | Conversational assistant with context |

---

## 🎨 Design System

The frontend uses a custom dark agricultural theme:

```css
--forest:       #0F1F0F   /* Page background */
--leaf:         #3D9A40   /* Primary green */
--leaf-light:   #52C455   /* Accent green */
--soil:         #C8860A   /* Warning / soil gold */
--soil-light:   #E8A020   /* Lighter gold */
--cream:        #F0EBE0   /* Primary text */
--sage-card:    #1A2E1A   /* Card background */
--muted:        #6B8F6B   /* Muted text */
```

**Typography:** Syne (display headings) + Inter (body text)

**Key animations:**
- `scan-ring` — pulsing ring on image upload
- `shimmer` — loading skeleton shimmer
- `pulse-dot` — live indicator dot
- `typing` — chat typing indicator

---

## 🔒 Security

- Passwords hashed with **bcrypt** (cost factor 12)
- **JWT tokens** with 7-day expiry
- All scan/chat endpoints require `Authorization: Bearer <token>`
- Images validated for type and size (max 10MB) before processing
- CORS limited to the origins in `CORS_ORIGINS` (localhost by default)
- SQL injection prevented by SQLAlchemy ORM parameterized queries
- Encrypted database connections with certificate checks when `MYSQL_SSL=true`
- API keys are removed from error messages before they are logged
- `.env` and `.env.prices` are git-ignored

---

## 📦 Running in Production

```bash
# Frontend
npm run build
npm start

# Backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```

Use one worker unless `MARKET_PRICES_FROM_DB=true`: each worker runs its own background price refresh, and several would fetch and save the same prices.

For production, also:
- Set `APP_SECRET_KEY` to a strong random 64-char string
- Set `MYSQL_SSL=true` for a cloud database
- Put Nginx in front of both services
- Set `CORS_ORIGINS` to your frontend's URL
- Set up log rotation for `uploads/` directory

### Free deployment (Render + TiDB Cloud + Vercel)

**1. Database: TiDB Cloud Serverless** (MySQL-compatible, free tier)
1. Create a Serverless cluster at [tidbcloud.com](https://tidbcloud.com).
2. Click **Connect** and note the host, port (usually `4000`), user and password.
3. Create the database: `CREATE DATABASE agrimind;`. Tables are created automatically on first start.

**2. Backend: Render** (free web service)
1. Push this repo to GitHub.
2. In Render, choose **New > Blueprint** and pick the repo. It reads [render.yaml](render.yaml).
3. Fill in the values it asks for: the TiDB details, `GEMINI_API_KEY`, `OPENWEATHER_API_KEY`, and `CORS_ORIGINS` (your Vercel URL, added after step 3).
4. When the deploy finishes, open `https://<your-service>.onrender.com/health`.

**3. Frontend: Vercel**
1. Import the frontend repo at [vercel.com](https://vercel.com).
2. Point its backend URL setting at your Render URL.
3. Copy the Vercel URL into `CORS_ORIGINS` on Render and redeploy.

**Free tier limits to expect**
- Render's free service sleeps after about 15 minutes without traffic; the next request takes up to a minute while it wakes.
- The disk is reset on every deploy and restart, so uploaded scan and post images in `uploads/` are lost.
- Gemini's free tier has daily request limits. Price forecasts are cached for 6 hours to save requests.
- Mandi prices come from a PC in India (next section) and only update while it's on.

### Mandi prices on the deployed backend

data.gov.in refuses connections from servers outside India, and Render has no Indian region. So the deployed backend (`MARKET_PRICES_FROM_DB=true` in `render.yaml`) never calls data.gov.in. It serves the latest prices saved in the database, and a PC in India saves them by running `scripts/update_prices.py`.

**1. Point the script at the cloud database.** Create `.env.prices` in the backend folder (it's git-ignored). The script reads `.env` first, then these values on top:
```env
MYSQL_HOST=gateway01.ap-southeast-1.prod.aws.tidbcloud.com
MYSQL_PORT=4000
MYSQL_USER=your_tidb_user
MYSQL_PASSWORD=your_tidb_password
MYSQL_DATABASE=agrimind
MYSQL_SSL=true
```
`DATA_GOV_API_KEY` comes from your normal `.env`.

**2. Run it once by hand:**
```powershell
venv\Scripts\python.exe scripts\update_prices.py
```
It prints each crop's price and mandi, and also writes to `scripts/update_prices.log`.

**3. Schedule it** to run every 3 hours and when you log in. Run this in PowerShell from the backend folder:
```powershell
$root = (Get-Location).Path
$action = New-ScheduledTaskAction -Execute "$root\venv\Scripts\pythonw.exe" -Argument "`"$root\scripts\update_prices.py`"" -WorkingDirectory $root
$every3h = New-ScheduledTaskTrigger -Once -At "09:00" -RepetitionInterval (New-TimeSpan -Hours 3)
$atLogon = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 15) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName "AgriMind mandi prices" -Action $action -Trigger @($every3h, $atLogon) -Settings $settings
```
To remove it later: `Unregister-ScheduledTask -TaskName "AgriMind mandi prices"`.

Prices only update while the PC is on. Each run updates that day's price, because data.gov.in adds records through the day. The API includes each price's `date`, so old prices are shown with their date.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

### Adding to the Knowledge Base

To expand the AI's agricultural knowledge, add new documents to `rag/knowledge_base.py`:

```python
{
    "id": "d009",
    "text": """Your agricultural knowledge here.
Crop: ...
Symptoms: ...
Treatment: ...""",
    "metadata": {"crop": "your_crop", "type": "disease|pest|nutrient|soil|market"}
}
```

## 📄 License

This project is licensed under the MIT License.


