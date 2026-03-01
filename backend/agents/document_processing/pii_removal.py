import logging
from datetime import datetime
from multiprocessing import context
from zoneinfo import ZoneInfo
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

logger = logging.getLogger("document_parser")

# Initialize analyzer and anonymizer
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# --- Custom recognizers ---
# Singapore NRIC/FIN (regex for S1234567A or F1234567B)
nric_pattern = Pattern(name="NRIC/FIN", regex=r"\b[STFG]\d{7}[A-Z]\b", score=0.8)
nric_recognizer = PatternRecognizer(supported_entity="NRIC_FIN", patterns=[nric_pattern])
analyzer.registry.add_recognizer(nric_recognizer)

def now():
    return datetime.now(ZoneInfo("Asia/Singapore")).isoformat()

def pii_removal_node(state):
    """
    Remove PII from parsed text
    """
    
    print("=" * 50)
    print("PII REMOVAL NODE")
    print("=" * 50)
    
    try:
        text_input = state.parsed_text

        # Restrict analyzer to only the PHI entities we care about
        target_entities = [
            "PERSON",          # names
            "PHONE_NUMBER",    # phone
            "EMAIL_ADDRESS",   # email
            "LOCATION",        # address
            "NRIC_FIN"         # custom
        ]

        config_operators = {}

        # call presidio analyzer to detect PII >> returns a list of objects 
        results = analyzer.analyze(
            text=text_input,
            language="en",
            entities=target_entities
        )

        # initialize new and empty PII-Value mapping and count the number of PIIs 
        pii_map = {}
        counter = 1

        for result in results:
            value = text_input[result.start:result.end]
            entity_type = result.entity_type

            # Avoid assigning a new placeholder if the same raw value appears twice
            if value not in pii_map:
                pii_map[value] = f"[{entity_type}_{counter}]"
                counter += 1

        # Build one custom operator per entity type.
        # The lambda looks up each individual value in pii_map so that
        # different names of the same entity type get different placeholders.
        snapshot = dict(pii_map)  # stable capture for the lambda

        def make_replacer(lookup: dict):
            def replacer(text: str) -> str:
                return lookup.get(text, text)
            return replacer

        config_operators = {
            entity: OperatorConfig("custom", {"lambda": make_replacer(snapshot)})
            for entity in {r.entity_type for r in results}
        }

        # running the presidio anonymizer once all operators are configured
        anonymized_result = anonymizer.anonymize(
            text=text_input,
            analyzer_results=results,
            operators=config_operators
        )

        # anonymizer returns an AnonymizedResult object; extract the text field
        sanitized = anonymized_result.text if hasattr(anonymized_result, "text") else str(anonymized_result)
        
        logger.info(f"Sanitized Content: {sanitized[:200]}...")  # Log first 200 chars of sanitized text

        return {
            "sanitized_text": sanitized,
            "next_node": "clinical_analysis",
            "last_updated": now()
        }
        
    except Exception as e:
        msg = str(e)
        short_msg = msg[:100] if len(msg) > 100 else msg
        logger.error(f"Error Encountered: {short_msg}")
        print("=" * 50 + "\n")
        return {
            "sanitized_text": "An error occurred while processing the document.",
            "next_node": "compliance",
            "final_response": f"An error has occurred. Please try again later.",
            "last_updated": now()
        }