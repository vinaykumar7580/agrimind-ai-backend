from typing import TypedDict, List, Dict, Any


class AgentState(TypedDict):

    user_id: str

    query: str

    tasks: List[str]

    context: str

    answer: str

    memory: List[str]

    weather_data: Dict[str, Any]
    soil_data: Dict[str, Any]
    market_data: Dict[str, Any]
    crop_data: str