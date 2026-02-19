from app.state import State
import logging

logger = logging.getLogger("nodes")

def risk_assessment_node(state: State):
    logger.info("Reached Risk Assessment Node")

    state.risk_assessment = ["High cholesterol"]
    return state

def insights_summary_node(state: State):
    logger.info("Reached Insights Summary Node")

    state.insight_summary = f"{state.clinical_analysis}; Risks: {', '.join(state.risk_assessment)}"
    if state.input_text:
        state.next_node = "qna"
    else: 
        state.next_node = "compliance"
    return state

def qna_node(state: State):
    logger.info("Reached QnA Node")
    # Past context + insight summary + input question 
    state.qna_answer = f"QnA response..."
    state.pre_compliance_response = f"QnA response..."
    return state

def pii_removal_node(state: State):
    logger.info("Reached PII Removal Node")

    state.cleaned_text = state.parsed_text
    return state

def compliance_node(state: State):
    logger.info("Reached Compliance Node")

    state.final_response = state.pre_compliance_response
    return state