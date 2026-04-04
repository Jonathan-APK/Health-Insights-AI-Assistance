import json
import logging
import re
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langfuse import Langfuse, get_client, observe, propagate_attributes

from config.settings import settings
from core.file_validators import FileValidator
from core.prompt_loader import load_prompt_config

load_dotenv()

logger = logging.getLogger("input_guardrail")

langfusePrompt = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_BASE_URL,
)
langfuse = get_client()

ERROR_FALLBACK_MESSAGE = "An error has occurred. Please try again later."


def now():
    return datetime.now(ZoneInfo("Asia/Singapore")).isoformat()


@observe(as_type="generation")
async def input_guardrail_node(state):
    """
    This is the input guardrail.
    Responsible for file validation (type, size), and text prompt checks and rate limit checks.
    """

    try:
        # 1. Must have either message or file
        validate_input(state.input_text, state.file)

        # 2. Rate limit checks
        session_data = state.session_data
        message_count = session_data.get("message_count", 0)
        upload_count = session_data.get("upload_count", 0)

        # Check max messages per session
        if message_count >= settings.MAX_MESSAGES_PER_SESSION:
            return {
                "session_data": None,
                "input_guardrail_passed": False,
                "input_guardrail_block_reason": "Max messages per session exceeded.",
                "final_response": "You have reached the maximum number of messages for this session. Please start a new session.",
                "next_node": "END",
                "last_updated": now(),
                "file": None,
                "limit_reached": True,
            }

        # Check max uploads per session
        if state.file and upload_count >= settings.MAX_UPLOADS_PER_SESSION:
            return {
                "input_guardrail_passed": False,
                "input_guardrail_block_reason": "Max uploads per session exceeded.",
                "final_response": "You have reached the maximum number of file uploads for this session. You can still ask questions based on the documents already uploaded, or start a new session to upload more files.",
                "next_node": "END",
                "last_updated": now(),
                "file": None,
                "session_data": None,
                "limit_reached": True,
            }

        # 3. File validation
        file_meta = None
        file_bytes = None

        if state.file:
            # Validate file type
            file_bytes = await state.file.read()
            is_valid, error = FileValidator.validate_file(
                file_bytes, state.file.filename
            )
            if not is_valid:
                return {
                    "session_data": None,
                    "input_guardrail_passed": False,
                    "input_guardrail_block_reason": "Failed file validation: " + error,
                    "final_response": "File upload failed. Please try again with a valid PDF file under 5MB.",
                    "next_node": "END",
                    "last_updated": now(),
                    "file": None,
                }

            file_meta = {
                "filename": state.file.filename,
                "content_type": state.file.content_type,
                "size": len(file_bytes),
            }

        # 4. Text prompt checks
        if state.input_text:
            cleaned_text = state.input_text.strip()

            # Empty/whitespace only
            if not cleaned_text:
                return {
                    "session_data": None,
                    "input_guardrail_passed": False,
                    "input_guardrail_block_reason": "Input text cannot be empty.",
                    "final_response": "Input text cannot be empty.",
                    "next_node": "END",
                    "last_updated": now(),
                    "file": None,
                }

            # Max length
            if len(cleaned_text) > 2000:
                return {
                    "session_data": None,
                    "input_guardrail_passed": False,
                    "input_guardrail_block_reason": "Input text exceeds the maximum allowed length.",
                    "final_response": "Input text exceeds the maximum allowed length.",
                    "next_node": "END",
                    "last_updated": now(),
                    "file": None,
                }

            # Spam/repetition check
            if len(set(cleaned_text.replace(" ", ""))) < 5:
                return {
                    "session_data": None,
                    "input_guardrail_passed": False,
                    "input_guardrail_block_reason": "Input text appears to be invalid.",
                    "final_response": "Input text appears to be invalid.",
                    "next_node": "END",
                    "last_updated": now(),
                    "file": None,
                }

            # Regex prompt injection
            injection_patterns = [
                r"ignore (all |previous |prior )?instructions",
                r"you are now",
                r"disregard (all |previous )?",
                r"forget (all |previous |your )?instructions",
                r"act as (a |an )?",
                r"jailbreak",
                r"dan mode",
            ]
            for pattern in injection_patterns:
                if re.search(pattern, cleaned_text, re.IGNORECASE):
                    return {
                        "session_data": None,
                        "input_guardrail_passed": False,
                        "input_guardrail_block_reason": "Your request could not be processed.",
                        "final_response": "I cannot process that request. Please rephrase and try again.",
                        "next_node": "END",
                        "last_updated": now(),
                        "file": None,
                    }

            # LLM classifier to check prompt injection and harmful content
            version = settings.PROMPT_VERSIONS.get(
                "input_guardrail", settings.DEFAULT_PROMPT_VERSION
            )
            classification_config = load_prompt_config(
                module="input_guardrail", key="classification", version=version
            )

            # langfuse prompt managment (START)
            try:
                prompt = langfusePrompt.get_prompt("input_guardrail/systemPrompt")
                system_prompt = prompt.compile()
                config = prompt.config
                model = config.get("model", "gpt-4o-mini")
                temperature = config.get("temperature", 0)
                logger.info(
                    f"Langfuse prompt fetched successfully: version {prompt.version}"
                )
            except Exception:
                # fallback to local prompt config if langfuse prompt retrieval fails
                logger.info(
                    "Failed to load system prompt from Langfuse, falling back to local prompt config."
                )
                system_prompt = classification_config["system"]
                model = classification_config["model"]
                temperature = classification_config["temperature"]
                prompt = None
            # langfuse prompt managment (END)

            # Call LLM for classification with config from prompts.json
            llm = ChatOpenAI(model=model, temperature=temperature)
            response = llm.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=state.input_text),
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
                trace_name="input_guardrail",
            ):
                pass

            result = response.content.strip()

            logger.info("input_guardrail classification result: %s", result)

            try:
                classification = json.loads(result)
                verdict = classification.get("verdict", "pass").lower()
                threat_type = classification.get("threat_type", "none")
                reason = classification.get("reason", None)

                logger.info(
                    "input_guardrail verdict: %s | threat_type: %s | reason: %s",
                    verdict,
                    threat_type,
                    reason,
                )

                if verdict == "block":
                    return {
                        "session_data": None,
                        "input_guardrail_passed": False,
                        "input_guardrail_block_reason": reason,
                        "final_response": "I cannot process that request. Please rephrase and try again.",
                        "next_node": "END",
                        "last_updated": now(),
                        "file": None,
                    }

            except (json.JSONDecodeError, AttributeError) as e:
                logger.error(
                    "input_guardrail LLM classification parse error: %s", str(e)
                )
                return {
                    "session_data": None,
                    "input_guardrail_passed": False,
                    "input_guardrail_block_reason": "LLM classification failed to parse.",
                    "final_response": ERROR_FALLBACK_MESSAGE,
                    "next_node": "END",
                    "last_updated": now(),
                    "file": None,
                }

        # PASS
        return {
            "session_data": None,
            "input_guardrail_passed": True,
            "input_guardrail_block_reason": None,
            "file": None,  # clear file object after validation
            "file_meta": file_meta,
            "file_bytes": file_bytes,
            "next_node": "orchestrator",
            "last_updated": now(),
        }

    except Exception as e:
        msg = str(e)
        short_msg = msg[:100] if len(msg) > 100 else msg
        logger.error(f"Error Encountered: {short_msg}")
        return {
            "session_data": None,
            "file": None,  # clear file object after validation
            "final_response": ERROR_FALLBACK_MESSAGE,
            "next_node": "END",
            "last_updated": now(),
        }


def validate_input(message: Optional[str], file: Optional[UploadFile]):
    if not message and not file:
        raise HTTPException(
            status_code=400, detail="Must provide either a message or a file"
        )
