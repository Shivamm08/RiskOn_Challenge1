from llm_client import build_context_prompt


def test_build_context_prompt_includes_recent_chat_history():
    pages = [{"title": "Suitability basics", "text": "Suitability records are required for advisory advice."}]
    prompt = build_context_prompt(
        "Do I need a suitability record for advisory recommendations?",
        pages,
        [{"role": "user", "content": "I am advising a private client in Monaco."}, {"role": "assistant", "content": "I will use the Monaco suitability guidance."}],
    )

    assert "Earlier chat context" in prompt
    assert "User: I am advising a private client in Monaco." in prompt
    assert "Assistant: I will use the Monaco suitability guidance." in prompt
    assert "Do I need a suitability record for advisory recommendations?" in prompt
