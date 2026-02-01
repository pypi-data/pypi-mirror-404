import json
import re
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

import os
from core.ai.q_assistant import QAssistant

import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Heading:
    title: str
    startCharIndex: int


_DEFAULT_FALLBACKS = [
    # Common FAR-style and solicitation headings
    "Section L – Instructions",  # Instructions to Offerors
    "Section M – Evaluation Factors",  # Evaluation Factors/Criteria
    "Statement of Work",
    "Scope of Work",
    "Performance Work Statement",
    "Past Performance",
    "Pricing",
    "Price",
    "Cost",
]


def _normalize_title(title: str) -> str:
    """Normalize a heading title for deduplication (casefold + collapse spaces/punct)."""
    if not isinstance(title, str):
        return ""
    t = title.strip()
    # Replace various dashes with a simple hyphen for consistency
    t = t.replace("–", "-").replace("—", "-")
    # Collapse whitespace
    t = re.sub(r"\s+", " ", t)
    # Remove trailing punctuation-only suffixes
    t = re.sub(r"\s*[:.-]+\s*$", "", t)
    return t.casefold()


def detect_headings_heuristic(text: str) -> List[Dict[str, int]]:
    """Detect candidate headings using regex heuristics.

    Returns a list of {"title": str, "startCharIndex": int} sorted by start.
    """
    if not isinstance(text, str) or not text:
        return []
    candidates: List[Tuple[str, int, str]] = []  # (norm, start, raw)
    # Try to keep original positions; operate on original text but also its cleaned form
    hay = text
    # Patterns for common headings; keep them intentionally broad but anchored
    patterns = [
        # FAR-style sections like "Section L - ...", "Section M – ..." (A-Z)
        r"(?i)\bSection\s+[A-Z]\b[^\n]*",
        # Numeric sections like "Section 1.0 ..."
        r"(?i)\bSection\s+\d+(?:[.\-]\d+)*\b[^\n]*",
        # Canonical names
        r"(?i)\bInstructions\s+to\s+Offerors[^\n]*",
        r"(?i)\bEvaluation\s+(?:Factors|Criteria)[^\n]*",
        r"(?i)\bStatement\s+of\s+Work[^\n]*",
        r"(?i)\bScope\s+of\s+Work[^\n]*",
        r"(?i)\bPerformance\s+Work\s+Statement[^\n]*",
        r"(?i)\bPast\s+Performance[^\n]*",
        r"(?i)\b(?:Pricing|Price|Cost)\b[^\n]*",
    ]
    seen_spans: List[Tuple[int, int]] = []
    for pat in patterns:
        try:
            for m in re.finditer(pat, hay):
                raw = m.group(0)
                title = _normalize_title(raw)
                if not title:
                    continue
                start = m.start()
                # Basic de-dup by overlapping spans
                if any(a <= start < b for a, b in seen_spans):
                    continue
                candidates.append((title, start, raw.strip()))
                seen_spans.append((start, m.end()))
        except re.error:
            continue
    # Deduplicate by normalized title, keep earliest index
    by_title: Dict[str, Tuple[int, str]] = {}
    for norm, start, raw in candidates:
        if norm not in by_title or start < by_title[norm][0]:
            by_title[norm] = (start, raw)
    ordered = [
        {"title": t, "titleRaw": by_title[t][1], "startCharIndex": by_title[t][0]}
        for t in sorted(by_title.keys(), key=lambda k: by_title[k][0])
    ]
    return ordered


