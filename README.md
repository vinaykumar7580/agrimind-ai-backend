# 🌱 AgriMind AI — Smart Crop Intelligence Platform


## 🌾 Overview

**AgriMind AI** is a full-stack agricultural intelligence platform that empowers Indian farmers with AI-powered tools. Upload a photo of your crop or soil and instantly get:

- 🔬 **Crop disease diagnosis** with treatment plans
- 🪨 **Soil NPK & pH analysis** with fertilizer recommendations
- 🌤️ **Weather-based farm advisory**
- 📈 **Live mandi prices** from 500+ markets
- 🤖 **Conversational AI assistant** with agricultural expertise
- 🌍 **Farmer community** to share knowledge and experiences

The platform uses a **3-step agentic AI pipeline**: vision model analysis → RAG knowledge retrieval → structured LLM synthesis — all running **100% locally** via Ollama.

---

## ✨ Features

### 🔬 Crop Analysis
- Upload crop photos for instant AI diagnosis
- Identifies 50+ diseases with confidence scores
- Detects pest infestations and nutrient deficiencies
- Provides step-by-step treatment plans with exact product names and dosages
- Health scoring (0–100) and yield impact estimation

### 🪨 Soil Analysis
- Visual soil analysis from photos
- NPK (Nitrogen, Phosphorus, Potassium) estimation
- pH level assessment with correction advice
- Organic matter and moisture content analysis
- Crop suitability recommendations

### 🌤️ Weather Intelligence
- Real-time weather from OpenWeatherMap API
- 7-day forecast with rain probability
- AI-generated farm advisory based on weather conditions
- Growing Degree Days (GDD) tracker for harvest timing
- Irrigation and spraying schedule recommendations

### 📈 Market Prices
- Live prices from 10+ major crops across Indian mandis
- MSP (Minimum Support Price) comparison
- AI-powered 30-day price forecast with confidence scores
- Top gainer/loser tracking
- Category filtering (Cereals, Oilseeds, Vegetables, Pulses, etc.)

### 🤖 AI Chat Assistant
- Context-aware responses using your latest scan data
- RAG-powered answers from agricultural knowledge base
- Personalized advice based on your farm profile and location
- Full conversation history stored per user

### 👥 Community
- Share farming stories, tips, and questions
- Like, bookmark, and share posts
- Trending topics and top contributor leaderboard
- Category filters: Disease Control, Yield Tips, Market Tips, Questions

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
| Python | 3.11+ | Backend language |
| FastAPI | 0.111 | Async REST API framework |
| SQLAlchemy | 2.0 | ORM for MySQL |
| PyMySQL | 1.1 | MySQL driver |
| FAISS | Vector database for RAG |
| Passlib + bcrypt | 1.7 | Password hashing |
| python-jose | 3.3 | JWT token management |
| httpx | 0.27 | Async HTTP client |
| Pillow | 10.3 | Image processing |

### AI / ML
| Technology | Purpose |
|---|---|
| Ollama | Local LLM inference server |
| LLaVA | Vision model for crop/soil image analysis |
| LLaMA 3.2 | Text generation for diagnosis and chat |
| nomic-embed-text | Text embeddings for RAG |
| FAISS | Vector similarity search |

### Database
| Technology | Purpose |
|---|---|
| MySQL 8.0 | Primary relational database |
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
│  │  │  (LLaVA +   │  │  (LLaVA +   │  │  (LLaMA 3.2)  │  │ │
│  │  │  LLaMA 3.2) │  │  LLaMA 3.2) │  └───────────────┘  │ │
│  │  └──────┬──────┘  └──────┬──────┘                      │ │
│  │         │                │                              │ │
│  │  ┌──────▼────────────────▼──────────────────────────┐  │ │
│  │  │                 RAG PIPELINE                      │  │ │
│  │  │  Query → FAISS Search → Context Injection      │  │ │
│  │  └───────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────┬───────────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
┌─────────────────┐       ┌──────────────────┐
│   MySQL 8.0     │       │   Ollama Server   │
│                 │       │   (Port 11434)    │
│ • users         │       │                  │
│ • scans         │       │ • llava           │
│ • chat_messages │       │ • llama3.2        │
│ • community_    │       │ • nomic-embed-    │
│   posts         │       │   text            │
│ • market_prices │       └──────────────────┘
│ • weather_logs  │
└─────────────────┘
       +
┌─────────────────┐
│    FAISS    │
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
│  Model: LLaVA               │
│  → Identifies crop/disease  │
│  → Describes visual symptoms│
└──────────────┬──────────────┘
               │  Vision text output
               ▼
┌─────────────────────────────┐
│  STEP 2: RAG Retrieval      │
│  Store: FAISS           │
│  → Similarity search on     │
│    vision output            │
│  → Returns top 3-4 relevant │
│    knowledge documents      │
└──────────────┬──────────────┘
               │  Context documents
               ▼
