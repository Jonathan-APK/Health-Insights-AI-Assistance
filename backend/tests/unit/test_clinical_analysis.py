import pytest
from unittest.mock import patch
from agents.document_processing.agent.clinical_analysis import clinical_analysis_node


class DummyState:
    def __init__(self, sanitized_text, input_text=None):
        self.sanitized_text = sanitized_text
        self.input_text = input_text
        self.session_id = "test-session"


@pytest.mark.parametrize(
    "llm_output,input_text,expected_next_node",
    [
        ("MEDICAL ANALYSIS CONTENT", "Follow-up question", "risk_assessment"),
        ("OFF_TOPIC", "Follow-up question", "qna"),
        ("OFF_TOPIC", "", "compliance"),
        ("OFF_TOPIC", None, "compliance"),
        ("ANALYSIS OF HEALTH RECORDS", None, "risk_assessment"),
    ],
)
def test_clinical_analysis_node_unit(llm_output, input_text, expected_next_node):
    """Test clinical analysis node with various outputs."""
    with patch("agents.document_processing.agent.clinical_analysis.ChatOpenAI") as mock_chatopenai:
        mock_instance = mock_chatopenai.return_value
        mock_instance.invoke.return_value = type(
            "obj",
            (),
            {
                "content": llm_output,
                "response_metadata": {
                    "token_usage": {"prompt_tokens": 1, "completion_tokens": 1},
                    "model_name": "gpt-4o-mini",
                },
            },
        )()

        state = DummyState("Sanitized medical text", input_text)
        result = clinical_analysis_node(state)

        assert result["next_node"] == expected_next_node
        assert "clinical_analysis" in result
        assert "last_updated" in result
        assert result["sanitized_text"] is None  # Should be cleared


def test_clinical_analysis_node_error():
    """Test error handling in clinical analysis."""
    with patch("agents.document_processing.agent.clinical_analysis.ChatOpenAI") as mock_chatopenai:
        mock_chatopenai.return_value.invoke.side_effect = Exception("LLM error")

        state = DummyState("Some text")
        result = clinical_analysis_node(state)

        assert result["next_node"] == "end"
        assert "error" in result["final_response"].lower()
        assert result["sanitized_text"] is None
