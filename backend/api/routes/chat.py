import json
import logging
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, File, Form, Header, Request, UploadFile
from fastapi.responses import StreamingResponse
from langgraph.graph import END, START, StateGraph

from agents.compliance.compliance import compliance_node
from agents.document_processing.agent.clinical_analysis import clinical_analysis_node
from agents.document_processing.agent.insights_summary import insights_summary_node
from agents.document_processing.agent.risk_assessment import risk_assessment_node
from agents.document_processing.document_parser import document_parser_node
from agents.document_processing.pii_removal import pii_removal_node
from agents.guardrail.input_guardrail import input_guardrail_node
from agents.orchestrator import orchestrator
from agents.qna.qna import qna_node
from app.graph_state import State

logger = logging.getLogger("chat")
router = APIRouter()

NODE_STATUS_PUBLIC = {
    "input_guardrail": "Checking your request...",
    "orchestrator": "Understanding your request...",
    "document_parser": "We’re reading your document...",
    "pii_removal": "Protecting your sensitive information...",
    "clinical_analysis": "Analyzing your health information...",
    "risk_assessment": "Looking for important health insights...",
    "insights_summary": "Summarizing key findings...",
    "qna": "Answering your question...",
    "compliance": "Final check...",
}


# Helper to format SSE messages
def sse_event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@router.post("/chat")
async def chat(
    request: Request,
    message: Optional[str] = Form(None, description="User's text message"),
    file: Optional[UploadFile] = File(None, description="Optional file upload"),
    x_session_id: Optional[str] = Header(None),
):
    # Get managers from app state
    session_manager = request.app.state.session_manager
    logger.info(f"Session from header: {x_session_id}")
    # Get session data and set session id in response header
    session_data = await session_manager.get_or_create_session(x_session_id)
    current_session_id = session_data["session_id"]

    logger.info(f"Session data:\n{json.dumps(session_data, indent=2)}")

    # Build graph once and store in app.state
    graph = request.app.state.graph

    initial_state = State(
        session_id=current_session_id,
        session_data=session_data,
        input_text=message,
        file=file,
        conversation_history=session_data["conversation_history"] or [],
        analysis=session_data["analysis"] or [],
    )

    # -------------------------------------------------------
    # SSE Generator — streams node status + final response
    # -------------------------------------------------------
    async def pipeline_stream():
        final_state = None

        try:
            async for event in graph.astream_events(initial_state, version="v2"):
                event_type = event["event"]
                node_name = event.get("name", "")

                # Node started
                if event_type == "on_chain_start" and node_name in NODE_STATUS_PUBLIC:
                    msg = NODE_STATUS_PUBLIC[node_name]
                    logger.info(f"NODE STARTED: {node_name}")
                    yield sse_event({"type": "status", "message": msg})

                elif event_type == "on_chain_end" and node_name in NODE_STATUS_PUBLIC:
                    logger.info(f"NODE COMPLETED: {node_name}")

                # Top-level chain done
                elif event_type == "on_chain_end" and node_name == "LangGraph":
                    final_state = event["data"].get("output", {})

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            yield sse_event(
                {
                    "type": "error",
                    "message": "An error occurred while processing your request.",
                }
            )
            return

        if not final_state:
            yield sse_event({"type": "error", "message": "No response generated."})
            return

        # --------------------------------------------------
        # Persist session after pipeline completes
        # --------------------------------------------------
        now = datetime.now(ZoneInfo("Asia/Singapore")).isoformat()

        session_data["last_active"] = now
        session_data["message_count"] += 1 if message else 0
        session_data["upload_count"] += 1 if file else 0

        if final_state.get("file_meta"):
            session_data["upload_history"].append(
                {
                    "filename": final_state.get("file_meta")["filename"],
                    "content_type": final_state.get("file_meta")["content_type"],
                    "size": final_state.get("file_meta")["size"],
                    "created_at": now,
                }
            )

        if final_state.get("clinical_analysis"):
            analysis_entry = {
                "filename": final_state.get("file_meta")["filename"],
                "uploaded_at": now,
                "clinical_analysis": final_state.get("clinical_analysis", ""),
                "risk_assessment": final_state.get("risk_assessment", ""),
            }
            session_data["analysis"].append(analysis_entry)
            session_data["has_active_analysis"] = True

        session_data["conversation_history"].append(
            {
                "timestamp": now,
                "input_text_snippet": (message or "")[:200],
                "response_snippet": (final_state.get("final_response") or "")[:400],
            }
        )

        logger.info(f"Final session state:\n{json.dumps(session_data, indent=2)}")
        await session_manager.save_session(current_session_id, session_data)

        # --------------------------------------------------
        # Emit final response to client
        # --------------------------------------------------
        message_text = final_state.get("final_response") or "No response generated."

        # Remove internal fields before logging
        final_state.pop("file_bytes", None)
        final_state.pop("parsed_text", None)
        logger.info(
            "Response state from graph:\n%s",
            json.dumps(final_state, indent=2, default=str),
        )

        yield sse_event(
            {
                "type": "complete",
                "message": message_text,
                "has_active_analysis": bool(session_data["analysis"]),
            }
        )

    # Set session ID header before streaming begins
    return StreamingResponse(
        pipeline_stream(),
        media_type="text/event-stream",
        headers={
            "X-Session-ID": current_session_id,
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Critical for Nginx — disables proxy buffering
            "Connection": "keep-alive",
        },
    )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "Health Insights AI"}


