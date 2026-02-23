"""
Follow-up Agent
Handles user follow-up questions after report summary is generated.
Ensures no diagnosis or treatment advice is given.
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import logging
from core.prompt_loader import load_prompt_config
from config.settings import settings

logger = logging.getLogger("followup_agent")

def followup_agent(state: Dict[str, Any], model: str = "gpt-3.5-turbo", temperature: float = 0.2) -> Dict[str, Any]:
    """
    Expected state structure:
    {
        "session_id": str,
        "summary": str,
        "chat_history": list,
        "user_question": str
    }
    """
    try:
        session_id = state.get("session_id")
        report_summary = state.get("summary", "")
        user_question = state.get("user_question", "")
        chat_history = state.get("chat_history", [])

        logger.info(f"[FollowUpAgent] Session: {session_id}")
        logger.info(f"[FollowUpAgent] Question: {user_question}")

        # Load prompt config from JSON

        version = settings.PROMPT_VERSIONS.get("followup", settings.DEFAULT_PROMPT_VERSION)
        prompt_config = load_prompt_config(
            module="followup",
            key="main",
            version=version
        )

        system_prompt = prompt_config["system"]
        model = prompt_config["model"]
        temperature = prompt_config["temperature"]

        # Safety Prompt
        system_prompt = """
You are a medical report explanation assistant.

IMPORTANT RULES:
- You are NOT a doctor.
- Do NOT provide diagnosis.
- Do NOT recommend treatment.
- Do NOT give emergency instructions.
- Provide general educational explanations only.
- Encourage consulting healthcare professionals when appropriate.
"""

        # Construct conversation context
        history_text = ""
        for msg in chat_history:
            history_text += f"{msg['role']}: {msg['content']}\n"

        context = f"""
Medical Report Summary:
{report_summary}

Previous Conversation:
{history_text}

User Question:
{user_question}

Provide a clear, simple explanation:
"""

        llm = ChatOpenAI(model=model, temperature=temperature)
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ]).content

        logger.info(f"[FollowUpAgent] Response generated")

        return {
            "followup_answer": response,
            "chat_history": chat_history + [
                {"role": "user", "content": user_question},
                {"role": "assistant", "content": response},
            ],
        }

    except Exception as e:
        logger.error(f"[FollowUpAgent] Error: {e}", exc_info=True)
        raise
