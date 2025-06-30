from langgraph.graph import StateGraph, END
from core.schemas import TradingState
from nodes.user_query_node import user_query_node
from nodes.intent_parser_node import intent_parser_node
from nodes.report_node import report_node
from nodes.decision_router_node import decision_router_node
from agents.data_collector_agent import data_collector_agent
from agents.ai_analyst_agent import ai_analyst_agent
from agents.trading_agent import trading_agent

def build_dual_pipeline():
    graph = StateGraph(TradingState)

    # Step 1: user query + intent classification
    graph.add_node("user_query_node", user_query_node)
    graph.add_node("classify_intent", intent_parser_node)
    #graph.add_node("route_decision", decision_router_node)

    # Step 2: optional trading DAG (if needed)
    graph.add_node("run_trading_analysis", data_collector_agent)
    graph.add_node("analyze_data", ai_analyst_agent)
    graph.add_node("make_trade", trading_agent)

    # Step 3: final response generator
    graph.add_node("generate_assistant_response", report_node)

    # Graph flow
    graph.set_entry_point("user_query_node")
    graph.add_edge("user_query_node", "classify_intent")
    #graph.add_edge("classify_intent", "route_decision")

    graph.add_conditional_edges("classify_intent", decision_router_node)

    # If routed to trading, then flow to report generator
    graph.add_edge("run_trading_analysis", "analyze_data")
    graph.add_edge("analyze_data", "make_trade")
    graph.add_edge("make_trade", "generate_assistant_response")

    # End of the flow
    graph.add_edge("generate_assistant_response", END)

    return graph.compile()