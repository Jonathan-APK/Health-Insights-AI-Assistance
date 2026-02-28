from app.state import State
import logging

logger = logging.getLogger("nodes")

def pii_removal_node(state: State):
    logger.info("Reached PII Removal Node")

    state.cleaned_text = state.parsed_text
    return state

def compliance_node(state: State):
    logger.info("Reached Compliance Node")
    if state.final_response:
        return state
    else:
        state.final_response = state.pre_compliance_response
        return state