import os
import uuid
import json

EMERGENT_KEY = os.environ.get('EMERGENT_LLM_KEY')


def parse_ai_json(response_text: str):
    """Parse AI response that may contain markdown code fences."""
    clean = response_text.strip()
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()
    return json.loads(clean)


async def create_llm_chat(session_prefix: str, system_message: str):
    """Create and configure an LLM chat instance."""
    from emergentintegrations.llm.chat import LlmChat
    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"{session_prefix}_{uuid.uuid4().hex[:8]}",
        system_message=system_message
    )
    chat.with_model("openai", "gpt-5.2")
    return chat
