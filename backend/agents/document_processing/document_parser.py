# backend/agents/document_processing/document_parser.py

import pymupdf4llm
import pymupdf
import logging
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger("document_parser")

def now():
    return datetime.now(ZoneInfo("Asia/Singapore")).isoformat()

def document_parser_node(state):
    """
    Parse PDF
    """
    
    print("=" * 50)
    print("DOCUMENT PARSER NODE")
    print("=" * 50)
    
    file_bytes = state.file_bytes
    filename = state.file_meta.get("filename", "unknown.pdf") if state.file_meta else "unknown.pdf"
    
    if not file_bytes:
        logger.error("No file bytes")
        return {
            "next_node": "end",
            "final_response": "Error: No file content",
            "last_updated": now()
        }
    
    try:
        # Parse PDF
        logger.info(f"Parsing: {filename}")
        pdf_stream = BytesIO(file_bytes)
        doc = pymupdf.open(stream=pdf_stream, filetype="pdf")
        markdown_text = pymupdf4llm.to_markdown(doc)
        logger.info(f"Extracted: {len(markdown_text)} chars")
                
        # Route to PII Removal Agent
        logger.info(f"Parsed Content: {markdown_text}")
        logger.info("Parsed document, routing to PII removal")
        logger.info("=" * 50 + "\n")
           
        return {
            "parsed_text": markdown_text,
            "next_node": "pii_removal",
            "last_updated": now()
        }
        
    except Exception as e:
        msg = str(e)
        short_msg = msg[:100] if len(msg) > 100 else msg
        logger.error(f"Error Encountered: {short_msg}")
        logger.info("=" * 50 + "\n")
        return {
            "next_node": "end",
            "final_response": f"An error occurred while processing the document: {str(e)}",
            "last_updated": now()
        }