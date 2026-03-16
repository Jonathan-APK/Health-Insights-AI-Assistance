import logging
from datetime import datetime
import re
from zoneinfo import ZoneInfo

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config.settings import settings
from core.context_builder import build_context
from core.prompt_loader import load_prompt_config

logger = logging.getLogger("Q&A Agent")

# flow
# user input -> prompt injection detection -> input sanitization -> update state.user_input-> context building -> llm call -> response


def now():
    return datetime.now(ZoneInfo("Asia/Singapore")).isoformat()

# Prompt injection detection
def detect_prompt_injection(user_input: str) -> bool:
    suspicious_patterns = [
        "ignore previous instructions",
        "reveal system prompt",
        "developer mode",
        "system prompt",
        "bypass filters",
        "jailbreak"]
    lower_input = user_input.lower()
    for pattern in suspicious_patterns:
        if pattern in lower_input:
            logger.warning(f"Potential prompt injection detected: '{pattern}' found in user input.")
            return True
        
    return False

# Sanitization to remove potentially harmful content
def sanitize_user_input(user_input: str) -> str:
    patterns = [r"ignore previous instructions",
                r"reveal system prompt",
                r"developer mode",
                r"system prompt",
                r"bypass filters",
                r"jailbreak"]
    
    # Basic sanitization to remove potentially harmful content
    sanitized = user_input
    for pattern in patterns:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
    return sanitized

def qna_node(state):
    """
    Health and Medical Q&A Assistant
    """

    try:
        # Load prompt config from JSON
        version = settings.PROMPT_VERSIONS.get("qna", settings.DEFAULT_PROMPT_VERSION)
        analysis_config = load_prompt_config(module="qna", key="qna", version=version)

        system_prompt = analysis_config["system"]
        model = analysis_config["model"]
        temperature = analysis_config["temperature"]

        context = ""

        if state.insights_summary:
            context += f"\n\nDOCUMENT INSIGHT SUMMARY\n{state.insights_summary}\n\n"

        # Check for potential prompt injection
        user_input = state.user_input
        # detect prompt injection
        if detect_prompt_injection(user_input):
            return {
                "qna_answer": "Your request cannot be processed due to suspicious content.",
                "pre_compliance_response": "Blocked Suspicious Prompt",
                "last_updated": now(),
            }
        
        # Sanitize user input before processing
        clean_user_input = sanitize_user_input(user_input)
        # log sanitized input
        logger.info(f"Sanitized user input for QnA Node: {clean_user_input}...") 

        # Update state with sanitized input
        state.user_input = clean_user_input

        context += build_context(state)

        logger.info(
            f"Context built for QnA Node: {context[:5000]}..."
        )  # Log only the first 5000 chars of context

        # Call LLM with config from prompts.json
        llm = ChatOpenAI(model=model, temperature=temperature)
        result = llm.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=clean_user_input)]
        ).content.strip()

        return {
            "qna_answer": result,
            "pre_compliance_response": result,
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