def detect_headings_llm(text: str, *, chunk_size: int = 12000, overlap: int = 800) -> List[Dict[str, int]]:
    """Detect headings via an LLM pass. Returns [{title,startCharIndex}] with absolute offsets.

    The model is asked to return a JSON array of objects with title and startCharIndex
    relative to the provided chunk; we then validate by re-searching the title in the
    chunk text and convert to absolute offsets. Titles that cannot be located are skipped.
    """
    if not isinstance(text, str) or not text:
        return []
    # Allow env overrides for chunking
    try:
        chunk_size = int(os.getenv('HEADING_LLM_CHUNK_SIZE', str(chunk_size)))
    except Exception:
        pass
    try:
        overlap = int(os.getenv('HEADING_LLM_OVERLAP', str(overlap)))
    except Exception:
        pass
    chunks: List[Tuple[int, str]] = []  # (start_idx, chunk_text)
    n = len(text)
    if n <= chunk_size:
        chunks.append((0, text))
    else:
        pos = 0
        while pos < n:
            end = min(n, pos + chunk_size)
            chunk = text[pos:end]
            chunks.append((pos, chunk))
            if end >= n:
                break
            pos = max(pos + chunk_size - overlap, pos + 1)

    assistant = QAssistant()
    out: List[Dict[str, int]] = []
    for idx, (start_idx, chunk) in enumerate(chunks, start=1):
        prompt = (
            "Return ONLY a JSON array of ordered section headings found in the given text chunk. "
            "Each item MUST have: {\"title\": string, \"startCharIndex\": number} where \"startCharIndex\" "
            "is the character index RELATIVE TO THIS CHUNK (0-based) for the first character of the heading title in the chunk.\n\n"
            "Strictly output JSON only, no commentary.\n\n"
            "Text chunk:\n<<<\n" + chunk + "\n>>>\n"
        )
        try:
            resp = str(assistant.run_task(prompt)).strip()
        except Exception:
            logger.exception("LLM heading detection failed for chunk %d/%d", idx, len(chunks))
            continue
        # Extract JSON array possibly wrapped in code fences
        try:
            m = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", resp)
            payload = m.group(1) if m else resp
            arr = json.loads(payload)
            if not isinstance(arr, list):
                arr = []
        except Exception:
            logger.debug("LLM heading output not parseable; skipping chunk %d", idx)
            arr = []

        # Validate headings by locating title in the chunk
        for it in arr:
            try:
                title_raw = it.get("title")
                if not isinstance(title_raw, str) or not title_raw.strip():
                    continue
                title_norm = _normalize_title(title_raw)
                # find literal occurrence (normalized) within chunk
                # We search for the raw title first; fallback to normalized match
                local_match = chunk.find(title_raw)
                if local_match < 0:
                    # approximate search using normalization
                    ch_norm = _normalize_title(chunk)
                    tpos = ch_norm.find(title_norm)
                    if tpos < 0:
                        continue
                    # Best-effort remap: use tpos in normalized string as an approximation
                    local_match = max(0, tpos)
                abs_idx = start_idx + local_match
                out.append({"title": title_norm, "titleRaw": title_raw.strip(), "startCharIndex": abs_idx})
            except Exception:
                continue

    # Merge and dedupe by title; keep earliest index
    return normalize_and_merge(out)


def normalize_and_merge(headings: List[Dict[str, int]], *, cap: int = 40) -> List[Dict[str, int]]:
    """Normalize and deduplicate a list of heading dicts; sort by startCharIndex; cap length."""
    if not headings:
        return []
    by_title: Dict[str, Tuple[int, str]] = {}
    for it in headings:
        try:
            t = _normalize_title(it.get("title", ""))
            s = int(it.get("startCharIndex", 0))
            raw = it.get("titleRaw") or it.get("title")
            if not t:
                continue
            if t not in by_title or s < by_title[t][0]:
                by_title[t] = (s, str(raw) if raw is not None else t)
        except Exception:
            continue
    ordered = [
        {"title": t, "titleRaw": by_title[t][1], "startCharIndex": by_title[t][0]}
        for t in sorted(by_title.keys(), key=lambda k: by_title[k][0])
    ]
    return ordered[:cap]


def derive_global_heading_order(per_volume_headings: Dict[str, List[Dict[str, int]]], fallbackNames: Optional[List[str]] = None) -> List[str]:
    """Derive a single ordered list of unique heading titles across volumes.

    Strategy:
    - Pick the primary volume as the one with the most detected headings.
    - Start with its ordered headings.
    - Append any additional headings from other volumes in the order of first occurrence.
    - Finally append fallbackNames (or defaults) that aren't already present.
    """
    fallback = fallbackNames or _DEFAULT_FALLBACKS
    if not per_volume_headings:
        return [_normalize_title(x) for x in fallback]

    # Choose primary by count
    primary_name = None
    primary_list: List[Dict[str, int]] = []
    for vname, lst in per_volume_headings.items():
        if len(lst) > len(primary_list):
            primary_name = vname
            primary_list = lst
    primary_titles = [_normalize_title(it.get("title", "")) for it in primary_list]
    ordered_unique: List[str] = []
    for t in primary_titles:
        if t and t not in ordered_unique:
            ordered_unique.append(t)

    # Merge others
    for vname, lst in per_volume_headings.items():
        if vname == primary_name:
            continue
        for it in lst:
            t = _normalize_title(it.get("title", ""))
            if t and t not in ordered_unique:
                ordered_unique.append(t)

    # Append fallbacks
    for fb in fallback:
        t = _normalize_title(fb)
        if t and t not in ordered_unique:
            ordered_unique.append(t)
    return ordered_unique


__all__ = [
    "Heading",
    "detect_headings_heuristic",
    "detect_headings_llm",
    "normalize_and_merge",
    "derive_global_heading_order",
]
