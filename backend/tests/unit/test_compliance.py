import pytest
from unittest.mock import patch
from agents.compliance.compliance import compliance_node

class DummyState:
    def __init__(self, text):
        self.final_response = None
        self.pre_compliance_response = text
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

@pytest.mark.parametrize("mock_output,expected_verdict", [
    ('{"verdict":"pass","final_response":"Safe"}', "pass"),
    ('{"verdict":"block","final_response":"Unsafe"}', "block"),
])
def test_compliance_node_unit(mock_output, expected_verdict):
    # Patch the ChatOpenAI class so no API key is needed
    with patch("agents.compliance.compliance.ChatOpenAI") as mock_chatopenai:
        mock_instance = mock_chatopenai.return_value
        mock_instance.invoke.return_value = _mock_llm_response(mock_output)

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
        mock_instance.invoke.return_value = _mock_llm_response("Invalid JSON {broken")

        state = DummyState("Sample input")
        result = compliance_node(state)

        assert result["compliance_response"]["verdict"] == "block"
        assert "malformed" in str(result["compliance_response"]["reasons"]).lower()


def test_compliance_node_block_safety_net():
    """Test compliance node applies safety net when block verdict lacks final_response."""
    with patch("agents.compliance.compliance.ChatOpenAI") as mock_chatopenai:
        mock_instance = mock_chatopenai.return_value
        mock_instance.invoke.return_value = _mock_llm_response('{"verdict":"block"}')

        state = DummyState("Sample input")
        result = compliance_node(state)

        assert result["compliance_response"]["verdict"] == "block"
        assert "blocked" in result["final_response"].lower()


def test_compliance_node_allows_informational_result_interpretation_with_disclaimer():
    """Normal report interpretation should not be blocked just for containing lab values."""
    with patch("agents.compliance.compliance.ChatOpenAI") as mock_chatopenai:
        mock_instance = mock_chatopenai.return_value
        mock_instance.invoke.return_value = _mock_llm_response(
            '{'
            '"verdict":"block",'
            '"reasons":["Contains specific health measurements and potential health risks."],'
            '"disclaimer_injected":false,'
            '"sanitized_output":null,'
            '"final_response":"This output has been blocked due to compliance violations. Please ask another question."'
            '}'
        )

        state = DummyState(
            "Your report indicates several important health measurements that suggest potential health risks. "
            "BMI is 29.7 kg/m2. Blood pressure is 142/90 mmHg. Total cholesterol is 240 mg/dL. "
            "Fasting glucose is 115 mg/dL and HbA1c is 6.1%. It is important to discuss these results "
            "with a healthcare provider for further evaluation."
        )
        result = compliance_node(state)

        assert result["compliance_response"]["verdict"] == "pass"
        assert "Disclaimer:" in result["final_response"]
        assert "healthcare provider" in result["final_response"]


def test_compliance_node_unjustified_block_is_downgraded_to_pass():
    """A block without any clear unsafe signal should be treated as false positive."""
    with patch("agents.compliance.compliance.ChatOpenAI") as mock_chatopenai:
        mock_instance = mock_chatopenai.return_value
        mock_instance.invoke.return_value = _mock_llm_response(
            '{'
            '"verdict":"block",'
            '"reasons":["Potentially sensitive medical interpretation."],'
            '"disclaimer_injected":false,'
            '"sanitized_output":null,'
            '"final_response":"This output has been blocked due to compliance violations. Please ask another question."'
            '}'
        )

        state = DummyState(
            "Your report shows elevated blood pressure and cholesterol. "
            "These findings may increase cardiovascular risk and should be discussed with a healthcare professional."
        )
        result = compliance_node(state)

        assert result["compliance_response"]["verdict"] == "pass"
        assert "Disclaimer:" in result["final_response"]


def test_compliance_node_keeps_block_for_explicit_pii_reason():
    """Explicit high-risk reasons like PII leakage must remain blocked."""
    with patch("agents.compliance.compliance.ChatOpenAI") as mock_chatopenai:
        mock_instance = mock_chatopenai.return_value
        mock_instance.invoke.return_value = _mock_llm_response(
            '{'
            '"verdict":"block",'
            '"reasons":["Contains PII including full name and phone number."],'
            '"disclaimer_injected":false,'
            '"sanitized_output":null,'
            '"final_response":"This output has been blocked due to compliance violations. Please ask another question."'
            '}'
        )

        state = DummyState(
            "Patient John Doe can be reached at +65 9123 4567 for follow-up."
        )
        result = compliance_node(state)

        assert result["compliance_response"]["verdict"] == "block"
        assert "blocked" in result["final_response"].lower()
