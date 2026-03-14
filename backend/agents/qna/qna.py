from datetime import datetime
from zoneinfo import ZoneInfo
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from core.prompt_loader import load_prompt_config
from config.settings import settings
from core.context_builder import build_context
import logging

logger = logging.getLogger("Q&A Agent")

def now():
    return datetime.now(ZoneInfo("Asia/Singapore")).isoformat()

def qna_node(state):
    """
    Health and Medical Q&A Assistant
    """

    try:
        # Load prompt config from JSON
        version = settings.PROMPT_VERSIONS.get("qna", settings.DEFAULT_PROMPT_VERSION)
        analysis_config = load_prompt_config(
            module="qna",
            key="qna",
            version=version
        )

        system_prompt = analysis_config["system"]
        model = analysis_config["model"]
        temperature = analysis_config["temperature"]
 
        context = ""

        if state.insights_summary:
            context += f"\n\nDOCUMENT INSIGHT SUMMARY\n{state.insights_summary}\n\n"

        context += build_context(state)

        logger.info(f"Context built for QnA Node: {context[:5000]}...")  # Log only the first 5000 chars of context

        # Call LLM with config from prompts.json
        llm = ChatOpenAI(model=model, temperature=temperature)
        result = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ]).content.strip()
        
        return {
                "qna_answer": result,
                "pre_compliance_response": result,
                "last_updated": now()
        }

    except Exception as e:
        msg = str(e)
        short_msg = msg[:100] if len(msg) > 100 else msg
        logger.error(f"Error Encountered: {short_msg}")
        return {
            "next_node": "end",
            "final_response": f"An error has occurred. Please try again later.",
            "last_updated": now()
        }