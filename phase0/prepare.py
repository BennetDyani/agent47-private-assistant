"""Convert raw recordings to 16 kHz mono WAV and build the benchmark manifest.

Expected layout (see docs/phase0/recording-guide.md):

    data/recordings/raw/<speaker>/<device>/<file containing prompt id, e.g. zu05.m4a>
    data/recordings/raw/<speaker>/<device>/<lang>/<files in prompt order>   (e.g. WhatsApp voice notes)

Usage:  uv run python -m phase0.prepare
"""

import csv
import re
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

from . import LANG_NAMES, MANIFEST_CSV, RAW_DIR, TRANSCRIPTS_CSV, WAV_DIR
from .prompts import Prompt, load_prompts

AUDIO_EXTS = {".m4a", ".wav", ".mp3", ".ogg", ".opus", ".aac", ".flac", ".webm", ".caf"}
PROMPT_ID = re.compile(r"(?<![a-z])(en|zu|tn|ts)(\d{2})(?!\d)", re.IGNORECASE)


def find_prompt_id(filename: str) -> str | None:
    m = PROMPT_ID.search(Path(filename).stem)
    return f"{m.group(1).lower()}{m.group(2)}" if m else None


def assign_clips(device_dir: Path, prompts: dict[str, Prompt]) -> tuple[list[tuple[Path, str]], list[str]]:
    """Map audio files under one <speaker>/<device> folder to prompt ids."""
    pairs, problems = [], []
    for path in sorted(device_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in AUDIO_EXTS:
            pid = find_prompt_id(path.name)
            if pid in prompts:
                pairs.append((path, pid))
            else:
                problems.append(f"{path}: no prompt id in filename (rename it, e.g. zu05{path.suffix})")
        elif path.is_dir() and path.name in LANG_NAMES:
            # Unnamed files (e.g. voice notes) in a language folder: assign in prompt order.
            files = sorted(p for p in path.iterdir() if p.suffix.lower() in AUDIO_EXTS)
            ids = [pid for pid, p in prompts.items() if p.lang == path.name]
            if len(files) != len(ids):
                problems.append(
                    f"{path}: {len(files)} files but {len(ids)} prompts for {path.name}; "
                    "can't match by order. Rename files with prompt ids instead."
                )
                continue
            pairs.extend(zip(files, ids))
    return pairs, problems


def load_overrides() -> dict[tuple[str, str], str]:
    """transcripts.csv: speaker,prompt_id,transcript - for free speech or when someone deviated."""
    if not TRANSCRIPTS_CSV.exists():
        return {}
    with open(TRANSCRIPTS_CSV, encoding="utf-8", newline="") as f:
        return {(r["speaker"], r["prompt_id"]): r["transcript"] for r in csv.DictReader(f)}


def to_wav(src: Path, dst: Path) -> None:
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(src),
           "-ac", "1", "-ar", "16000", str(dst)]
    subprocess.run(cmd, check=True)


def main() -> int:
    prompts = load_prompts()
    overrides = load_overrides()
    rows, problems = [], []

    for speaker_dir in sorted(p for p in RAW_DIR.glob("*") if p.is_dir()):
        for device_dir in sorted(p for p in speaker_dir.iterdir() if p.is_dir()):
            pairs, errs = assign_clips(device_dir, prompts)
            problems += errs
            for src, pid in pairs:
                speaker, device, prompt = speaker_dir.name, device_dir.name, prompts[pid]
                reference = overrides.get((speaker, pid))
                if reference is None and prompt.type == "free":
                    problems.append(f"{src}: free-speech clip needs a transcript in {TRANSCRIPTS_CSV.name}")
                    continue
                clip_id = f"{speaker}_{device}_{pid}"
                wav = WAV_DIR / f"{clip_id}.wav"
                to_wav(src, wav)
                rows.append({
                    "clip_id": clip_id, "wav": str(wav), "speaker": speaker, "device": device,
                    "prompt_id": pid, "lang": prompt.lang, "type": prompt.type,
                    "reference": reference or prompt.text,
                })

    MANIFEST_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["clip_id", "wav", "speaker", "device", "prompt_id",
                                               "lang", "type", "reference"])
        writer.writeheader()
        writer.writerows(rows)

    for p in problems:
        print("WARNING:", p)
    print(f"{len(rows)} clips ready -> {MANIFEST_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
