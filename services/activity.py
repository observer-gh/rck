import datetime as dt
from dataclasses import asdict
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
        formatted_report=formatted
    )
    reports = persistence.load_list('activity_reports')
    reports.append(asdict(report))
    persistence.replace_all('activity_reports', reports)
    return report


def list_reports() -> List[Dict[str, Any]]:
    return persistence.load_list('activity_reports')


def verify_report(report_id: str, points: int = 10):
    reports = persistence.load_list('activity_reports')
    changed = False
    now = dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')
    for r in reports:
        if r['id'] == report_id:
            r['status'] = 'Verified'
            r['verified_at'] = now
            r['points_awarded'] = points
            changed = True
            break
    if changed:
        persistence.replace_all('activity_reports', reports)
    return changed
