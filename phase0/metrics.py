"""Word and character error rates with text normalisation suited to SA languages."""

import re
import unicodedata

_PUNCT = re.compile(r"[^\w\s]")
_SPACE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Lowercase, fold accents (ê -> e, š -> s), drop hyphens/apostrophes/punctuation.

    Hyphens are removed rather than split so that "ama-imeyili" and "amaimeyili"
    (both seen in practice) score as the same word.
    """
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.replace("-", "").replace("'", "").replace("’", "")
    text = _PUNCT.sub(" ", text)
    return _SPACE.sub(" ", text).strip()


def _edit_distance(ref: list, hyp: list) -> int:
    prev = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        cur = [i]
        for j, h in enumerate(hyp, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (r != h)))
        prev = cur
    return prev[-1]


def error_counts(reference: str, hypothesis: str) -> tuple[int, int, int, int]:
    """Return (word_errors, ref_words, char_errors, ref_chars) after normalisation."""
    ref, hyp = normalize(reference), normalize(hypothesis)
    return (
        _edit_distance(ref.split(), hyp.split()),
        len(ref.split()),
        _edit_distance(list(ref), list(hyp)),
        len(ref),
    )


def wer(reference: str, hypothesis: str) -> float:
    errors, n, _, _ = error_counts(reference, hypothesis)
    return errors / n if n else 0.0


def cer(reference: str, hypothesis: str) -> float:
    _, _, errors, n = error_counts(reference, hypothesis)
    return errors / n if n else 0.0
