"""Text chat with Malume.  Usage:  uv run python -m malume

Commands: /facts (what Malume remembers), /forget <n>, /quit
"""

import os
import sys

from dotenv import load_dotenv

from . import DB_PATH, ROOT
from .brain import Brain, GeminiLLM
from .memory import Memory


def main() -> int:
    load_dotenv(ROOT / ".env")
    if not os.environ.get("GEMINI_API_KEY"):
        print("No GEMINI_API_KEY found. Get a free key at https://aistudio.google.com/apikey "
              "and put it in .env (see .env.example).")
        return 1

    memory = Memory(DB_PATH)
    brain = Brain(memory, GeminiLLM())
    print("Malume is here. Type /quit to leave.\n")

    while True:
        try:
            text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text:
            continue
        if text == "/quit":
            break
        if text == "/facts":
            for fid, fact in memory.facts() or [(0, "(nothing yet)")]:
                print(f"  {fid}: {fact}")
            continue
        if text.startswith("/forget "):
            ok = memory.forget_fact(int(text.split()[1]))
            print("  forgotten" if ok else "  no such fact")
            continue
        try:
            print(f"Malume: {brain.reply(text)}\n")
        except Exception as e:
            print(f"  [error: {type(e).__name__}: {e}]\n")

    print("Sharp, mshana. Hamba kahle!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
