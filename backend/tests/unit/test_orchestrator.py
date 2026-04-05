import pytest
from unittest.mock import patch
from agents.orchestrator.orchestrator import orchestrator_node


class DummyFile:
    def __init__(self, filename="test.pdf"):
        self.filename = filename


class DummyState:
    def __init__(self, input_text=None, file_meta=None):
        self.input_text = input_text
        self.file_meta = file_meta
        self.context_history = []
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
    "llm_output,input_text,file_meta,expected_next_node",
    [
        ("MEDICAL", "What is diabetes?", None, "qna"),
        ("OFF_TOPIC", "Hello there", None, "compliance"),
    ],
)
def test_orchestrator_text_only_routing(llm_output, input_text, file_meta, expected_next_node):
    """Test orchestrator routing logic for text input."""
    with patch("agents.orchestrator.orchestrator.ChatOpenAI") as mock_chatopenai, \
         patch("agents.orchestrator.orchestrator.build_context"):

        mock_instance = mock_chatopenai.return_value
        mock_instance.invoke.return_value = _mock_llm_response(llm_output)

        state = DummyState(input_text, file_meta)
        result = orchestrator_node(state)

        assert result["next_node"] == expected_next_node
        assert "last_updated" in result


def test_orchestrator_text_only_medical():
    """Test orchestrator routes medical text to QnA."""
    with patch("agents.orchestrator.orchestrator.ChatOpenAI") as mock_chatopenai, \
         patch("agents.orchestrator.orchestrator.build_context"):

        mock_instance = mock_chatopenai.return_value
        mock_instance.invoke.return_value = _mock_llm_response("MEDICAL")

        state = DummyState(input_text="What are symptoms of hypertension?")
        result = orchestrator_node(state)

        assert result["next_node"] == "qna"


def test_orchestrator_text_only_off_topic():
    """Test orchestrator handles off-topic text with response generation."""
    with patch("agents.orchestrator.orchestrator.ChatOpenAI") as mock_chatopenai, \
         patch("agents.orchestrator.orchestrator.build_context"), \
         patch("agents.orchestrator.orchestrator.load_prompt_config") as mock_load:

        # First call returns OFF_TOPIC classification
        # Second call returns off-topic response
        mock_instance = mock_chatopenai.return_value
        mock_instance.invoke.side_effect = [
            _mock_llm_response("OFF_TOPIC"),
            _mock_llm_response("I can only answer health-related questions"),
        ]

        mock_load.return_value = {
            "system": "You are helpful",
            "model": "gpt-4",
            "temperature": 0.7,
        }

        state = DummyState(input_text="Tell me a joke")
        result = orchestrator_node(state)

        assert result["next_node"] == "compliance"
        assert "pre_compliance_response" in result


def test_orchestrator_file_only():
    """Test orchestrator routes file-only upload to document parser."""
    state = DummyState(input_text=None, file_meta={"filename": "medical_record.pdf"})
    result = orchestrator_node(state)

    assert result["next_node"] == "doc_pipeline"


def test_orchestrator_file_and_text():
    """Test orchestrator handles both file and text."""
    state = DummyState(
        input_text="Analyze this document",
        file_meta={"filename": "record.pdf"}
    )
    result = orchestrator_node(state)

    assert result["next_node"] == "doc_then_qna"


def test_orchestrator_no_input():
    """Test orchestrator handles no input case."""
    state = DummyState(input_text=None, file_meta=None)
    result = orchestrator_node(state)

    # Fallback when no input or file is provided
    assert result["next_node"] == "compliance"

