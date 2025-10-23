from dataclasses import asdict
from domain.models import Club
from domain.models import User
from services.matching import compute_matches
from services import activity, persistence
import sys
import os
import datetime as dt
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def make_user(i, interests, region='서울', rank='사원', atmos='외향'):
    return User(id=f'tu{i}', name=f'TU{i}', employee_number=f"E-TEST-{i}", region=region, rank=rank, interests=interests, personality_trait=atmos)


def test_match_explanations_present(tmp_path, monkeypatch):
    # Redirect data dir for isolation
    data_dir = tmp_path / 'data'
    data_dir.mkdir()
    monkeypatch.setattr('services.persistence.DATA_DIR', str(data_dir))
    users = [make_user(i, ['축구', '영화보기']) for i in range(5)]
    clubs = compute_matches(users, target_size=5, run_id='testrun')
    assert clubs, 'Expected at least one club'
    club = clubs[0]
    # For each member, an explanation should exist.
    for uid in club.member_ids:
        assert uid in club.explanations
        explanation = club.explanations[uid]
        assert "그룹" in explanation
        assert "공통 관심사" in explanation["그룹"]
        assert "직급 다양성" in explanation["그룹"]


def test_verify_report_points(tmp_path, monkeypatch):
    data_dir = tmp_path / 'data'
    data_dir.mkdir()
    monkeypatch.setattr('services.persistence.DATA_DIR', str(data_dir))

    # Create a dummy club and users for the report to be verified against
    test_users = [make_user(i, ['축구', '영화보기']) for i in range(5)]
    test_club = Club(id='clubX', member_ids=[
                     u.id for u in test_users], leader_id=test_users[0].id)
    persistence.replace_all('users', [asdict(u) for u in test_users])
    persistence.replace_all('clubs', [asdict(test_club)])

    # Create a fake report that mentions an interest
    rep = activity.create_activity_report(club_id='clubX', date=str(
        dt.date.today()), photo_name='p', raw_text='축구도 보고 영화보기도 하고 재밌었다', participant_override=4)
    reports = persistence.load_list('activity_reports')
    assert reports[0]['status'] == 'Pending'

    activity.verify_report(rep.id, points=15)

    reports2 = persistence.load_list('activity_reports')
    verified_report = reports2[0]
    assert verified_report['status'] == 'Verified'
    # Check if points are awarded based on the simulation logic
    assert verified_report['points_awarded'] > 0
    assert 'verification_metrics' in verified_report
    assert verified_report['verification_metrics']['interest'] > 0

    # Now un-verify and ensure reset
    activity.unverify_report(verified_report['id'])
    reports3 = persistence.load_list('activity_reports')
    reverted = reports3[0]
    assert reverted['status'] == 'Pending'
    assert 'points_awarded' not in reverted
    assert 'verification_metrics' not in reverted
    assert 'verified_at' not in reverted
