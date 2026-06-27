"""Pure scoring helpers for inter-annotator agreement (IAA).

No DB / framework imports — kept pure so it can be unit-tested in isolation
(`python3 scoring.py` runs the self-tests). Used by A1 (double-blind) to compare
two annotators' transcripts of the same page and by A2 (gold pages) to score an
annotator against ground truth.
"""

from typing import List, Optional


def _levenshtein(a: str, b: str) -> int:
    """Edit distance between two strings (insertions/deletions/substitutions)."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def cer(reference: str, hypothesis: str) -> float:
    """Character error rate of `hypothesis` against `reference` (>= 0.0)."""
    ref = reference or ""
    hyp = hypothesis or ""
    if not ref:
        return 0.0 if not hyp else 1.0
    return _levenshtein(ref, hyp) / len(ref)


def agreement(a: str, b: str) -> float:
    """Symmetric character-level agreement in [0, 1]; 1.0 means identical.

    Defined as 1 - editdistance/max(len). Symmetric (order of args does not
    matter), unlike CER which is relative to a chosen reference.
    """
    a = a or ""
    b = b or ""
    if not a and not b:
        return 1.0
    denom = max(len(a), len(b)) or 1
    return 1.0 - (_levenshtein(a, b) / denom)


def transcript_from_boxes(boxes: List[dict]) -> str:
    """Concatenate box text in reading order into one normalised transcript.

    `boxes` are dicts as returned by box_db (keys: content_text, reading_order, id).
    Boxes with no text are skipped; ordering is by reading_order then id, with
    null reading_order sorted last (matching box_db.get_boxes).
    """
    def key(b: dict):
        ro: Optional[int] = b.get("reading_order")
        return (ro is None, ro if ro is not None else 0, b.get("id") or 0)

    parts = []
    for b in sorted(boxes, key=key):
        text = (b.get("content_text") or "").strip()
        if text:
            parts.append(text)
    return "\n".join(parts)


# Pages with IAA at or above this threshold are considered "agreed" (PIPELINE §2).
IAA_ACCEPT_THRESHOLD = 0.98


if __name__ == "__main__":
    assert _levenshtein("kitten", "sitting") == 3
    assert cer("abc", "abc") == 0.0
    assert cer("abc", "abx") == 1 / 3
    assert cer("", "") == 0.0
    assert cer("", "x") == 1.0
    assert agreement("abc", "abc") == 1.0
    assert agreement("", "") == 1.0
    assert agreement("a", "") == 0.0
    assert abs(agreement("kitten", "sitting") - (1 - 3 / 7)) < 1e-9
    assert agreement("abc", "abd") == agreement("abd", "abc")  # symmetric
    assert transcript_from_boxes([
        {"content_text": "second", "reading_order": 2, "id": 10},
        {"content_text": "first",  "reading_order": 1, "id": 11},
        {"content_text": "",        "reading_order": 3, "id": 12},
        {"content_text": "last",   "reading_order": None, "id": 9},
    ]) == "first\nsecond\nlast"
    print("scoring self-tests passed")
