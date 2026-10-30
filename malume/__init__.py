"""Malume - a friendly South African voice assistant (prototype)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DB_PATH = DATA / "malume.db"