┌─────────────────────────────┐
│  STEP 3: LLM Synthesis      │
│  Model: LLaMA 3.2           │
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
│   │       ├── WeatherPanel.tsx         # Weather + 7-day forecast
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
    ├── models.py                        # ORM models (6 tables)
    ├── auth.py                          # JWT + bcrypt auth
    │
    ├── agents/
    │   ├── crop_agent.py                # Vision → RAG → Crop diagnosis
    │   ├── soil_agent.py                # Vision → RAG → Soil analysis
    │   ├── weather_agent.py             # OpenWeather + AI advisory
    │   ├── market_agent.py              # Price data + AI forecast
    │   └── orchestrator.py             # Chat agent with full context
    │
    ├── rag/
    │   ├── knowledge_base.py            # 20+ agricultural documents
    │   └── vector_store.py              # FAISS init + search
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
    │   ├── ollama_service.py            # LLM + vision + embedding calls
    │   └── image_service.py            # Image save/resize/serve
    │
    ├── requirements.txt
    └── .env
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
| Ollama | latest | [ollama.ai](https://ollama.ai) |
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

# Activate (Windows)
source venv/Scripts/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your MySQL credentials and API keys

# 4. Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: **http://localhost:8000**
API Docs at: **http://localhost:8000/docs**

---

### Ollama Setup

```bash
# 1. Install Ollama
# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Mac
brew install ollama

# 2. Start Ollama server
ollama serve

# 3. Pull required models (in a new terminal)
ollama pull llama3.2          # Text generation (~2GB)
ollama pull llava             # Vision model (~4GB)
ollama pull nomic-embed-text  # Embeddings (~274MB)

# 4. Verify models are running
ollama list
```

> ⚠️ **Hardware Requirements:** Minimum 8GB RAM for llama3.2 + llava. 16GB recommended for smooth performance.

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
-- 6 tables auto-created by SQLAlchemy

users              -- Farmer accounts with profile data
scans              -- Crop & soil scan results with AI analysis
chat_messages      -- Conversation history per user
community_posts    -- Farmer stories, tips, questions
market_prices      -- Crop price data from mandis
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

# ── Ollama ────────────────────────────────────
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2                    # Text model
OLLAMA_VISION_MODEL=llava                # Vision model


# ── OpenWeatherMap (free tier) ────────────────
# Get free API key at: https://openweathermap.org/api
OPENWEATHER_API_KEY=your_openweather_api_key
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
| GET | `/scan/history` | Get all scans for current user | ✅ |
| GET | `/scan/{scan_id}` | Get single scan details | ✅ |
| PUT | `/scan/{scan_id}/status` | Update scan status | ✅ |

**POST `/scan/analyze` — Form Data:**
```
file:      image file (JPG/PNG, max 10MB)
scan_type: "crop" or "soil"
location:  "Field A" (optional)
```

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

### Market

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/market/prices` | Get all crop prices | ❌ |
| GET | `/market/forecast` | AI 30-day price forecast | ❌ |
| GET | `/market/summary` | Market summary stats | ❌ |

**Query params:** `?category=Cereals&state=Maharashtra`

### Weather

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/weather/` | Current weather + forecast | ✅ |
| GET | `/weather/advisory` | AI farm advisory only | ✅ |

**Query params:** `?district=Nashik&state=Maharashtra`

### Community

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/community/posts` | Get community posts | ❌ |
| POST | `/community/posts` | Create new post | ✅ |
| POST | `/community/posts/{id}/like` | Like a post | ✅ |
| DELETE | `/community/posts/{id}` | Delete own post | ✅ |

**Query params:** `?tag=Disease+Control&search=tomato&skip=0&limit=20`

---

## 🤖 AI Agents

### Crop Agent (`agents/crop_agent.py`)

Runs a **3-step agentic pipeline** for crop disease detection:

```
1. LLaVA Vision  →  Describe what's visible in the image
2. FAISS RAG  →  Retrieve top-3 matching disease documents
3. LLaMA 3.2     →  Synthesize structured JSON diagnosis
```

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
1. LLaVA Vision  →  Analyze color, texture, moisture
2. FAISS RAG  →  Retrieve soil type knowledge
3. LLaMA 3.2     →  Generate NPK + pH report JSON
```

**Output includes:**
- Soil type classification (Alluvial, Black Cotton, Red Laterite, etc.)
- NPK values with status and ideal ranges
- pH value with correction advice
- Overall health score
- Crop suitability recommendations

### Weather Agent (`agents/weather_agent.py`)

```
OpenWeatherMap API  →  Current conditions + 7-day forecast
LLaMA 3.2           →  AI farm advisory based on weather
```

**Output includes:**
- Real-time temperature, humidity, wind, visibility
- 7-day forecast with rain probability
- AI-generated farm advisory (spray timing, irrigation, warnings)
- Growing Degree Days (GDD) calculation

### Market Agent (`agents/market_agent.py`)

```
Seed price database  →  Current prices from 10 crops
LLaMA 3.2 + RAG      →  30-day AI price forecast
```

### Chat Orchestrator (`agents/orchestrator.py`)

```
User message
    + RAG (top-3 agricultural documents)
    + Latest scan context (crop/soil results)
    + User farm profile (location, crops, land)
    + Last 6 conversation messages
         ↓
    LLaMA 3.2
         ↓
    Personalized agricultural response
```

---

## 📚 RAG Knowledge Base

FAISS is seeded with **20+ agricultural documents** across 4 categories:

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

> Documents are loaded into FAISS on first startup and persisted to disk. Add more documents in `rag/knowledge_base.py` to expand AI knowledge.

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
| Weather | Current conditions, 7-day forecast, GDD |
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
- CORS restricted to `localhost:3000` in development
- SQL injection prevented by SQLAlchemy ORM parameterized queries

---

## 📦 Running in Production

```bash
# Frontend
npm run build
npm start

# Backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Use a process manager
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

For production, also:
- Set `APP_SECRET_KEY` to a strong random 64-char string
- Configure MySQL with SSL
- Put Nginx in front of both services
- Use environment-specific CORS origins
- Set up log rotation for `uploads/` directory

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


