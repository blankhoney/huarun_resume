from openai import OpenAI

from huarun_app.settings import get_settings


def complete_chat(messages: list[dict[str, str]]) -> str:
    settings = get_settings()
    if not settings.minimax_api_key:
        raise RuntimeError("MiniMax API key is not configured")

    client = OpenAI(
        base_url=settings.minimax_base_url,
        api_key=settings.minimax_api_key,
    )
    response = client.chat.completions.create(
        model=settings.minimax_model,
        messages=messages,
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("MiniMax returned an empty response")
    return content
