# Compute relavance by counting overlapped keywords between the query and text
def filter_relevant_context(chunks, query, top_k=3, min_score=1):
    scored_chunks = []

    for chunk in chunks:
        relevance_score = keyword_overlap_score(chunk, query)
        if relevance_score >= min_score:
            scored_chunks.append((relevance_score, chunk))

    scored_chunks.sort(reverse=True, key=lambda x: x[0])

    return [chunk for _, chunk in scored_chunks[:top_k]]


# Select the Top-K most relevant chunks based on keyword overlap with the query
def keyword_overlap_score(text, query):
    query_keywords = set(query.lower().split())
    text_keywords = set(text.lower().split())

    return len(query_keywords & text_keywords)


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
            f"  • Risk Flags: {latest.get('risk_assessment', []) if latest.get('risk_assessment') else 'None'}",
        ]
        context_parts.append("\n".join(analysis_lines))

    # 3. Current message (highlighted)
    if getattr(state, "input_text", None):
        query = state.input_text
        context_parts.append(f'NEW MESSAGE FROM USER:\n  "{state.input_text}"')
    else:
        query = ""

    if query:
        filtered_chunks = filter_relevant_context(context_parts, query, top_k=4)
    else:
        filtered_chunks = context_parts

    return "\n\n".join(filtered_chunks)
