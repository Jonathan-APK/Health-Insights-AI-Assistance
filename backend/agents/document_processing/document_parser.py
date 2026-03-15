import logging
from datetime import datetime
from io import BytesIO
from zoneinfo import ZoneInfo

import pymupdf
import pymupdf4llm

logger = logging.getLogger("document_parser")


def now():
    return datetime.now(ZoneInfo("Asia/Singapore")).isoformat()


def document_parser_node(state):
    """
    Parse PDF
    """

    file_bytes = state.file_bytes
    filename = (
        state.file_meta.get("filename", "unknown.pdf")
        if state.file_meta
        else "unknown.pdf"
    )

    if not file_bytes:
        logger.error("No file bytes")
        return {
            "next_node": "end",
            "final_response": "Error: No file content",
            "last_updated": now(),
            "file_bytes": None,  # clear file bytes after parsing
        }

    try:
        # Parse PDF
        logger.info(f"Parsing: {filename}")
        pdf_stream = BytesIO(file_bytes)
        doc = pymupdf.open(stream=pdf_stream, filetype="pdf")
        markdown_text = pymupdf4llm.to_markdown(doc)
        safe_text = f"<UNTRUSTED_DATA>\n{markdown_text}\n</UNTRUSTED_DATA>"
        logger.info(f"Extracted: {len(safe_text)} chars")

        # Route to PII Removal Agent
        logger.info("Parsed document, routing to PII removal")

        return {
            "parsed_text": safe_text,
            "next_node": "pii_removal",
            "last_updated": now(),
            "file_bytes": None,  # clear file bytes after parsing
        }

    except Exception as e:
        msg = str(e)
        short_msg = msg[:100] if len(msg) > 100 else msg
        logger.error(f"Error Encountered: {short_msg}")
        return {
            "next_node": "compliance",
            "final_response": "An error has occurred. Please try again later.",
            "last_updated": now(),
            "file_bytes": None,  # clear file bytes after parsing
        }
