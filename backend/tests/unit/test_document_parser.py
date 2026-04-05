import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
from agents.document_processing.document_parser import document_parser_node


class DummyState:
    def __init__(self, file_bytes, file_meta=None):
        self.file_bytes = file_bytes
        self.file_meta = file_meta or {}
        self.session_id = "test-session"


@pytest.mark.parametrize(
    "file_bytes,file_meta,expected_next_node",
    [
        (b"PDF content here", {"filename": "test.pdf"}, "pii_removal"),
        (b"Another PDF", {"filename": "document.pdf", "size": 100}, "pii_removal"),
        (None, {}, "end"),
        (b"", {}, "end"),
    ],
)
def test_document_parser_node_unit(file_bytes, file_meta, expected_next_node):
    """Test document parser node with various inputs."""
    with patch("agents.document_processing.document_parser.pymupdf") as mock_pymupdf, \
         patch("agents.document_processing.document_parser.pymupdf4llm") as mock_pymupdf4llm:

        if file_bytes:
            # Mock successful PDF parsing
            mock_doc = MagicMock()
            mock_pymupdf.open.return_value = mock_doc
            mock_pymupdf4llm.to_markdown.return_value = "Parsed markdown content"

        state = DummyState(file_bytes, file_meta)
        result = document_parser_node(state)

        assert result["next_node"] == expected_next_node
        assert result["file_bytes"] is None  # file_bytes should be cleared
        assert "last_updated" in result


def test_document_parser_node_parsing_error():
    """Test document parser node error handling."""
    with patch("agents.document_processing.document_parser.pymupdf") as mock_pymupdf:
        mock_pymupdf.open.side_effect = Exception("PDF parsing error")

        state = DummyState(b"Invalid PDF", {"filename": "bad.pdf"})
        result = document_parser_node(state)

        assert result["next_node"] == "compliance"
        assert "error" in result["final_response"].lower()
        assert result["file_bytes"] is None


def test_document_parser_node_large_file():
    """Test document parser handles large files successfully."""
    with patch("agents.document_processing.document_parser.pymupdf") as mock_pymupdf, \
         patch("agents.document_processing.document_parser.pymupdf4llm") as mock_pymupdf4llm:

        mock_doc = MagicMock()
        mock_pymupdf.open.return_value = mock_doc
        large_content = "Parsed content " * 1000  # Simulate large document
        mock_pymupdf4llm.to_markdown.return_value = large_content

        state = DummyState(b"Large PDF content", {"filename": "large_file.pdf", "size": 5000000})
        result = document_parser_node(state)

        assert result["next_node"] == "pii_removal"
        assert len(result["parsed_text"]) > 1000
        assert "<UNTRUSTED_DATA>" in result["parsed_text"]


def test_document_parser_node_preserves_untrusted_data_wrapper():
    """Test document parser wraps content with UNTRUSTED_DATA tags."""
    with patch("agents.document_processing.document_parser.pymupdf") as mock_pymupdf, \
         patch("agents.document_processing.document_parser.pymupdf4llm") as mock_pymupdf4llm:

        mock_doc = MagicMock()
        mock_pymupdf.open.return_value = mock_doc
        mock_pymupdf4llm.to_markdown.return_value = "Medical information"

        state = DummyState(b"PDF", {"filename": "test.pdf"})
        result = document_parser_node(state)

        assert "<UNTRUSTED_DATA>" in result["parsed_text"]
        assert "</UNTRUSTED_DATA>" in result["parsed_text"]
        assert "Medical information" in result["parsed_text"]