def build_graph():
    """
    Build the orchestrator graph with 3 routing scenarios:
    1. Input Text only -> Input Guardrail -> Orchestrator agent -> QnA agent  → Compliance agent  -> END
    2a. File only -> Input Guardrail -> Orchestrator agent -> Document Parser service -> PII Removal service -> Clinical agent (Health/Medical Related) -> Risk agent -> Insights Summary agent -> Compliance agent -> END
    2b. File only -> Input Guardrail -> Orchestrator agent -> Document Parser service -> PII Removal service -> Clinical agent (Non-Health/Medical Related) -> QnA agent -> Compliance agent -> END
    3a. File + Input Text -> Input Guardrail -> Orchestrator agent -> Document Parser service -> PII Removal service -> Clinical agent (Health/Medical Related) -> Risk agent -> Insights Summary agent -> QnA agent -> Compliance agent -> END
    3b. File + Input Text -> Input Guardrail -> Orchestrator agent -> Document Parser service -> PII Removal service -> Clinical agent (Non-Health/Medical Related) -> QnA agent -> Compliance agent -> END
    """

    builder = StateGraph(State)

    # Add all nodes
    builder.add_node("input_guardrail", input_guardrail_node)
    builder.add_node("orchestrator", orchestrator.orchestrator_node)
    builder.add_node("document_parser", document_parser_node)
    builder.add_node("pii_removal", pii_removal_node)
    builder.add_node("clinical_analysis", clinical_analysis_node)
    builder.add_node("risk_assessment", risk_assessment_node)
    builder.add_node("insights_summary", insights_summary_node)
    builder.add_node("qna", qna_node)
    builder.add_node("compliance", compliance_node)

    # Entry point
    builder.add_edge(START, "input_guardrail")

    # ============================================
    # Conditional routing from input guardrail
    # ============================================

    def route_from_input_guardrail(state: State) -> str:
        """
        Perform checks on the input and determine next node.
        """
        next_node = state.next_node

        if next_node == "orchestrator":
            return "orchestrator"
        else:
            return "END"

    builder.add_conditional_edges(
        "input_guardrail",
        route_from_input_guardrail,
        {"orchestrator": "orchestrator", "END": END},
    )

    # ============================================
    # Conditional routing from orchestrator
    # ============================================
    def route_from_orchestrator(state: State) -> str:
        """
        Determine initial route based on input.
        Routes:
        - "doc_pipeline" -> File only OR File + Text
        - "qna" -> Text only
        """
        next_node = state.next_node

        if next_node == "doc_pipeline" or next_node == "doc_then_qna":
            return "document_parser"
        elif next_node == "qna":
            return "qna"
        else:
            # Fallback - shouldn't happen
            return "compliance"

    builder.add_conditional_edges(
        "orchestrator",
        route_from_orchestrator,
        {
            "document_parser": "document_parser",
            "qna": "qna",
            "compliance": "compliance",
        },
    )

    # ============================================
    # Conditional routing from Document Parser
    # ============================================
    def route_from_document_parser(state: State) -> str:
        """
        Determine route after document parsing.
        Routes:
        - No issue parsing document -> Go to PII Removal
        - Issue -> END with error message
        """
        next_node = state.next_node

        if next_node == "pii_removal":
            return "pii_removal"
        else:
            # Fallback - shouldn't happen
            return "compliance"

    builder.add_conditional_edges(
        "document_parser",
        route_from_document_parser,
        {"pii_removal": "pii_removal", "compliance": "compliance"},
    )

    builder.add_edge("pii_removal", "clinical_analysis")

    # ============================================
    # Conditional routing from clinical_analysis
    # ============================================
    def route_from_clinical_analysis(state: State) -> str:
        """
        Determine route after clinical analysis.
        Routes:
        - if medical related -> route to risk_assessment
        - if not medical related + No input text -> route to compliance (skip risk assessment)
        - if not medical related + Has input text -> route to QnA (skip risk assessment)
        """
        next_node = state.next_node

        if next_node == "risk_assessment":
            return "risk_assessment"
        elif next_node == "compliance":
            return "compliance"
        elif next_node == "qna":
            return "qna"
        else:
            # Fallback - shouldn't happen
            return "compliance"

    builder.add_conditional_edges(
        "clinical_analysis",
        route_from_clinical_analysis,
        {
            "risk_assessment": "risk_assessment",
            "compliance": "compliance",
            "qna": "qna",
        },
    )

    # ============================================
    # Conditional routing from Insight Summary
    # Check if we need QnA agent to answer user question based on analysis, or if we can skip straight to compliance.
    # ============================================
    def route_after_insights(state: State) -> str:
        """
        After document analysis:
        - If user asked a question (file + text) → Go to QnA
        - If file only → Go straight to compliance
        """
        next_node = state.next_node

        # If user uploaded file + asked a question
        if next_node == "qna":
            return "qna"
        else:
            # File only - go straight to compliance
            return "compliance"

    builder.add_conditional_edges(
        "insights_summary",
        route_after_insights,
        {"qna": "qna", "compliance": "compliance"},
    )

    # ============================================
    # Risk Assessment always goes to Insights Summary
    # ============================================
    builder.add_edge("risk_assessment", "insights_summary")

    # ============================================
    # QnA always goes to compliance
    # ============================================
    builder.add_edge("qna", "compliance")

    # ============================================
    # Compliance is the final node before END
    # ============================================
    builder.add_edge("compliance", END)

    return builder.compile()
