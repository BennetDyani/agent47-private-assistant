"""The brain: combines persona, memory and an LLM into one conversational turn."""

import os
from collections.abc import Callable
from typing import Protocol

from .memory import Memory
from .persona import build_system_prompt

HISTORY_TURNS = 20


class LLM(Protocol):
    def generate(self, system: str, history: list[tuple[str, str]], user_text: str,
                 tools: list[Callable]) -> str: ...


# Lite first: ~1 s replies matter more than depth for a voice assistant.
DEFAULT_MODELS = "gemini-flash-lite-latest,gemini-flash-latest,gemini-3.5-flash-lite"


class GeminiLLM:
    """Google Gemini (free tier). Python functions passed as tools are called automatically.

    Free-tier models are often busy (503) or rate-limited (429), so we try each model in
    GEMINI_MODELS in turn instead of waiting on one.
    """

    def __init__(self, models: list[str] | None = None):
        from google import genai
        from google.genai import types

        self.client = genai.Client(
            api_key=os.environ["GEMINI_API_KEY"],
            http_options=types.HttpOptions(
                # No SDK retries: a busy model can stall for a minute; falling back is faster.
                timeout=20_000, retry_options=types.HttpRetryOptions(attempts=1)
            ),
        )
        self.models = models or os.environ.get("GEMINI_MODELS", DEFAULT_MODELS).split(",")

    def generate(self, system, history, user_text, tools):
        from google.genai import errors, types

        failures = []
        for model in self.models:
            # A fresh chat per turn: the system prompt changes as Malume learns new facts,
            # and the history lives in our own memory database.
            chat = self.client.chats.create(
                model=model.strip(),
                config=types.GenerateContentConfig(system_instruction=system, tools=tools),
                history=[types.Content(role=role, parts=[types.Part(text=text)]) for role, text in history],
            )
            try:
                return (chat.send_message(user_text).text or "").strip()
            except errors.APIError as e:
                if e.code not in (429, 500, 503, 504):
                    raise
                failures.append(f"{model}: {e.code}")
        raise RuntimeError("All Gemini models are busy, try again shortly (" + ", ".join(failures) + ")")


class Brain:
    def __init__(self, memory: Memory, llm: LLM):
        self.memory = memory
        self.llm = llm

    def tools(self) -> list[Callable]:
        memory = self.memory

        def remember(fact: str) -> str:
            """Save a short fact about the user to long-term memory."""
            return f"Saved as fact {memory.add_fact(fact)}."

        def forget(fact_number: int) -> str:
            """Delete a remembered fact by its number."""
            return "Forgotten." if memory.forget_fact(fact_number) else "No fact with that number."

        return [remember, forget]

    def reply(self, user_text: str) -> str:
        system = build_system_prompt(self.memory.facts())
        history = self.memory.recent_messages(HISTORY_TURNS)
        answer = self.llm.generate(system, history, user_text, self.tools())
        self.memory.add_message("user", user_text)
        self.memory.add_message("model", answer)
        return answer
