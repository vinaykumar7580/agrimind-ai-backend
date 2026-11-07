from services.gemini_service import vision_analyze, generate_json
from rag.vector_store import similarity_search

CROP_SYSTEM = """You are AgriMind's expert crop disease detection AI with 20 years of agricultural science experience in India.
You analyze crop images and identify diseases, pests, and nutrient deficiencies.
Always provide specific, actionable advice with exact product names and dosages relevant to Indian agriculture.
Respond ONLY in valid JSON."""

async def analyze_crop_image(image_bytes: bytes, user_context: dict = {}) -> dict:
    """
    Agentic crop analysis pipeline:
    1. Vision model identifies the crop and visible symptoms
    2. RAG retrieves relevant disease/treatment knowledge
    3. LLM synthesizes a structured diagnosis
    """

    # Step 1: Vision analysis
    vision_prompt = """Analyze this crop image carefully. Identify:
1. The crop species (scientific name if possible)
2. Growth stage
3. Any visible diseases, discoloration, spots, lesions, wilting
4. Pest damage signs
5. Nutrient deficiency symptoms
6. Overall plant health (0-100)
Describe exactly what you see."""

    vision_result = await vision_analyze(image_bytes, vision_prompt)

    # Step 2: RAG — retrieve relevant knowledge
    rag_docs = similarity_search(vision_result, n_results=3)
    rag_context = "\n\n".join([d["text"] for d in rag_docs])

    # Step 3: Structured diagnosis via LLM
    diagnosis_prompt = f"""
You are analyzing a crop image. Here is what the vision model observed:

VISION ANALYSIS:
{vision_result}

RELEVANT AGRICULTURAL KNOWLEDGE:
{rag_context}

USER CONTEXT:
Location: {user_context.get('district', 'India')}, {user_context.get('state', '')}
Farming type: {user_context.get('farming_type', 'traditional')}

RULES:
- The VISION ANALYSIS is the only evidence of what is in the image. Take the crop identity and every symptom from it.
- Never infer the crop or a disease from the location, the farming type, or the knowledge documents.
- The knowledge documents may be unrelated. Use one only if it matches the crop and symptoms in the VISION ANALYSIS.
- Do not report symptoms the VISION ANALYSIS does not describe. If none are described, set disease to "Healthy" and severity to "none".
- Use the location only to tailor treatment and prevention advice.
- Set confidence according to how clearly the VISION ANALYSIS identifies the crop and condition.

Generate a complete crop diagnosis as JSON with this exact structure:
{{
  "crop_name": "Common name",
  "crop_scientific": "Scientific name",
  "growth_stage": "Stage description",
  "confidence": 92,
  "health_score": 68,
  "disease": "Primary disease/issue name or Healthy",
  "severity": "none|low|medium|high",
  "yield_impact_pct": -15,
  "findings": [
    {{"type": "warning|good|info", "label": "Finding title", "desc": "Brief description", "color_hint": "warning|good|info"}}
  ],
  "treatment": [
    {{"step": "Immediate", "action": "Specific action with product, dose, frequency", "urgent": true}}
  ],
  "prevention": ["Prevention tip 1", "Prevention tip 2"],
  "ai_summary": "2-3 sentence summary of the crop health and main recommendation"
}}"""

    result = await generate_json(diagnosis_prompt, CROP_SYSTEM)
    return result