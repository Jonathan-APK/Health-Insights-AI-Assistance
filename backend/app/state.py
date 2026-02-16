from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo

class State(BaseModel):
    # Core session info
    session_id: str
    input_text: Optional[str] = None
    file_meta: Optional[Dict[str, Any]] = None
    file_bytes: Optional[bytes] = None

    # Workflow routing flag 
    next_node: Optional[str] = None

    # Conversation history
    conversation_history: Optional[list] = None  # list of past conversations
    
    # Past analysis 
    analysis: Optional[list] = None  # list of analysis results

    # Document processing outputs
    parsed_text: Optional[str] = None           # before PII removal
    cleaned_text: Optional[str] = None          # after PII removal
    clinical_analysis: Optional[str] = None     # summary of findings
    risk_assessment: Optional[list] = None      # list of risk flags
    insight_summary: Optional[str] = None       # consolidated insights

    # QnA output
    qna_answer: Optional[str] = None

    # Pre-compliance response (before compliance node processes it)
    pre_compliance_response: Optional[str] = None

    # Final response (after compliance check and any modifications)
    final_response: Optional[str] = None

    created_at: str = datetime.now(ZoneInfo("Asia/Singapore")).isoformat()
    last_updated: str = datetime.now(ZoneInfo("Asia/Singapore")).isoformat()
