import pytest
from unittest.mock import patch
from agents.document_processing.agent.insights_summary import insights_summary_node


class DummyState:
    def __init__(self, clinical_analysis, risk_assessment, input_text=None):
        self.clinical_analysis = clinical_analysis
        self.risk_assessment = risk_assessment
        self.input_text = input_text
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


@pytest.mark.parametrize(
    "input_text,expected_next_node",
    [
        ("Follow-up question", "qna"),
        ("", "compliance"),
        (None, "compliance"),
    ],
)
def test_insights_summary_node_unit(input_text, expected_next_node):
    """Test insights summary node routing based on input."""
    with patch("agents.document_processing.agent.insights_summary.ChatOpenAI") as mock_chatopenai:
        mock_instance = mock_chatopenai.return_value
        mock_instance.invoke.return_value = _mock_llm_response("Summary of health insights")

        state = DummyState("Medical analysis", "Risk assessment data", input_text)
        result = insights_summary_node(state)

        assert result["next_node"] == expected_next_node
        assert "insights_summary" in result
        assert "last_updated" in result


def test_insights_summary_node_combines_inputs():
    """Test that insights summary combines clinical and risk assessment."""
    with patch("agents.document_processing.agent.insights_summary.ChatOpenAI") as mock_chatopenai:
        mock_instance = mock_chatopenai.return_value
        mock_instance.invoke.return_value = _mock_llm_response("Combined insights")

        state = DummyState("Clinical findings", "Risk findings", "user query")
        insights_summary_node(state)

        # Verify that invoke was called with combined content
        call_args = mock_instance.invoke.call_args
        assert "Clinical findings" in str(call_args)
        assert "Risk findings" in str(call_args)


def test_insights_summary_node_error():
    """Test error handling in insights summary."""
    with patch("agents.document_processing.agent.insights_summary.ChatOpenAI") as mock_chatopenai:
        mock_chatopenai.return_value.invoke.side_effect = Exception("LLM error")

        state = DummyState("Analysis", "Risk", "query")
        result = insights_summary_node(state)

        assert result["next_node"] == "end"
        assert "error" in result["final_response"].lower()
