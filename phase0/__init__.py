"""Phase 0: language spike - benchmark speech-to-text for isiZulu, Setswana, Xitsonga and English."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_CSV = Path(__file__).resolve().parent / "prompts.csv"
DATA = ROOT / "data"
RAW_DIR = DATA / "recordings" / "raw"
WAV_DIR = DATA / "recordings" / "wav"
MANIFEST_CSV = DATA / "recordings" / "manifest.csv"
TRANSCRIPTS_CSV = DATA / "recordings" / "transcripts.csv"
RESULTS_DIR = DATA / "results"

LANG_NAMES = {"en": "English", "zu": "isiZulu", "tn": "Setswana", "ts": "Xitsonga"}
