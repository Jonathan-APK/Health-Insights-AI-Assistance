from datetime import datetime
from zoneinfo import ZoneInfo
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from core.prompt_loader import load_prompt_config
from config.settings import settings
import logging

logger = logging.getLogger("orchestrator")

def now():
    return datetime.now(ZoneInfo("Asia/Singapore")).isoformat()

def orchestrator_node(state):
    """
    This is the routing brain.
    It uses an LLM to classify text-only messages as medical or off-topic.
    It returns a dict of updates (LangGraph merges them into State).
    """
    print("=" * 50)
    print("ORCHESTRATOR NODE")
    print("=" * 50)

    has_text = bool(state.input_text)
    has_file = bool(state.file_meta)

    # -----------------------------
    # TEXT ONLY = classify with LLM
    # -----------------------------
    if has_text and not has_file:
        logger.info("Has Text Only")

        # Load classification prompt config from JSON
        version = settings.PROMPT_VERSIONS.get("orchestrator", settings.DEFAULT_PROMPT_VERSION)
        classification_config = load_prompt_config(
            module="orchestrator",
            key="classification",
            version=version
        )
        
        system_prompt = classification_config["system"]
        model = classification_config["model"]
        temperature = classification_config["temperature"]

        context = build_context(state)

        logger.info("Orchestrator build context:\n %s", context)

        # Call LLM for classification with config from prompts.json
        llm = ChatOpenAI(model=model, temperature=temperature)
        result = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ]).content.strip().upper()

        logger.info("Orchestrator classification result: %s", result)

        if result == "OFF_TOPIC":
            # Load off-topic response prompt config from JSON
            response_config = load_prompt_config(
                module="orchestrator",
                key="off_topic_response",
                version=version
            )
            
            response_prompt = response_config["system"]
            response_model = response_config["model"]
            response_temperature = response_config["temperature"]
            
            llm_response = ChatOpenAI(model=response_model, temperature=response_temperature)
            contextual_response = llm_response.invoke([
                SystemMessage(content=response_prompt),
                HumanMessage(content=f"User message: '{state.input_text}'")
            ]).content.strip()
            
            logger.info("Generated off-topic response: %s", contextual_response)
            print("=" * 50 +"\n")

            return {
                "pre_compliance_response": contextual_response,
                "next_node": "end",
                "last_updated": now()
            }
        
        # Medical = route to QnA
        print("=" * 50 +"\n")
        return {
            "next_node": "qna",
            "last_updated": now()
        }

    # -----------------------------
    # FILE ONLY = document pipeline
    # -----------------------------
    if has_file and not has_text:
        logger.info("Has File Only")

        print("=" * 50 + "\n")
        return {
            "next_node": "doc_pipeline",
            "last_updated": now()
        }

    # -----------------------------
    # BOTH FILE + TEXT = doc pipeline first, then QnA
    # -----------------------------
    if has_file and has_text:
        logger.info("Has File and Text")

        print("=" * 50 +"\n")
        return {
            "next_node": "doc_then_qna",
            "last_updated": now()
        }

    print("=" * 50 + "\n")

    # Fallback
    return {
        "next_node": "end",
        "pre_compliance_response": "No valid input provided.",
        "last_updated": now()
    }

def build_context(state) -> str:
    """
    Build structured context for LLM classification.
    Clear formatting helps LLM understand conversation flow and clinical context.
    """
    
    context_parts = []
    
    # 1. Past conversation with turn numbers and clear role distinction
    conversation = state.conversation_history
    if conversation:
        recent = conversation[-5:]
        conv_text = []
        for i, msg in enumerate(recent, 1):
            conv_text.append(f"  Turn {i}:")
            conv_text.append(f"    User: {msg['input_text_snippet']}")
            conv_text.append(f"    Assistant: {msg['response_snippet']}")
        context_parts.append("CONVERSATION HISTORY:\n" + "\n".join(conv_text))
    
    # 2. Past analysis with structured sections
    analysis = state.analysis
    if analysis:
        latest = analysis[-1]
        analysis_lines = [
            f"PREVIOUS DOCUMENT ANALYSIS: {latest['filename']}",
            f"  • Clinical Findings: {latest['clinical_analysis']}",
            f"  • Risk Flags: {', '.join(latest['risk_assessment']) if latest['risk_assessment'] else 'None'}"
        ]
        context_parts.append("\n".join(analysis_lines))
    
    # 4. Current message (highlighted)
    context_parts.append(f"NEW MESSAGE FROM USER:\n  \"{state.input_text}\"")
    
    return "\n\n".join(context_parts)