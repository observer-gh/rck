from domain.models import User
from services import matching


def make_user(i: int, region="서울", trait="중간", rank="사원", interests=None):
    if interests is None:
        interests = ["축구", "영화보기"]
    return User(
        id=f"u{i}",
        name=f"사용자{i}",
        employee_number=f"E{i:04d}",
        region=region,
        rank=rank,
        interests=interests,
        personality_trait=trait,
        survey_answers=[3, 3, 3, 3, 3]
    )


def test_compute_matches_forms_clubs_with_common_interest():
    users = [
        make_user(1, interests=["축구", "독서"], rank="사원"),
        make_user(2, interests=["축구"], rank="대리"),
        make_user(3, interests=["축구", "요리"], rank="과장"),
        make_user(4, interests=["축구"], rank="차장"),
        make_user(5, interests=["축구", "헬스"], rank="부장"),
    ]
    clubs = matching.compute_matches(users, target_size=5, run_id="run_test")
    assert len(clubs) == 1
    club = clubs[0]
    assert set(club.member_ids) == {u.id for u in users}
    # All share "축구"
    assert club.primary_interest in {"축구", "독서", "요리", "헬스"}
    assert club.match_run_id == "run_test"


def test_compute_matches_requires_minimum_users():
    users = [make_user(1), make_user(2), make_user(3), make_user(4)]
    try:
        matching.compute_matches(users)
    except AssertionError as e:
        assert "at least" in str(e)
    else:
        assert False, "Expected assertion for insufficient users"
# (Removed duplicate legacy tests to keep suite minimal and focused.)
