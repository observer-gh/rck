import datetime as dt
from dataclasses import asdict
import random
from typing import List, Dict, Any, Optional
from domain.models import ActivityReport
from utils.ids import create_id_with_prefix
from . import persistence


def create_activity_report(club_id: str, date: str, photo_name: str, raw_text: str, participant_override: Optional[int] = None):
    participant_count = participant_override if participant_override is not None else 'N/A'
    formatted = f"활동일자: {date}"
    if participant_count != '':
        formatted += f", 참여인원: {participant_count}"
    formatted += f", 활동내용: {raw_text}"
    formatted = formatted.strip()
    report = ActivityReport(
        id=create_id_with_prefix('rep'),
        club_id=club_id,
        date=date,
        photo_filename=photo_name,
        raw_text=raw_text,
        formatted_report=formatted,
        participant_override=participant_override
    )
    reports = persistence.load_list('activity_reports')
    reports.append(asdict(report))
    persistence.replace_all('activity_reports', reports)
    return report


def list_reports() -> List[Dict[str, Any]]:
    return persistence.load_list('activity_reports')


def run_verification_simulation(report: Dict[str, Any], club: Dict[str, Any], users: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Runs a deterministic simulation to score an activity report.
    Returns a dictionary with the scores for each metric.
    """
    # Metric 1: Participant Ratio
    participant_ratio = min(1.0, len(report.get('participant_ids', [])) / len(club.get('member_ids', [])))

    # Metric 2: Interest Alignment
    club_interests = {interest for user_id in club.get('member_ids', []) for user in users if user['id'] == user_id for interest in user['interests']}
    # Simple simulation: check if the report text mentions any of the club interests
    interest_alignment = 0.0
    if club_interests:
        mentioned_interests = {interest for interest in club_interests if interest in report.get('raw_text', '')}
        interest_alignment = len(mentioned_interests) / len(club_interests)

    # Metric 3: Rank Diversity
    participant_ranks = {user['rank'] for user_id in report.get('participant_ids', []) for user in users if user['id'] == user_id}
    rank_diversity = len(participant_ranks) / len(set(user['rank'] for user_id in club.get('member_ids', []) for user in users if user['id'] == user_id)) if club.get('member_ids') else 0

    return {
        "participants": round(participant_ratio, 2),
        "interest": round(interest_alignment, 2),
        "diversity": round(rank_diversity, 2)
    }


def verify_report(report_id: str, points: int = 10):
    reports = persistence.load_list('activity_reports')
    clubs = persistence.load_list('clubs')
    users = persistence.load_list('users')

    report = next((r for r in reports if r['id'] == report_id), None)
    if not report:
        return False

    club = next((c for c in clubs if c['id'] == report['club_id']), None)
    if not club:
        return False

    # Simulate some participants for the demo
    participant_count = report.get('participant_override') or random.randint(3, len(club['member_ids']))
    report['participant_ids'] = random.sample(club['member_ids'], k=min(participant_count, len(club['member_ids'])))

    metrics = run_verification_simulation(report, club, users)

    thresholds = {
        "participants": 0.75,
        "interest": 0.70,
        "diversity": 0.60
    }

    passed = all(metrics[key] >= thresholds[key] for key in thresholds)

    now = dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')
    report['status'] = 'Verified'
    report['verified_at'] = now
    report['points_awarded'] = points if passed else 0
    report['verification_metrics'] = metrics

    persistence.replace_all('activity_reports', reports)
    return True
