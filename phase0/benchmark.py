"""Run every clip in the manifest through the chosen STT engines and score them.

Usage:
    uv run python -m phase0.benchmark --engines gemini azure mms
    uv run python -m phase0.benchmark --engines gemini --lang zu --limit 5   # quick trial

Results are cached in data/results/<engine>.jsonl, so re-running only processes new clips.
Outputs data/results/summary.md (scores) and data/results/details.csv (every transcript).
"""

import argparse
import csv
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

from . import LANG_NAMES, MANIFEST_CSV, RESULTS_DIR, ROOT
from .metrics import error_counts
from .stt import ENGINES


def load_manifest() -> list[dict]:
    with open(MANIFEST_CSV, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_cache(engine: str) -> dict[str, dict]:
    path = RESULTS_DIR / f"{engine}.jsonl"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return {r["clip_id"]: r for r in map(json.loads, f) if not r.get("error")}


def run_engine(name: str, clips: list[dict]) -> None:
    cache = load_cache(name)
    todo = [c for c in clips if c["clip_id"] not in cache]
    if not todo:
        return
    engine = ENGINES[name]()
    todo = [c for c in todo if engine.supports(c["lang"])]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_DIR / f"{name}.jsonl", "a", encoding="utf-8") as out:
        for i, clip in enumerate(todo, 1):
            start = time.perf_counter()
            record = {"clip_id": clip["clip_id"]}
            try:
                record["hypothesis"] = engine.transcribe(Path(clip["wav"]), clip["lang"])
            except Exception as e:
                record["error"] = f"{type(e).__name__}: {e}"
            record["seconds"] = round(time.perf_counter() - start, 2)
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()
            status = record.get("error") or record["hypothesis"]
            print(f"[{name} {i}/{len(todo)}] {clip['clip_id']}: {status}")


def summarize(engines: list[str], clips: list[dict]) -> str:
    # (engine, lang, type) -> [word_err, words, char_err, chars, clips, seconds]
    totals = defaultdict(lambda: [0, 0, 0, 0, 0, 0.0])
    details = []
    for name in engines:
        cache = load_cache(name)
        for clip in clips:
            r = cache.get(clip["clip_id"])
            if r is None:
                continue
            counts = error_counts(clip["reference"], r["hypothesis"])
            for key in [(name, clip["lang"], clip["type"]), (name, clip["lang"], "all")]:
                t = totals[key]
                for k in range(4):
                    t[k] += counts[k]
                t[4] += 1
                t[5] += r["seconds"]
            details.append({"engine": name, "clip_id": clip["clip_id"], "lang": clip["lang"],
                            "type": clip["type"], "reference": clip["reference"],
                            "hypothesis": r["hypothesis"],
                            "wer": round(counts[0] / max(counts[1], 1), 3)})

    with open(RESULTS_DIR / "details.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["engine", "clip_id", "lang", "type", "reference",
                                               "hypothesis", "wer"])
        writer.writeheader()
        writer.writerows(details)

    lines = ["# Phase 0 STT results", "",
             "Lower is better. WER = word error rate, CER = character error rate. "
             "Types: pure, cs = code-switched, free = free speech.", "",
             "| Language | Type | Engine | Clips | WER | CER | Avg sec |",
             "|---|---|---|---|---|---|---|"]
    for (name, lang, typ), (we, w, ce, c, n, s) in sorted(
            totals.items(), key=lambda kv: (list(LANG_NAMES).index(kv[0][1]), kv[0][2], kv[0][0])):
        lines.append(f"| {LANG_NAMES[lang]} | {typ} | {name} | {n} | {we / max(w, 1):.1%} | "
                     f"{ce / max(c, 1):.1%} | {s / n:.1f} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--engines", nargs="+", choices=list(ENGINES), default=["gemini"])
    parser.add_argument("--lang", choices=list(LANG_NAMES), help="only this language")
    parser.add_argument("--limit", type=int, help="only the first N clips (for a quick trial)")
    args = parser.parse_args()

    clips = load_manifest()
    if args.lang:
        clips = [c for c in clips if c["lang"] == args.lang]
    if args.limit:
        clips = clips[: args.limit]

    for name in args.engines:
        run_engine(name, clips)

    report = summarize(args.engines, clips)
    (RESULTS_DIR / "summary.md").write_text(report, encoding="utf-8")
    print("\n" + report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
