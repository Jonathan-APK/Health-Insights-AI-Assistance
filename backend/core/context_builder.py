def build_context(state) -> str:
    """
    Build structured context for LLM classification.
    Clear formatting helps LLM understand conversation flow and clinical context.
    """
    
    context_parts = []
    
    # 1. Past conversation with turn numbers and clear role distinction
    conversation = state.conversation_history
    if conversation:
        recent = conversation[-5:]
        conv_text = []
        for i, msg in enumerate(recent, 1):
            conv_text.append(f"  Turn {i}:")
            conv_text.append(f"    User: {msg['input_text_snippet']}")
            conv_text.append(f"    Assistant: {msg['response_snippet']}")
        context_parts.append("CONVERSATION HISTORY:\n" + "\n".join(conv_text))
    
    # 2. Past analysis with structured sections
    analysis = state.analysis
    if analysis:
        latest = analysis[-1]
        analysis_lines = [
            f"PREVIOUS DOCUMENT ANALYSIS: {latest['filename']}",
            f"  • Clinical Findings: {latest['clinical_analysis']}",
            f"  • Risk Flags: {', '.join(latest['risk_assessment']) if latest['risk_assessment'] else 'None'}"
        ]
        context_parts.append("\n".join(analysis_lines))
    
    # 4. Current message (highlighted)
    if state.input_text:
        context_parts.append(f"NEW MESSAGE FROM USER:\n  \"{state.input_text}\"")
    
    if not context_parts:
        return []
    else:
        return "\n\n".join(context_parts)