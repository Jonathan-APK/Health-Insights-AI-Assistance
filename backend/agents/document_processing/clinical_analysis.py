from datetime import datetime
from multiprocessing import context
from zoneinfo import ZoneInfo
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from core.prompt_loader import load_prompt_config
from config.settings import settings
import logging

logger = logging.getLogger("clinical_analysis")

def now():
    return datetime.now(ZoneInfo("Asia/Singapore")).isoformat()

def clinical_analysis_node(state):
    """
    Send report text to LLM for clinical analysis.
    """

    print("=" * 50)
    print("CLINICAL ANALYSIS NODE")
    print("=" * 50)

    try:
        # Load prompt config from JSON
        version = settings.PROMPT_VERSIONS.get("clinical_analysis", settings.DEFAULT_PROMPT_VERSION)
        analysis_config = load_prompt_config(
            module="clinical_analysis",
            key="analysis",
            version=version
        )

        system_prompt = analysis_config["system"]
        model = analysis_config["model"]
        temperature = analysis_config["temperature"]
 
        # Call LLM for classification with config from prompts.json
        llm = ChatOpenAI(model=model, temperature=temperature)
        result = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=state.parsed_text)
        ]).content.strip().upper()
        
        if result == "OFF_TOPIC" and state.input_text:
            logger.info("Document classified as OFF_TOPIC with user input. Routing to QnA node.")
            return {
                "clinical_analysis": "The document does not appear to be health-related.",
                "insight_summary": "The document does not appear to be health-related.",
                "next_node": "qna",
                "last_updated": now()
            }
        elif result == "OFF_TOPIC" and (state.input_text is None or state.input_text.strip() == ""):
            logger.info("Document classified as OFF_TOPIC with no user input. Routing to Compliance node.")
            return {
                "clinical_analysis": "The document does not appear to be health-related.",
                "insight_summary": "The document does not appear to be health-related.",
                "next_node": "compliance",
                "pre_compliance_response": "Document uploaded is not health-related. Please provide health-related input for analysis.",
                "last_updated": now()
            }
        else:
            # For simplicity, we return a dummy analysis here.
            # In a real implementation, you'd parse the LLM's response for insights.
            logger.info("Document classified as ON_TOPIC. Proceeding with analysis.")
            return {
                "clinical_analysis": result,
                "next_node": "risk_assessment",
                "last_updated": now()
            }

    except Exception as e:
        msg = str(e)
        short_msg = msg[:100] if len(msg) > 100 else msg
        logger.error(f"Error Encountered: {short_msg}")
        print("=" * 50 + "\n")
        return {
            "next_node": "end",
            "final_response": f"An error occurred while analyzing the document: {str(e)}",
            "last_updated": now()
        }