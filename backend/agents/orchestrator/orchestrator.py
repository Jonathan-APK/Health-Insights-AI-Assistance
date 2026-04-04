import logging
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

logger = logging.getLogger("orchestrator")

langfusePrompt = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_BASE_URL,
)
langfuse = get_client()


def now():
    return datetime.now(ZoneInfo("Asia/Singapore")).isoformat()


@observe(as_type="span")
def orchestrator_node(state):
    """
    This is the routing brain.
    It uses an LLM to classify text-only messages as medical or off-topic.
    It returns a dict of updates (LangGraph merges them into State).
    """
    logger.info(f"Langfuse host: '{settings.LANGFUSE_BASE_URL}'")

    # Add langfuse session tracking
    with propagate_attributes(
        session_id=state.session_id,
        user_id=state.session_id,
        trace_name="orchestrator",
    ):
        has_text = bool(state.input_text)
        has_file = bool(state.file_meta)

        # -----------------------------
        # TEXT ONLY = classify with LLM
        # -----------------------------
        if has_text and not has_file:
            logger.info("Has Text Only")

            # Load classification prompt config from JSON
            version = settings.PROMPT_VERSIONS.get(
                "orchestrator", settings.DEFAULT_PROMPT_VERSION
            )
            classification_config = load_prompt_config(
                module="orchestrator", key="classification", version=version
            )

            # langfuse prompt managment (START)
            try:
                classification_prompt = langfusePrompt.get_prompt(
                    "orchestrator/classificationSystemPrompt"
                )
                system_prompt = classification_prompt.compile()
                config = classification_prompt.config
                model = config.get("model", "gpt-4o-mini")
                temperature = config.get("temperature", 0.2)
                logger.info(
                    f"Langfuse prompt fetched successfully: version {classification_prompt.version}"
                )
            except Exception:
                # fallback to local prompt config if langfuse prompt retrieval fails
                logger.info(
                    "Failed to load classification system prompt from Langfuse, falling back to local prompt config."
                )
                system_prompt = classification_config["system"]
                model = classification_config["model"]
                temperature = classification_config["temperature"]
                classification_prompt = None
            # langfuse prompt managment (END)

            context = build_context(state)

            logger.info("Orchestrator build context:\n %s", context)

            # Call LLM for classification with config from prompts.json
            llm = ChatOpenAI(model=model, temperature=temperature)
            response = llm.invoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=context)]
            )

            # Update langfuse monitoring w/o prompt management
            langfuse.update_current_generation(
                usage_details=response.response_metadata.get("token_usage"),
                model=response.response_metadata.get("model_name"),
                prompt=classification_prompt,
            )

            result = response.content.strip().upper()

            logger.info("Orchestrator classification result: %s", result)

            if result == "OFF_TOPIC":
                # Load off-topic response prompt config from JSON
                response_config = load_prompt_config(
                    module="orchestrator", key="off_topic_response", version=version
                )

                # langfuse prompt managment (START)
                try:
                    off_topic_prompt = langfusePrompt.get_prompt(
                        "orchestrator/offTopicSystemPrompt"
                    )
                    response_prompt = off_topic_prompt.compile()
                    config = off_topic_prompt.config
                    response_model = config.get("model", "gpt-4o-mini")
                    response_temperature = config.get("temperature", 0.7)
                    logger.info(
                        f"Langfuse prompt fetched successfully: version {off_topic_prompt.version}"
                    )
                except Exception:
                    # fallback to local prompt config if langfuse prompt retrieval fails
                    logger.info(
                        "Failed to load off topic system prompt from Langfuse, falling back to local prompt config."
                    )
                    response_prompt = response_config["system"]
                    response_model = response_config["model"]
                    response_temperature = response_config["temperature"]
                    off_topic_prompt = None
                # langfuse prompt managment (END)

                llm_response = ChatOpenAI(
                    model=response_model, temperature=response_temperature
                )
                contextual_result = llm_response.invoke(
                    [
                        SystemMessage(content=response_prompt),
                        HumanMessage(content=f"User message: '{state.input_text}'"),
                    ]
                )

                # Update langfuse monitoring w/o prompt management
                langfuse.update_current_generation(
                    usage_details=contextual_result.response_metadata.get(
                        "token_usage"
                    ),
                    model=contextual_result.response_metadata.get("model_name"),
                    prompt=off_topic_prompt,
                )

                contextual_response = contextual_result.content.strip()

                logger.info("Generated off-topic response: %s", contextual_response)
                print("=" * 50 + "\n")

                return {
                    "pre_compliance_response": contextual_response,
                    "next_node": "compliance",
                    "last_updated": now(),
                }

            # Medical = route to QnA
            print("=" * 50 + "\n")
            return {"next_node": "qna", "last_updated": now()}

        # -----------------------------
        # FILE ONLY = document pipeline
        # -----------------------------
        if has_file and not has_text:
            logger.info("Has File Only")

            return {"next_node": "doc_pipeline", "last_updated": now()}

        # -----------------------------
        # BOTH FILE + TEXT = doc pipeline first, then QnA
        # -----------------------------
        if has_file and has_text:
            logger.info("Has File and Text")

            print("=" * 50 + "\n")
            return {"next_node": "doc_then_qna", "last_updated": now()}

        # Fallback
        return {
            "next_node": "compliance",
            "final_response": "An error has occurred. Please try again later.",
            "last_updated": now(),
        }
