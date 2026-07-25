from services.gemini_service import generate
from rag.vector_store import similarity_search

AGRIMIND_SYSTEM = """You are AgriMind AI, an expert agricultural assistant for Indian farmers.
You have deep knowledge of:
- Crop diseases and treatments (Indian conditions)
- Soil health and fertilizer recommendations
- Indian market prices and MSP policies
- Kharif and Rabi farming calendars
- Weather impact on agriculture

Always give practical, specific advice with:
- Exact product names available in India
- Quantities and dosages
- Timing recommendations
- Cost-effective alternatives

Speak clearly and directly. Be concise. Reference the user's crop/soil scan context when available."""

async def chat(
    user_message: str,
    history: list[dict],
    scan_context: dict = None,
    user_profile: dict = None
) -> str:
    """
    Agentic chat pipeline:
    1. RAG retrieval based on user query
    2. Build context from scan + user profile
    3. Generate response with full context
    """

    # Step 1: RAG
    rag_docs = similarity_search(user_message, n_results=3)
    rag_context = "\n\n".join([f"[Knowledge]: {d['text']}" for d in rag_docs])

    # Step 2: Build scan context string
    scan_str = ""
    if scan_context:
        scan_str = f"""
LATEST SCAN CONTEXT:
- Crop: {scan_context.get('crop_name', 'Unknown')}
- Disease: {scan_context.get('disease', 'None')}
- Health Score: {scan_context.get('health_score', 'N/A')}/100
- Severity: {scan_context.get('severity', 'N/A')}
- AI Summary: {scan_context.get('ai_summary', '')}
"""

    # Step 3: User profile context
    profile_str = ""
    if user_profile:
        profile_str = f"""
FARMER PROFILE:
- Location: {user_profile.get('district', '')}, {user_profile.get('state', '')}
- Land: {user_profile.get('land_acres', '')} acres
- Farming type: {user_profile.get('farming_type', 'traditional')}
- Primary crops: {', '.join(user_profile.get('primary_crops') or [])}
"""

    # Step 4: Build conversation history
    history_str = ""
    for msg in history[-6:]:  # last 6 messages
        role = "Farmer" if msg["role"] == "user" else "AgriMind"
        history_str += f"{role}: {msg['content']}\n"

    # Step 5: Full prompt
    full_prompt = f"""{AGRIMIND_SYSTEM}

RELEVANT AGRICULTURAL KNOWLEDGE:
{rag_context}
{scan_str}
{profile_str}

CONVERSATION HISTORY:
{history_str}

Farmer: {user_message}
AgriMind:"""

    response = await generate(full_prompt)
    return response