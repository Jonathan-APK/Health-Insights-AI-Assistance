import pytest
from unittest.mock import patch
from agents.document_processing.agent.risk_assessment import risk_assessment_node


class DummyState:
    def __init__(self, parsed_text):
        self.parsed_text = parsed_text
        self.session_id = "test-session"


def _mock_llm_response(content: str):
    return type(
        "obj",
        (),
        {
            "content": content,
            "response_metadata": {
                "token_usage": {"prompt_tokens": 1, "completion_tokens": 1},
                "model_name": "gpt-4o-mini",
            },
        },
    )()


def test_risk_assessment_node_success():
    """Test successful risk assessment generation."""
    with patch("agents.document_processing.agent.risk_assessment.ChatOpenAI") as mock_chatopenai:
        mock_instance = mock_chatopenai.return_value
        mock_instance.invoke.return_value = _mock_llm_response("HIGH RISK: Hypertension")

        state = DummyState("Medical record text")
        result = risk_assessment_node(state)

        assert result["next_node"] == "insights_summary"
        assert "risk_assessment" in result
        assert "HIGH RISK" in result["risk_assessment"]
        assert "last_updated" in result


def test_risk_assessment_node_low_risk():
    """Test risk assessment with low risk output."""
    with patch("agents.document_processing.agent.risk_assessment.ChatOpenAI") as mock_chatopenai:
        mock_instance = mock_chatopenai.return_value
        mock_instance.invoke.return_value = _mock_llm_response("LOW RISK: Generally healthy")

        state = DummyState("Medical record text")
        result = risk_assessment_node(state)

        assert result["next_node"] == "insights_summary"
        assert "LOW RISK" in result["risk_assessment"]


def test_risk_assessment_node_error():
    """Test error handling in risk assessment."""
    with patch("agents.document_processing.agent.risk_assessment.ChatOpenAI") as mock_chatopenai:
        mock_chatopenai.return_value.invoke.side_effect = Exception("LLM error")

        state = DummyState("Medical record text")
        result = risk_assessment_node(state)

        assert result["next_node"] == "end"
        assert "error" in result["final_response"].lower()


def test_risk_assessment_node_moderate_risk():
    """Test risk assessment with moderate risk output."""
    with patch("agents.document_processing.agent.risk_assessment.ChatOpenAI") as mock_chatopenai:
        mock_instance = mock_chatopenai.return_value
        mock_instance.invoke.return_value = _mock_llm_response("MODERATE RISK: Pre-diabetes condition")

        state = DummyState("Medical record text")
        result = risk_assessment_node(state)

        assert result["next_node"] == "insights_summary"
        assert "MODERATE RISK" in result["risk_assessment"]


def test_risk_assessment_node_routes_to_summary():
    """Test risk assessment always routes to insights summary on success."""
    with patch("agents.document_processing.agent.risk_assessment.ChatOpenAI") as mock_chatopenai:
        mock_instance = mock_chatopenai.return_value
        mock_instance.invoke.return_value = _mock_llm_response("CRITICAL RISK: Urgent intervention needed")

        state = DummyState("Medical record text")
        result = risk_assessment_node(state)

        assert result["next_node"] == "insights_summary"
        assert "last_updated" in result
