import re
from utils.korean_names import generate_canonical_names, validate_hangul

HANGUL_RE = re.compile(r'^[가-힣]{2,4}(?:\(\d+\))?$')


def test_generate_unique_names_basic():
    existing = set()
    names = generate_canonical_names(30, existing)
    assert len(names) == 30
    assert len(set(names)) == 30
    for nm in names:
        assert validate_hangul(nm)
        assert HANGUL_RE.match(nm)


def test_collision_handling():
    # Pre-fill with first 10 deterministic names
    existing = set(generate_canonical_names(10, set()))
    new = generate_canonical_names(15, existing)
    assert len(new) == 15
    assert not any(n in existing for n in new)
