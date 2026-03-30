from nodes.user_query_node import user_query_node
from nodes.intent_parser_node import intent_parser_node
from nodes.report_node import report_node

def conversational_agent(state):
    """
    Full conversational pipeline: query → intent → assistant response.
    """
    state = user_query_node(state)
    state = intent_parser_node(state)
    state = report_node(state)
    return state