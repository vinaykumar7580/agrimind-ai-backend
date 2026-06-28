from services.ollama_service import vision_analyze, generate_json
from rag.vector_store import similarity_search

SOIL_SYSTEM = """You are AgriMind's soil science expert specializing in Indian agricultural soils.
You analyze soil images and data to provide NPK estimates, pH ranges, and actionable fertilizer recommendations.
Respond ONLY in valid JSON."""

async def analyze_soil_image(image_bytes: bytes, user_context: dict = {}) -> dict:
    """
    Agentic soil analysis:
    1. Vision model reads soil color, texture, moisture
    2. RAG retrieves soil type knowledge
    3. LLM produces structured soil report
    """

    # Step 1: Vision
    vision_prompt = """Analyze this soil sample image:
1. Soil color (use Munsell notation if possible)
2. Texture appearance (sandy, loamy, clay, silty)
3. Moisture level (dry, moist, wet)
4. Visible organic matter
5. Any visible deficiency indicators
6. Estimated soil type"""

    vision_result = await vision_analyze(image_bytes, vision_prompt)

    # Step 2: RAG
    rag_docs = similarity_search(vision_result + " soil management", n_results=3)
    rag_context = "\n\n".join([d["text"] for d in rag_docs])

    # Step 3: Structured analysis
    prompt = f"""
VISION ANALYSIS OF SOIL:
{vision_result}

RELEVANT SOIL KNOWLEDGE:
{rag_context}

USER CONTEXT:
State: {user_context.get('state', 'Maharashtra')}
Primary crops: {user_context.get('primary_crops', [])}

Generate comprehensive soil analysis JSON:
{{
  "soil_type": "Alluvial|Black Cotton|Red Laterite|Sandy|Clayey",
  "texture": "Loamy|Sandy|Clay|Silt",
  "overall_health": 74,
  "ph": {{"value": 6.8, "status": "good|low|high", "ideal": "6.0-7.0"}},
  "nutrients": {{
    "nitrogen": {{"value": 42, "unit": "kg/ha", "status": "good|low|high", "ideal": "40-60", "pct": 55}},
    "phosphorus": {{"value": 18, "unit": "kg/ha", "status": "good|low|high", "ideal": "25-40", "pct": 35}},
    "potassium": {{"value": 156, "unit": "kg/ha", "status": "good|low|high", "ideal": "120-180", "pct": 72}},
    "organic_matter": {{"value": 2.1, "unit": "%", "status": "good|low|high", "ideal": "3-5%", "pct": 28}},
    "moisture": {{"value": 38, "unit": "%", "status": "good|low|high", "ideal": "35-45%", "pct": 62}},
    "ec": {{"value": 0.42, "unit": "dS/m", "status": "good|low|high"}}
  }},
  "recommendations": [
    "Specific fertilizer recommendation with product name and quantity"
  ],
  "best_crops": ["Crop1", "Crop2", "Crop3"],
  "ai_summary": "2-3 sentence summary of soil health"
}}"""

    result = await generate_json(prompt, SOIL_SYSTEM)
    return result