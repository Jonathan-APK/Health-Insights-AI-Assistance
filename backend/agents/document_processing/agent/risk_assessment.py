import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langfuse import Langfuse, get_client, observe, propagate_attributes

from config.settings import settings
from core.prompt_loader import load_prompt_config

load_dotenv()

logger = logging.getLogger("risk_assessment")

langfusePrompt = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_BASE_URL"),
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

        # langfuse prompt managment (START)
        try:
            prompt = langfusePrompt.get_prompt("risk_assessment/systemPrompt")
            system_prompt = prompt.compile()
            config = prompt.config
            model = config.get("model", "gpt-4o-mini")
            temperature = config.get("temperature", 0.2)
            logger.info(
                f"Langfuse prompt fetched successfully: version {prompt.version}"
            )
        except Exception:
            # fallback to local prompt config if langfuse prompt retrieval fails
            logger.info(
                "Failed to load system prompt from Langfuse, falling back to local prompt config."
            )
            system_prompt = analysis_config["system"]
            model = analysis_config["model"]
            temperature = analysis_config["temperature"]
        # langfuse prompt managment (END)

        # Call LLM for classification with config from prompts.json
        llm = ChatOpenAI(model=model, temperature=temperature)
        response = llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=state.parsed_text),
            ]
        )

        # Update langfuse monitoring w/o prompt management
        langfuse.update_current_generation(
            usage_details=response.response_metadata.get("token_usage"),
            model=response.response_metadata.get("model_name"),
        )

        # Add langfuse session tracking
        with propagate_attributes(
            session_id=state.session_id,
            user_id=state.session_id,
            trace_name="risk_assessment",
        ):
            pass

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
