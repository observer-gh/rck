from domain.models import User
from services.matching import score, compute_matches
import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def make_user(i, interests, region='서울', rank='사원', atmos='외향'):
    return User(id=f'u{i}', name=f'U{i}', region=region, rank=rank, interests=interests, preferred_atmosphere=atmos)


def test_score_components():
    u1 = make_user(1, ['A', 'B'], region='R1', rank='R', atmos='X')
    u2 = make_user(2, ['B', 'C'], region='R1', rank='R', atmos='X')
    s = score(u1, u2)
    # common interests=1 ->10, region +5, rank +3, atmos +2 =20
    assert s == 20


def test_grouping_no_duplicate_and_size():
    users = [make_user(i, ['K', 'L']) for i in range(10)]
    clubs = compute_matches(users, target_size=5)
    all_members = [m for c in clubs for m in c.member_ids]
    assert len(all_members) == 10
    assert len(set(all_members)) == 10
    # Each club size should be 5 (two clubs) for homogeneous users
    sizes = {len(c.member_ids) for c in clubs}
    assert sizes == {5}


def test_grouping_leftover_redistribution():
    users = [make_user(i, ['X', 'Y']) for i in range(7)]
    clubs = compute_matches(users, target_size=5)
    sizes = sorted([len(c.member_ids) for c in clubs])
    # Current algorithm may produce one group of 5 and redistribute leftover 2 into existing (yield [7]) or two full groups of 5 if logic changes.
    assert sizes in ([7], [5, 5])
