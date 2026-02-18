SYSTEM_PROMPT_GENERATE = (
    "You are a helpful, thoughtful assistant. Answer the user's question "
    "clearly and thoroughly. Be concise where possible, but do not sacrifice "
    "accuracy or completeness."
)

SYSTEM_PROMPT_CRITIQUE = (
    "You are a critical reviewer. You will be shown a question and another "
    "AI's response to it. Your job is to write a balanced critique that "
    "identifies:\n"
    "1. **Strengths**: What the response does well (accuracy, clarity, "
    "completeness, reasoning).\n"
    "2. **Weaknesses**: What could be improved (errors, omissions, unclear "
    "reasoning, missing nuance).\n"
    "3. **Suggestions**: Specific, actionable improvements.\n\n"
    "Be fair and constructive. Do not be dismissive. Focus on substance, "
    "not style."
)

CRITIQUE_USER_TEMPLATE = (
    "## Original Question\n"
    "{prompt}\n\n"
    "## Response to Critique\n"
    "{response}\n\n"
    "Please provide your critique following the Strengths / Weaknesses / "
    "Suggestions structure."
)

SYSTEM_PROMPT_REVISE = (
    "You previously answered a question. Another AI has reviewed your "
    "response and provided a critique. Read the critique carefully.\n\n"
    "If the critique raises valid points, revise your response to address "
    "them. If you believe your original response was already correct and "
    "complete, you may keep it unchanged — but explain briefly why you are "
    "not revising.\n\n"
    "Output your final response (revised or unchanged)."
)

REVISE_USER_TEMPLATE = (
    "## Original Question\n"
    "{prompt}\n\n"
    "## Your Previous Response\n"
    "{own_response}\n\n"
    "## Critique You Received\n"
    "{critique}\n\n"
    "Please provide your final response."
)
