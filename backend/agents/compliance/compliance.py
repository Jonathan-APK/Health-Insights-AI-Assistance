import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config.settings import settings
from core.prompt_loader import load_prompt_config

logger = logging.getLogger("compliance")

BLOCK_FALLBACK_MESSAGE = "This output has been blocked due to compliance violations. Please contact your administrator."
ERROR_FALLBACK_MESSAGE = "An error has occurred. Please try again later."

def now():
    return datetime.now(ZoneInfo("Asia/Singapore")).isoformat()

def compliance_node(state):
    """
    Generate insight summary from report text using LLM.
    """

    try:
        # Check if final_response already exists in state, if so return early to avoid redundant processing
        if state.final_response:
            logger.info("Skip compliance check as final_response already exists in state.")
            return {
            "next_node": "END",
            "last_updated": now()
            }

        # Load prompt config from JSON
        version = settings.PROMPT_VERSIONS.get("compliance", settings.DEFAULT_PROMPT_VERSION)
        analysis_config = load_prompt_config(
            module="compliance",
            key="compliance",
            version=version
        )

        system_prompt = analysis_config["system"]
        model = analysis_config["model"]
        temperature = analysis_config["temperature"]

        # Call LLM for classification with config from prompts.json
        llm = ChatOpenAI(model=model, temperature=temperature)
        result = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=state.pre_compliance_response)
        ]).content.strip()

        # Parse JSON response from LLM
        # Strip markdown code fences if present
        clean_result = result.replace("```json", "").replace("```", "").strip()
        compliance_response = json.loads(clean_result)

        verdict = compliance_response.get("verdict", "block")
        final_response = compliance_response.get("final_response", BLOCK_FALLBACK_MESSAGE)

        # Safety net: if verdict is block but LLM forgot to set a safe final_response
        if verdict == "block":
            final_response = BLOCK_FALLBACK_MESSAGE

        logger.info(f"Compliance verdict: {verdict}")
        logger.info(f"Reasons: {compliance_response.get('reasons', [])}")

        return {
            "compliance_response": compliance_response,   # full JSON object
            "final_response": final_response,             # extracted for easy access
            "next_node": "END",
            "last_updated": now()
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse compliance LLM response as JSON: {str(e)}")
        return {
            "compliance_response": {
                "verdict": "block",
                "reasons": ["Compliance agent returned malformed response."],
                "sanitized_output": None,
                "final_response": BLOCK_FALLBACK_MESSAGE
            },
            "final_response": BLOCK_FALLBACK_MESSAGE,
            "next_node": "END",
            "last_updated": now()
        }

    except Exception as e:
        msg = str(e)
        short_msg = msg[:100] if len(msg) > 100 else msg
        logger.error(f"Error Encountered: {short_msg}")
        return {
            "compliance_response": {
                "verdict": "block",
                "reasons": [f"Compliance check failed due to an internal error: {short_msg}"],
                "sanitized_output": None,
                "final_response": ERROR_FALLBACK_MESSAGE
            },
            "final_response": ERROR_FALLBACK_MESSAGE,
            "next_node": "END",
            "last_updated": now()
        }
