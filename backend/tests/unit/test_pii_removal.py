import pytest
from unittest.mock import patch, MagicMock
from agents.document_processing.pii_removal import pii_removal_node


class DummyState:
    def __init__(self, parsed_text):
        self.parsed_text = parsed_text


def test_pii_removal_node_success():
    """Test successful PII removal from parsed text."""
    with patch("agents.document_processing.pii_removal.analyzer") as mock_analyzer, \
         patch("agents.document_processing.pii_removal.anonymizer") as mock_anonymizer:

        # Mock analyzer results (simulating detected PII)
        mock_result = MagicMock()
        mock_result.start = 0
        mock_result.end = 4
        mock_result.entity_type = "PERSON"
        mock_analyzer.analyze.return_value = [mock_result]

        # Mock anonymizer
        mock_anonymized = MagicMock()
        mock_anonymized.text = "Anonymous text with [PERSON_1] redacted"
        mock_anonymizer.anonymize.return_value = mock_anonymized

        state = DummyState("<UNTRUSTED_DATA>\nJohn Smith works here\n</UNTRUSTED_DATA>")
        result = pii_removal_node(state)

        assert result["next_node"] == "clinical_analysis"
        assert "[PERSON_1]" in result["sanitized_text"]
        assert "last_updated" in result


def test_pii_removal_node_no_pii():
    """Test PII removal when no PII is detected."""
    with patch("agents.document_processing.pii_removal.analyzer") as mock_analyzer, \
         patch("agents.document_processing.pii_removal.anonymizer") as mock_anonymizer:

        mock_analyzer.analyze.return_value = []

        mock_anonymized = MagicMock()
        mock_anonymized.text = "Text with no PII"
        mock_anonymizer.anonymize.return_value = mock_anonymized

        state = DummyState("<UNTRUSTED_DATA>\nSafe medical information\n</UNTRUSTED_DATA>")
        result = pii_removal_node(state)

        assert result["next_node"] == "clinical_analysis"
        assert "last_updated" in result


def test_pii_removal_node_error():
    """Test error handling in PII removal."""
    with patch("agents.document_processing.pii_removal.analyzer") as mock_analyzer:
        mock_analyzer.analyze.side_effect = Exception("Analyzer error")

        state = DummyState("Some text")
        result = pii_removal_node(state)

        assert result["next_node"] == "compliance"
        assert "error" in result["final_response"].lower()


def test_pii_removal_node_nric():
    """Test PII removal detects and redacts Singapore NRIC/FIN."""
    with patch("agents.document_processing.pii_removal.analyzer") as mock_analyzer, \
         patch("agents.document_processing.pii_removal.anonymizer") as mock_anonymizer:

        # Mock NRIC detection (e.g., S1234567A)
        mock_result = MagicMock()
        mock_result.start = 30
        mock_result.end = 38
        mock_result.entity_type = "NRIC_FIN"
        mock_analyzer.analyze.return_value = [mock_result]

        mock_anonymized = MagicMock()
        mock_anonymized.text = "Patient ID: [NRIC_FIN_1] is registered"
        mock_anonymizer.anonymize.return_value = mock_anonymized

        state = DummyState("<UNTRUSTED_DATA>\nPatient NRIC: S1234567A medical record\n</UNTRUSTED_DATA>")
        result = pii_removal_node(state)

        assert result["next_node"] == "clinical_analysis"
        assert "[NRIC_FIN_1]" in result["sanitized_text"]


def test_pii_removal_node_email():
    """Test PII removal detects and redacts email addresses."""
    with patch("agents.document_processing.pii_removal.analyzer") as mock_analyzer, \
         patch("agents.document_processing.pii_removal.anonymizer") as mock_anonymizer:

        # Mock email detection
        mock_result = MagicMock()
        mock_result.start = 15
        mock_result.end = 35
        mock_result.entity_type = "EMAIL_ADDRESS"
        mock_analyzer.analyze.return_value = [mock_result]

        mock_anonymized = MagicMock()
        mock_anonymized.text = "Contact: [EMAIL_ADDRESS_1] for follow-up"
        mock_anonymizer.anonymize.return_value = mock_anonymized

        state = DummyState("<UNTRUSTED_DATA>\nContact: john.doe@hospital.com for follow-up\n</UNTRUSTED_DATA>")
        result = pii_removal_node(state)

        assert result["next_node"] == "clinical_analysis"
        assert "[EMAIL_ADDRESS_1]" in result["sanitized_text"]


def test_pii_removal_node_address():
    """Test PII removal detects and redacts location/address information."""
    with patch("agents.document_processing.pii_removal.analyzer") as mock_analyzer, \
         patch("agents.document_processing.pii_removal.anonymizer") as mock_anonymizer:

        # Mock location/address detection
        mock_result = MagicMock()
        mock_result.start = 20
        mock_result.end = 45
        mock_result.entity_type = "LOCATION"
        mock_analyzer.analyze.return_value = [mock_result]

        mock_anonymized = MagicMock()
        mock_anonymized.text = "Address: [LOCATION_1] clinic"
        mock_anonymizer.anonymize.return_value = mock_anonymized

        state = DummyState("<UNTRUSTED_DATA>\nAddress: 123 Medical Plaza, Singapore clinic\n</UNTRUSTED_DATA>")
        result = pii_removal_node(state)

        assert result["next_node"] == "clinical_analysis"
        assert "[LOCATION_1]" in result["sanitized_text"]


def test_pii_removal_node_phone():
    """Test PII removal detects and redacts phone numbers."""
    with patch("agents.document_processing.pii_removal.analyzer") as mock_analyzer, \
         patch("agents.document_processing.pii_removal.anonymizer") as mock_anonymizer:

        # Mock phone number detection
        mock_result = MagicMock()
        mock_result.start = 15
        mock_result.end = 28
        mock_result.entity_type = "PHONE_NUMBER"
        mock_analyzer.analyze.return_value = [mock_result]

        mock_anonymized = MagicMock()
        mock_anonymized.text = "Contact: [PHONE_NUMBER_1] for appointments"
        mock_anonymizer.anonymize.return_value = mock_anonymized

        state = DummyState("<UNTRUSTED_DATA>\nContact: +65-6123-4567 for appointments\n</UNTRUSTED_DATA>")
        result = pii_removal_node(state)

        assert result["next_node"] == "clinical_analysis"
        assert "[PHONE_NUMBER_1]" in result["sanitized_text"]
