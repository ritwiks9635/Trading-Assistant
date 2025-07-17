from langgraph.graph import StateGraph, END
from core.schemas import TradingState

# Core nodes
from nodes.user_query_node import user_query_node
from nodes.query_parser_node import query_parser_node
from nodes.intent_parser_node import intent_parser_node
from nodes.decision_router_node import decision_router_node

# Trading flow nodes
from nodes.top_movers_node import top_movers_node
from nodes.report_node import report_node
from agents.data_collector_agent import data_collector_agent
from agents.ai_analyst_agent import ai_analyst_agent
from agents.trading_agent import trading_agent
from nodes.gpt_analyst_node import gpt_analyst_node

# Specialized response nodes
from nodes.stock_insight_node import stock_insight_node
from nodes.technical_analysis_node import technical_analysis_node
from nodes.risk_analysis_node import risk_analysis_node
from nodes.portfolio_node import portfolio_node
from nodes.macro_trend_node import macro_trend_node

def build_dual_pipeline():
    graph = StateGraph(TradingState)

    # ⏳ Entry flow
    graph.add_node("step_user_input", user_query_node)
    graph.add_node("step_parse_query", query_parser_node)
    graph.add_node("step_classify_intent", intent_parser_node)
    graph.add_node("step_route_decision", decision_router_node)

    # 🧠 Top mover + GPT route
    graph.add_node("step_fetch_top_movers", top_movers_node)
    graph.add_node("step_gpt_analysis", gpt_analyst_node)

    # 📈 Core trading execution path
    graph.add_node("step_collect_data", data_collector_agent)
    graph.add_node("step_analyze_data", ai_analyst_agent)
    graph.add_node("step_make_trade", trading_agent)

    # 📊 Specialized insight modules
    graph.add_node("step_stock_insight", stock_insight_node)
    graph.add_node("step_technical_analysis", technical_analysis_node)
    graph.add_node("step_risk_analysis", risk_analysis_node)
    graph.add_node("step_portfolio_guidance", portfolio_node)
    graph.add_node("step_macro_trends", macro_trend_node)

    # 🧾 Final formatted reply
    graph.add_node("step_generate_response", report_node)

    # ▶️ Start of pipeline
    graph.set_entry_point("step_user_input")
    graph.add_edge("step_user_input", "step_parse_query")
    graph.add_edge("step_parse_query", "step_classify_intent")
    graph.add_edge("step_classify_intent", "step_route_decision")

    # ✅ Routing handled by decision_router_node's return: {"next": "step_xyz"}
    graph.add_conditional_edges("step_route_decision", lambda state: state.next)

    # ✅ Trading analysis path
    graph.add_edge("step_collect_data", "step_analyze_data")
    graph.add_edge("step_analyze_data", "step_make_trade")
    graph.add_edge("step_make_trade", "step_generate_response")

    # ✅ Top movers → GPT analysis
    graph.add_edge("step_fetch_top_movers", "step_gpt_analysis")
    graph.add_edge("step_gpt_analysis", "step_generate_response")

    # ✅ Direct-return nodes (end here)
    graph.add_edge("step_stock_insight", END)
    graph.add_edge("step_technical_analysis", END)
    graph.add_edge("step_risk_analysis", END)
    graph.add_edge("step_portfolio_guidance", END)
    graph.add_edge("step_macro_trends", END)

    # ✅ Fallback final response (e.g., unknown intent)
    graph.add_edge("step_generate_response", END)

    return graph.compile()
