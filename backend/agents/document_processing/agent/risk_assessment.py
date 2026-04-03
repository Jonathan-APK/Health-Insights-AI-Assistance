import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langfuse import observe, get_client, Langfuse
from dotenv import load_dotenv

from config.settings import settings
from core.prompt_loader import load_prompt_config

load_dotenv()

logger = logging.getLogger("risk_assessment")

langfusePrompt = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_BASE_URL")
)
langfuse = get_client()

def now():
    return datetime.now(ZoneInfo("Asia/Singapore")).isoformat()

@observe(as_type="generation")
def risk_assessment_node(state):
    """
    Reviews medical records and generates a short, minimal summary of key health risks
    """

    try:
        # Load prompt config from JSON
        version = settings.PROMPT_VERSIONS.get(
            "risk_assessment", settings.DEFAULT_PROMPT_VERSION
        )
        analysis_config = load_prompt_config(
            module="risk_assessment", key="risk_assessment", version=version
        )

        system_prompt = analysis_config["system"]
        model = analysis_config["model"]
        temperature = analysis_config["temperature"]

        # Call LLM for classification with config from prompts.json
        llm = ChatOpenAI(model=model, temperature=temperature)
        response = (
            llm.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=state.parsed_text),
                ]
            )
        )

        # Update langfuse monitoring w/o prompt management
        langfuse.update_current_generation(
            usage_details=response.response_metadata.get("token_usage"),
            model=response.response_metadata.get("model_name")
        )

        result = response.content.strip().upper()

        return {
            "risk_assessment": result,
            "next_node": "insights_summary",
            "last_updated": now(),
        }

    except Exception as e:
        msg = str(e)
        short_msg = msg[:100] if len(msg) > 100 else msg
        logger.error(f"Error Encountered: {short_msg}")
        return {
            "next_node": "end",
            "final_response": "An error has occurred. Please try again later.",
            "last_updated": now(),
        }
