"""Utility functions for generating canonical Korean names for demo user seeding.

The goal is to produce realistic, non-random-looking Korean full names while
remaining deterministic for reproducibility in demos.

Approach:
- Use a curated list of common family names.
- Use a curated list of common given names (precombined syllables) rather than
  constructing arbitrary syllable pairs.
- Deterministic indexing: given a global index i, map to a family and given
  name via modular arithmetic. This guarantees repeatability and coverage.
- Ensure uniqueness against an existing set of names; if a collision occurs,
  advance the index until a free name is found. If the pool is exhausted,
  append a numeric suffix like '(2)'.

Pool size: len(FAMILY_NAMES) * len(GIVEN_NAMES) supports a few thousand
unique combinations before suffixing.
"""
from __future__ import annotations
import re
from typing import List, Set

FAMILY_NAMES: List[str] = [
    "김", "이", "박", "최", "정", "강", "조", "윤", "장", "임",
    "오", "한", "신", "서", "권", "황", "안", "송", "유", "전"
]

# Curated common given names (gender-neutral or popular). Keep length 2~3.
GIVEN_NAMES: List[str] = [
    "서준", "민준", "서연", "지후", "하윤", "지우", "서현", "도윤", "예준", "하준",
    "지민", "유진", "수아", "윤서", "현우", "연우", "다은", "주원", "시우", "가은",
    "은우", "준서", "세아", "지호", "예린", "태윤", "소윤", "지안", "민서", "다현",
    "은서", "나윤", "채원", "시윤", "지환", "서율", "지유", "준우", "하율", "예서",
    "가윤", "시현", "하영", "재윤", "하진", "지혁", "리아", "서윤", "하민", "서희",
    "주현", "하은", "채윤", "태민", "나연", "하준", "채현", "다윤", "민재", "준혁",
    "지연", "세윤", "재민", "라윤", "지율", "서아", "유주", "서진", "수현", "연서",
    "하람", "세준", "지온", "연준", "예진", "지후", "도현", "지훈", "지은", "로아",
    "민희", "민호", "준호", "여준", "채민", "아린", "유나", "예원", "지성", "소현",
    "민유", "다원", "규민", "은채", "서린", "수민", "태연", "규진", "하온", "준영",
    "수빈", "이안", "정우", "소율", "은호", "세진", "민규", "지헌", "예슬", "서후",
    "하율", "윤우", "승현", "도연", "재현", "현서", "유빈", "승우", "시온", "도영",
    "하린", "채우", "산하", "민우", "하윤", "아현", "윤호", "지오", "준하", "예나",
    "다경", "도경", "소은", "미소", "도하", "라온", "이준", "유현", "주호", "주형",
    "지하", "태경", "하경", "예담", "유성", "가현", "유림", "예율", "아율", "주율"
]

_HANGUL_RE = re.compile(r"^[가-힣]{2,4}(?:\(\d+\))?$")


def validate_hangul(name: str) -> bool:
    """Return True if name is composed of Hangul syllables (optionally suffix)."""
    return bool(_HANGUL_RE.match(name))


def _raw_name_for_index(index: int) -> str:
    fam = FAMILY_NAMES[index % len(FAMILY_NAMES)]
    given = GIVEN_NAMES[(index // len(FAMILY_NAMES)) % len(GIVEN_NAMES)]
    return fam + given


def get_canonical_name(index: int, existing: Set[str]) -> str:
    """Generate a canonical name for a single index ensuring uniqueness.

    If the base name already exists, advance index until free; if the full
    pool is exhausted, append a numeric suffix.
    """
    attempts = 0
    base_index = index
    max_pool = len(FAMILY_NAMES) * len(GIVEN_NAMES)
    while attempts < max_pool:
        candidate = _raw_name_for_index(base_index + attempts)
        if candidate not in existing:
            return candidate
        attempts += 1
    # Pool exhausted; start suffixing
    suffix = 2
    candidate = _raw_name_for_index(base_index % max_pool)
    while f"{candidate}({suffix})" in existing:
        suffix += 1
    return f"{candidate}({suffix})"


def generate_canonical_names(count: int, existing: Set[str], start_index: int = 0) -> List[str]:
    names: List[str] = []
    used = set(existing)
    for i in range(count):
        name = get_canonical_name(start_index + i, used)
        used.add(name)
        names.append(name)
    return names


__all__ = [
    "FAMILY_NAMES",
    "GIVEN_NAMES",
    "validate_hangul",
    "get_canonical_name",
    "generate_canonical_names",
]
