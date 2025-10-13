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
    return User(id=f'tu{i}', name=f'TU{i}', region=region, rank=rank, interests=interests, preferred_atmosphere=atmos)


def test_match_explanations_present(tmp_path, monkeypatch):
    # Redirect data dir for isolation
    data_dir = tmp_path / 'data'
    data_dir.mkdir()
    monkeypatch.setattr('services.persistence.DATA_DIR', str(data_dir))
    users = [make_user(i, ['축구', '영화보기']) for i in range(5)]
    clubs = compute_matches(users, target_size=5, run_id='testrun')
    assert clubs, 'Expected at least one club'
    club = clubs[0]
    # For each member explanations dict should have entries for other members
    for uid in club.member_ids:
        assert uid in club.explanations
        peers = club.explanations[uid]
        # each other user should appear
        assert all(other in peers for other in club.member_ids if other != uid)


def test_verify_report_points(tmp_path, monkeypatch):
    data_dir = tmp_path / 'data'
    data_dir.mkdir()
    monkeypatch.setattr('services.persistence.DATA_DIR', str(data_dir))
    # Create a fake report
    rep = activity.create_activity_report(club_id='clubX', date=str(
        dt.date.today()), photo_name='p', raw_text='내용', participant_override=3)
    reports = persistence.load_list('activity_reports')
    assert reports[0]['status'] == 'Pending'
    activity.verify_report(rep.id, points=15)
    reports2 = persistence.load_list('activity_reports')
    assert reports2[0]['status'] == 'Verified'
    assert reports2[0]['points_awarded'] == 15
