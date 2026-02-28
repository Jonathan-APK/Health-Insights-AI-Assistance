from datetime import datetime
from multiprocessing import context
from zoneinfo import ZoneInfo
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from core.prompt_loader import load_prompt_config
from config.settings import settings
import logging

logger = logging.getLogger("insights_summary")

def now():
    return datetime.now(ZoneInfo("Asia/Singapore")).isoformat()

def insights_summary_node(state):
    """
    Generate insight summary from report text using LLM.
    """

    print("=" * 50)
    print("INSIGHT SUMMARY NODE")
    print("=" * 50)

    try:
        # Load prompt config from JSON
        version = settings.PROMPT_VERSIONS.get("insights_summary", settings.DEFAULT_PROMPT_VERSION)
        analysis_config = load_prompt_config(
            module="insights_summary",
            key="summarize",
            version=version
        )

        system_prompt = analysis_config["system"]
        model = analysis_config["model"]
        temperature = analysis_config["temperature"]
 
        # Combine both Clinical Analysis and Risk Assessment fields
        combined_content = f"""Clinical Analysis:
        {state.clinical_analysis}

        Risk Assessment:
        {state.risk_assessment}"""

        # Call LLM for classification with config from prompts.json
        llm = ChatOpenAI(model=model, temperature=temperature)
        result = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=combined_content)
        ]).content.strip()
        
        if state.input_text:
            logger.info("User entered text, past to QnA agent for further processing.")
            return {
                "insights_summary": result,
                "next_node": "qna",
                "last_updated": now()
            }
        else:
            logger.info("User only uploaded document with no additional input. Routing to Compliance agent for further processing.")
            return {
                "insights_summary": result,
                "pre_compliance_response": result,
                "next_node": "compliance",
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