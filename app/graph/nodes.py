from app.memory.store import memory_store
from langchain_ollama import ChatOllama
import json

from app.agents.crop_agent import crop_agent
from app.agents.weather_agent import weather_agent
from app.agents.soil_agent import soil_agent
from app.agents.market_agent import market_agent

llm = ChatOllama(
    model="llama3",
    temperature=0.3
)


def planner_node(state):

    user_id = state["user_id"]

    history = memory_store.get(user_id)

    prompt = f"""
You are an agriculture AI planner.

User History:
{history}

Question:
{state['query']}

Decide tasks:
- crop
- weather
- soil
- market

Return JSON:
{{"tasks": []}}
"""

    response = llm.invoke(prompt)

    try:
        tasks = json.loads(response.content)["tasks"]
    except:
        tasks = ["crop"]

    state["tasks"] = tasks

    return state

def agent_executor_node(state):

    tasks = state["tasks"]

    context_parts = []

    # CROp AGENT
    if "crop" in tasks:
        state["crop_data"] = crop_agent(state["query"])
        context_parts.append("CROP:\n" + state["crop_data"])

    # WEATHER AGENT
    if "weather" in tasks:
        state["weather_data"] = weather_agent()
        context_parts.append(f"WEATHER:\n{state['weather_data']}")

    # SOIL AGENT
    if "soil" in tasks:
        state["soil_data"] = soil_agent()
        context_parts.append(f"SOIL:\n{state['soil_data']}")

    # MARKET AGENT
    if "market" in tasks:
        state["market_data"] = market_agent()
        context_parts.append(f"MARKET:\n{state['market_data']}")

    state["context"] = "\n\n".join(context_parts)

    return state

def answer_node(state):

    prompt = f"""
You are an expert agriculture advisor AI.

Use ALL provided data to give best farming advice.

DATA:
{state['context']}

QUESTION:
{state['query']}

Give:
- Clear recommendation
- Reason
- Risk factors
- Best practice
"""

    response = llm.invoke(prompt)

    state["answer"] = response.content

    return state

def memory_node(state):

    user_id = state["user_id"]

    memory_store.add(user_id, state["query"])
    memory_store.add(user_id, state["answer"])

    return state