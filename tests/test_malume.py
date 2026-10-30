from datetime import datetime

from malume.brain import Brain
from malume.memory import Memory
from malume.persona import build_system_prompt


class FakeLLM:
    """Records what the brain sends and can call tools like the real model would."""

    def __init__(self, answer="Sharp, mshana.", call=None):
        self.answer, self.call, self.seen = answer, call, None

    def generate(self, system, history, user_text, tools):
        self.seen = (system, history, user_text)
        if self.call:
            name, arg = self.call
            {t.__name__: t for t in tools}[name](arg)
        return self.answer


def test_memory_facts_and_messages():
    m = Memory(":memory:")
    fid = m.add_fact("  Name is Bennett ")
    assert m.facts() == [(fid, "Name is Bennett")]
    assert m.add_fact("name is bennett") == fid and len(m.facts()) == 1
    assert m.forget_fact(fid) and not m.forget_fact(fid)
    for i in range(5):
        m.add_message("user", f"msg {i}")
    assert m.recent_messages(2) == [("user", "msg 3"), ("user", "msg 4")]


def test_system_prompt_includes_facts_and_date():
    prompt = build_system_prompt([(1, "Lives in Pretoria")], now=datetime(2026, 10, 30, 9, 0))
    assert "You are Malume" in prompt
    assert "1: Lives in Pretoria" in prompt
    assert "Friday 30 October 2026" in prompt


def test_brain_passes_history_and_saves_turn():
    m = Memory(":memory:")
    m.add_message("user", "Hi")
    m.add_message("model", "Hello mshana")
    llm = FakeLLM()
    assert Brain(m, llm).reply("How are you?") == "Sharp, mshana."
    assert llm.seen[1] == [("user", "Hi"), ("model", "Hello mshana")]
    assert m.recent_messages()[-2:] == [("user", "How are you?"), ("model", "Sharp, mshana.")]


def test_remember_tool_saves_fact_visible_next_turn():
    m = Memory(":memory:")
    Brain(m, FakeLLM(call=("remember", "Has a daughter named Lerato"))).reply("My daughter is Lerato")
    llm = FakeLLM()
    Brain(m, llm).reply("Who is my daughter?")
    assert "Has a daughter named Lerato" in llm.seen[0]
