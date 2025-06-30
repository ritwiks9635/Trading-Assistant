from langgraph.graph import StateGraph, END
from core.schemas import TradingState
from agents.data_collector_agent import data_collector_agent
from agents.ai_analyst_agent import ai_analyst_agent
from agents.trading_agent import trading_agent

def build_trading_pipeline():
    """
    Constructs the LangGraph DAG for the trading assistant.
    """

    graph = StateGraph(TradingState)

    # Define each agent as a node
    graph.add_node("collect_data", data_collector_agent)
    graph.add_node("analyze_data", ai_analyst_agent)
    graph.add_node("make_trade", trading_agent)

    # Chain them: collect → analyze → trade → END
    graph.set_entry_point("collect_data")
    graph.add_edge("collect_data", "analyze_data")
    graph.add_edge("analyze_data", "make_trade")
    graph.add_edge("make_trade", END)

    # Compile to DAG
    return graph.compile()