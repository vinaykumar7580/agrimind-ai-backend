from langgraph.graph import StateGraph

from app.graph.state import AgentState

from app.graph.nodes import (
    planner_node,
    agent_executor_node,
    answer_node,
    memory_node
)

# Create graph
graph = StateGraph(AgentState)

# -------------------
# NODES
# -------------------

graph.add_node("planner", planner_node)

graph.add_node("agent_executor", agent_executor_node)

graph.add_node("answer", answer_node)

graph.add_node("memory", memory_node)

# -------------------
# FLOW (IMPORTANT)
# -------------------

graph.set_entry_point("planner")

graph.add_edge("planner", "agent_executor")

graph.add_edge("agent_executor", "answer")

graph.add_edge("answer", "memory")

graph.set_finish_point("memory")

workflow = graph.compile()