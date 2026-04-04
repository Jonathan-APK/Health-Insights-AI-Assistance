import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langfuse import Langfuse, get_client, observe, propagate_attributes

from config.settings import settings
from core.prompt_loader import load_prompt_config

load_dotenv()

logger = logging.getLogger("compliance")

langfusePrompt = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_BASE_URL,
)
langfuse = get_client()

BLOCK_FALLBACK_MESSAGE = "This output has been blocked due to compliance violations. Please contact your administrator."
ERROR_FALLBACK_MESSAGE = "An error has occurred. Please try again later."


def now():
    return datetime.now(ZoneInfo("Asia/Singapore")).isoformat()


@observe(as_type="generation")
def compliance_node(state):
    """
    Generate insight summary from report text using LLM.
    """

    try:
        # Check if final_response already exists in state, if so return early to avoid redundant processing
        if state.final_response:
            logger.info(
                "Skip compliance check as final_response already exists in state."
            )
            return {"next_node": "END", "last_updated": now()}

        # Load prompt config from JSON
        version = settings.PROMPT_VERSIONS.get(
            "compliance", settings.DEFAULT_PROMPT_VERSION
        )
        analysis_config = load_prompt_config(
            module="compliance", key="compliance", version=version
        )

        # langfuse prompt managment (START)
        try:
            prompt = langfusePrompt.get_prompt("compliance/systemPrompt")
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
            prompt = None
        # langfuse prompt managment (END)

        # Call LLM for classification with config from prompts.json
        llm = ChatOpenAI(model=model, temperature=temperature)
        response = llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=state.pre_compliance_response),
            ]
        )

        # Update langfuse monitoring w/o prompt management
        langfuse.update_current_generation(
            usage_details=response.response_metadata.get("token_usage"),
            model=response.response_metadata.get("model_name"),
            prompt=prompt,
        )

        # Add langfuse session tracking
        with propagate_attributes(
            session_id=state.session_id,
            user_id=state.session_id,
            trace_name="compliance",
        ):
            pass

        result = response.content.strip()

        # Parse JSON response from LLM
        # Strip markdown code fences if present
        clean_result = result.replace("```json", "").replace("```", "").strip()
        compliance_response = json.loads(clean_result)

        verdict = compliance_response.get("verdict", "block")
        final_response = compliance_response.get(
            "final_response", BLOCK_FALLBACK_MESSAGE
        )

        # Safety net: if verdict is block but LLM forgot to set a safe final_response
        if verdict == "block":
            final_response = BLOCK_FALLBACK_MESSAGE

        logger.info(f"Compliance verdict: {verdict}")
        logger.info(f"Reasons: {compliance_response.get('reasons', [])}")

        return {
            "compliance_response": compliance_response,  # full JSON object
            "final_response": final_response,  # extracted for easy access
            "next_node": "END",
            "last_updated": now(),
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse compliance LLM response as JSON: {str(e)}")
        return {
            "compliance_response": {
                "verdict": "block",
                "reasons": ["Compliance agent returned malformed response."],
                "sanitized_output": None,
                "final_response": BLOCK_FALLBACK_MESSAGE,
            },
            "final_response": BLOCK_FALLBACK_MESSAGE,
            "next_node": "END",
            "last_updated": now(),
        }

    except Exception as e:
        msg = str(e)
        short_msg = msg[:100] if len(msg) > 100 else msg
        logger.error(f"Error Encountered: {short_msg}")
        return {
            "compliance_response": {
                "verdict": "block",
                "reasons": [
                    f"Compliance check failed due to an internal error: {short_msg}"
                ],
                "sanitized_output": None,
                "final_response": ERROR_FALLBACK_MESSAGE,
            },
            "final_response": ERROR_FALLBACK_MESSAGE,
            "next_node": "END",
            "last_updated": now(),
        }
