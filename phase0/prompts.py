"""Load recording prompts and print readable scripts for speakers.

Usage:  uv run python -m phase0.prompts      (writes docs/phase0/script-<lang>.md)
"""

import csv
from dataclasses import dataclass

from . import LANG_NAMES, PROMPTS_CSV, ROOT


@dataclass(frozen=True)
class Prompt:
    id: str
    lang: str
    type: str  # pure | cs (code-switched) | free
    text: str


def load_prompts() -> dict[str, Prompt]:
    with open(PROMPTS_CSV, encoding="utf-8", newline="") as f:
        return {row["id"]: Prompt(**row) for row in csv.DictReader(f)}


def write_scripts() -> None:
    out_dir = ROOT / "docs" / "phase0"
    out_dir.mkdir(parents=True, exist_ok=True)
    prompts = list(load_prompts().values())
    for lang, name in LANG_NAMES.items():
        lines = [
            f"# Malume recording script: {name}",
            "",
            "Record **one clip per line**. Name each clip with its code (e.g. "
            f"`{lang}01`). Speak naturally, the way you would talk to a real person.",
            "If you say something different from the text, that's fine: just tell us what you actually said.",
            "",
        ]
        for p in (p for p in prompts if p.lang == lang):
            tag = {"pure": "", "cs": " _(mix)_", "free": " _(free speech)_"}[p.type]
            lines.append(f"- **{p.id}**{tag}: {p.text}")
        path = out_dir / f"script-{lang}.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    write_scripts()
