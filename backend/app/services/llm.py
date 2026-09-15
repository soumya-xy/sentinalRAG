"""Gemini (and optional other) LLM helpers for captioning and query compose."""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings


def message_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text") or ""))
            elif hasattr(item, "text"):
                parts.append(str(item.text))
        return "".join(parts)
    return str(content)


def get_chat_model():
    settings = get_settings()
    provider = (settings.llm_provider or "google").lower()
    if provider == "google":
        if not settings.google_api_key:
            return None
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.google_model,
            google_api_key=settings.google_api_key,
            temperature=0.2,
        )
    if provider == "anthropic" and settings.anthropic_api_key:
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
            temperature=0.2,
        )
    return None


def invoke_gemini_vision(prompt: str, jpeg_base64: str) -> str:
    settings = get_settings()
    if not settings.google_api_key:
        raise RuntimeError("GOOGLE_API_KEY is required for Gemini vision captions")
    from langchain_core.messages import HumanMessage
    from langchain_google_genai import ChatGoogleGenerativeAI

    model = ChatGoogleGenerativeAI(
        model=settings.google_model,
        google_api_key=settings.google_api_key,
        temperature=0.2,
    )
    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{jpeg_base64}"},
            },
        ]
    )
    result = model.invoke([message])
    return message_text(result.content)
