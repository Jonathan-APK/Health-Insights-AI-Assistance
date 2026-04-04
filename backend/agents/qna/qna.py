import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langfuse import Langfuse, get_client, observe, propagate_attributes

from config.settings import settings
from core.context_builder import build_context
from core.prompt_loader import load_prompt_config

load_dotenv()

logger = logging.getLogger("Q&A Agent")

langfusePrompt = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_BASE_URL,
)
langfuse = get_client()

# flow
# user input -> prompt injection detection -> input sanitization -> update state.input_text-> context building -> llm call -> response


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
        "jailbreak",
    ]
    lower_input = user_input.lower()
    for pattern in suspicious_patterns:
        if pattern in lower_input:
            logger.warning(
                f"Potential prompt injection detected: '{pattern}' found in user input."
            )
            return True

    return False


# Sanitization to remove potentially harmful content
def sanitize_user_input(user_input: str) -> str:
    patterns = [
        r"ignore previous instructions",
        r"reveal system prompt",
        r"developer mode",
        r"system prompt",
        r"bypass filters",
        r"jailbreak",
    ]

    # Basic sanitization to remove potentially harmful content
    sanitized = user_input
    for pattern in patterns:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
    return sanitized


# Additional check for medical advice in output
def detect_medical_output_risk(output: str) -> bool:
    risky_keywords = [
        "take .* mg",
        "dosage",
        "prescribe",
        "stop taking",
        "start taking",
        "you should take",
        "diagnose",
        "treatment plan",
    ]

    for keyword in risky_keywords:
        if re.search(keyword, output, re.IGNORECASE):
            logger.warning(
                f"Potential medical advice detected in output: '{keyword}' found."
            )
            return True

    return False


@observe(as_type="generation")
def qna_node(state):
    """
    Health and Medical Q&A Assistant
    """

    try:
        # Load prompt config from JSON
        version = settings.PROMPT_VERSIONS.get("qna", settings.DEFAULT_PROMPT_VERSION)
        analysis_config = load_prompt_config(module="qna", key="qna", version=version)

        # langfuse prompt managment (START)
        try:
            prompt = langfusePrompt.get_prompt("qna/systemPrompt")
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

        context = ""

        if state.insights_summary:
            context += f"\n\nDOCUMENT INSIGHT SUMMARY\n{state.insights_summary}\n\n"

        # Check for potential prompt injection
        user_input = state.input_text
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
        state.input_text = clean_user_input

        context += build_context(state)

        # If context is empty after building, return a default response
        if not context.strip():
            return {
                "qna_answer": "No relevant context available to answer your question.",
                "pre_compliance_response": "No Context Available",
                "last_updated": now(),
            }

        logger.info(
            f"Context built for QnA Node: {context[:5000]}..."
        )  # Log only the first 5000 chars of context

        # Determine context strength based on length (To be enhanced if possible as using only length to determine strength)
        context_strength = "strong" if len(context) > 100 else "weak"

        # Call LLM with config from prompts.json
        # Injects retrived context and user questions into the LLM prompt to enable grounded answering with optional to fallback to general knowledge
        llm = ChatOpenAI(model=model, temperature=temperature)
        response = llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(
                    content=f"""
                CONTEXT STRENGTH: {context_strength}
                CONTEXT:
                {context if context else "No relevant context available."}
                If context is strong -> prioritize context in answer.
                If context is weak -> rely more on general knowledge.
                QUESTION:
                {clean_user_input}
                """
                ),
            ]
            # content=clean_user_input)]
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
            trace_name="qna",
        ):
            pass

        result = response.content.strip()

        # Check for potential medical advice in output and modify response if necessary
        if detect_medical_output_risk(result):
            logger.warning(
                "Potential medical advice detected in LLM output. Modifying response to ensure safety."
            )
            result = (
                result
                + "\n\n Disclaimer: The response contains information that may be considered medical advice. Please consult a qualified healthcare professional for personalized guidance."
            )

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
