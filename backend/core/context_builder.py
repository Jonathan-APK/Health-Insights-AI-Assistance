def build_context(state) -> str:
    """
    Build structured context for LLM using past conversation history, analysis, and current input.
    """
    context_parts = []
    
    # 1. Past conversation with turn numbers and clear role distinction
    conversation = getattr(state, "conversation_history", None)
    if conversation:
        recent = conversation[-5:]
        conv_text = []
        for i, msg in enumerate(recent, 1):
            conv_text.append(f"  Turn {i}:")
            conv_text.append(f"    User: {msg.get('input_text_snippet', '')}")
            conv_text.append(f"    Assistant: {msg.get('response_snippet', '')}")
        context_parts.append("CONVERSATION HISTORY:\n" + "\n".join(conv_text))
    
    # 2. Past analysis with structured sections
    analysis = getattr(state, "analysis", None)
    if analysis:
        latest = analysis[-1]
        analysis_lines = [
            f"PREVIOUS DOCUMENT ANALYSIS: {latest.get('filename', '')}",
            f"  • Clinical Findings: {latest.get('clinical_analysis', '')}",
            f"  • Risk Flags: {', '.join(latest.get('risk_assessment', [])) if latest.get('risk_assessment') else 'None'}"
        ]
        context_parts.append("\n".join(analysis_lines))
    
    # 3. Current message (highlighted)
    if getattr(state, "input_text", None):
        context_parts.append(f"NEW MESSAGE FROM USER:\n  \"{state.input_text}\"")
    
    return "\n\n".join(context_parts) if context_parts else ""
