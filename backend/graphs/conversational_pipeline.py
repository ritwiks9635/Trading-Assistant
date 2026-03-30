from langgraph.graph import StateGraph, END
from core.schemas import TradingState
from agents.conversational_agent import conversational_agent

def build_conversational_pipeline():
    graph = StateGraph(TradingState)

    graph.add_node("chat", conversational_agent)

    graph.set_entry_point("chat")
    graph.add_edge("chat", END)

    return graph.compile()