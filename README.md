# 🌾 AgriMind AI

> AI-Powered Agriculture Intelligence Platform using LangGraph, LangChain, RAG, Ollama, FastAPI, PostgreSQL, Redis, and ChromaDB.

---

## 🚀 Overview

AgriMind AI is an advanced multi-agent agriculture assistant designed to help farmers make data-driven decisions.

The platform combines:

* 🤖 Agentic AI
* 🧠 Large Language Models (Ollama)
* 📚 Retrieval-Augmented Generation (RAG)
* 🌦 Weather Intelligence
* 🌱 Soil Analysis
* 🦠 Disease Detection
* 📈 Market Intelligence

to provide personalized recommendations for crop management, disease diagnosis, fertilizer usage, and market opportunities.

---

# 🎯 Problem Statement

Farmers often face challenges such as:

* Unpredictable weather conditions
* Soil nutrient deficiencies
* Crop diseases and pest attacks
* Lack of market insights
* Difficulty understanding agricultural documents
* Choosing the right crop at the right time

AgriMind AI solves these problems by acting as a 24/7 intelligent farming assistant.

---

# ✨ Features

## 💬 AI Agriculture Chat

Ask questions such as:

```text
Can I grow cotton next month?

What fertilizer is recommended for wheat?

How can I increase soybean production?
```

---

## 📄 PDF Knowledge Base

Upload:

* Agriculture guides
* Government schemes
* Crop manuals
* Research papers

and chat with them using RAG.

---

## 🌦 Weather Intelligence

Provides:

* Temperature
* Humidity
* Rainfall
* Wind Speed
* Forecast Analysis

---

## 🌱 Soil Analysis

Upload soil reports and receive:

* Soil Health Score
* Nutrient Analysis
* Fertilizer Recommendation
* Crop Suitability Suggestions

---

## 🦠 Disease Detection

Upload crop leaf images to detect:

* Leaf Spot
* Powdery Mildew
* Bacterial Blight
* Rust Disease

and receive treatment recommendations.

---

## 📈 Market Intelligence

Provides:

* Crop Prices
* Market Trends
* Profitability Insights
* Selling Recommendations

---

# 🏗 System Architecture

```text
User
 │
 ▼
Next.js Frontend
 │
 ▼
FastAPI Backend
 │
 ▼
LangGraph Orchestrator
 │
 ▼
Planner Agent
 │
 ├───────────────┬───────────────┬───────────────┬───────────────┐
 ▼               ▼               ▼               ▼               ▼
Crop Agent   Weather Agent   Soil Agent   Disease Agent   Market Agent
 │               │               │               │               │
 └───────────────┴───────────────┴───────────────┴───────────────┘
                         │
                         ▼
                Context Aggregation
                         │
                         ▼
                    Ollama LLM
                         │
                         ▼
                  Final Response
```

---

# 🧠 Agent Architecture

## Planner Agent

Responsible for:

* Understanding user intent
* Selecting required agents
* Routing requests dynamically

Example:

```json
{
  "question": "Can I grow cotton next month?"
}
```

Planner Output:

```json
{
  "tasks": [
    "crop",
    "weather",
    "soil",
    "market"
  ]
}
```

---

## Crop Agent

Uses:

* LangChain
* ChromaDB
* RAG
* Ollama

Responsibilities:

* Search uploaded documents
* Retrieve farming knowledge
* Generate crop recommendations

---

## Weather Agent

Uses:

* OpenWeather API

Provides:

* Temperature
* Humidity
* Rainfall
* Weather Forecast

---

## Soil Agent

Analyzes:

```text
soil_report.xlsx
```

Checks:

* pH
* Nitrogen
* Potassium
* Phosphorus
* Organic Carbon

Provides:

* Soil Health Report
* Nutrient Deficiency Detection
* Fertilizer Recommendations

---

## Disease Agent

Uses:

* YOLO
* Computer Vision

Detects:

* Leaf Spot
* Bacterial Blight
* Powdery Mildew
* Rust

Provides:

* Disease Name
* Severity
* Treatment Plan

---

## Market Agent

Provides:

* Crop Prices
* Market Trends
* Demand Analysis
* Profitability Recommendations

---

# 📚 RAG Workflow

```text
PDF Upload
    │
    ▼
PyPDFLoader
    │
    ▼
Text Extraction
    │
    ▼
Chunking
    │
    ▼
Embeddings
    │
    ▼
ChromaDB
    │
    ▼
Retriever
    │
    ▼
Ollama
    │
    ▼
Answer
```

---

# 🔄 LangGraph Workflow

```text
User Query
     │
     ▼
Planner Agent
     │
     ▼
Agent Executor
     │
     ▼
Selected Agents
     │
     ▼
Context Aggregation
     │
     ▼
Answer Agent
     │
     ▼
Redis Memory
     │
     ▼
Response
```

---

# 🗄 Database Architecture

## PostgreSQL

### Users Table

```sql
id
name
email
mobile
created_at
```

### Chats Table

```sql
id
user_id
question
answer
created_at
```

### Files Table

```sql
id
user_id
filename
path
file_type
uploaded_at
```

### Document Metadata Table

```sql
id
file_id
total_pages
chunk_count
indexed_at
```

---

# 🧠 Memory Layer

Redis is used for:

* Session Storage
* Conversation History
* Agent Memory
* User Context

Benefits:

* Faster Responses
* Context Awareness
* Personalized Recommendations

---


# 🚀 Future Enhancements

* Voice Assistant
* Multi-Language Support
* Satellite Image Analysis
* Crop Yield Prediction
* Drone Integration
* IoT Sensor Integration
* Mobile Application
* Farmer Dashboard
* WhatsApp Integration

---

# 📊 Expected Impact

AgriMind AI helps farmers:

✅ Improve crop productivity

✅ Reduce crop losses

✅ Detect diseases early

✅ Optimize fertilizer usage

✅ Improve soil health

✅ Increase profitability


