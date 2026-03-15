from datetime import datetime
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel


class State(BaseModel):
    # Core session info
    session_id: str
    session_data: Optional[Dict[str, Any]] = (
        None  # Store any session-specific data here
    )
    input_text: Optional[str] = None
    file_meta: Optional[Dict[str, Any]] = None
    file_bytes: Optional[bytes] = None
    file: Optional[Any] = None  # Store the UploadFile object for later use if needed

    # Workflow routing flag
    next_node: Optional[str] = None

    # Conversation history
    conversation_history: Optional[list] = None  # list of past conversations

    # Past analysis
    analysis: Optional[list] = None  # list of analysis results

    # Input Guardrail
    input_guardrail_passed: Optional[bool] = None
    input_guardrail_block_reason: Optional[str] = None

    # Document processing outputs
    parsed_text: Optional[str] = None  # before PII removal
    sanitized_text: Optional[str] = None  # after PII removal
    clinical_analysis: Optional[str] = None  # summary of findings
    risk_assessment: Optional[str] = None  # list of risk flags
    insights_summary: Optional[str] = None  # consolidated insights

    # QnA output
    qna_answer: Optional[str] = None

    # Pre-compliance response (before compliance node processes it)
    pre_compliance_response: Optional[str] = None

    # Compliance check result (stores the full JSON verdict object)
    compliance_response: Optional[Dict[str, Any]] = None

    # Final response (after compliance check and any modifications)
    final_response: Optional[str] = None

    created_at: str = datetime.now(ZoneInfo("Asia/Singapore")).isoformat()
    last_updated: str = datetime.now(ZoneInfo("Asia/Singapore")).isoformat()
