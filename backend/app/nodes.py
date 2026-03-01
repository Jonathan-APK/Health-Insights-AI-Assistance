from app.graph_state import State
import logging

logger = logging.getLogger("nodes")

def compliance_node(state: State):
    logger.info("Reached Compliance Node")
    if state.final_response:
        return state
    else:
        state.final_response = state.pre_compliance_response
        return state