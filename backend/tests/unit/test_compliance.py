import pytest
from unittest.mock import patch
from agents.compliance.compliance import compliance_node

class DummyState:
    def __init__(self, text):
        self.final_response = None
        self.pre_compliance_response = text

@pytest.mark.parametrize("mock_output,expected_verdict", [
    ('{"verdict":"pass","final_response":"Safe"}', "pass"),
    ('{"verdict":"block","final_response":"Unsafe"}', "block"),
])
def test_compliance_node_unit(mock_output, expected_verdict):
    # Patch the ChatOpenAI class so no API key is needed
    with patch("agents.compliance.compliance.ChatOpenAI") as mock_chatopenai:
        mock_instance = mock_chatopenai.return_value
        mock_instance.invoke.return_value = type("obj", (), {"content": mock_output})()

        state = DummyState("Sample input")
        result = compliance_node(state)

        assert result["compliance_response"]["verdict"] == expected_verdict
        assert "final_response" in result


def test_compliance_node_early_return():
    """Test compliance node skips check when final_response already exists."""
    class StateWithResponse:
        def __init__(self):
            self.final_response = "Already set"
            self.pre_compliance_response = "Input text"

    state = StateWithResponse()
    result = compliance_node(state)

    assert result["next_node"] == "END"
    assert "last_updated" in result


def test_compliance_node_json_decode_error():
    """Test compliance node handles malformed JSON response."""
    with patch("agents.compliance.compliance.ChatOpenAI") as mock_chatopenai:
        mock_instance = mock_chatopenai.return_value
        mock_instance.invoke.return_value = type("obj", (), {"content": "Invalid JSON {broken"})()

        state = DummyState("Sample input")
        result = compliance_node(state)

        assert result["compliance_response"]["verdict"] == "block"
        assert "malformed" in str(result["compliance_response"]["reasons"]).lower()


def test_compliance_node_block_safety_net():
    """Test compliance node applies safety net when block verdict lacks final_response."""
    with patch("agents.compliance.compliance.ChatOpenAI") as mock_chatopenai:
        mock_instance = mock_chatopenai.return_value
        mock_instance.invoke.return_value = type("obj", (), {"content": '{"verdict":"block"}'})()

        state = DummyState("Sample input")
        result = compliance_node(state)

        assert result["compliance_response"]["verdict"] == "block"
        assert "blocked" in result["final_response"].lower()
