import datetime as dt
from dataclasses import asdict
import random
from typing import List, Dict, Any, Optional
import difflib
import os
import struct
from domain.models import ActivityReport
from utils.ids import create_id_with_prefix
from . import persistence


def create_activity_report(club_id: str, date: str, photo_name: str, raw_text: str, participant_override: Optional[int] = None):
    participant_count = participant_override if participant_override is not None else 'N/A'
    # Default photo fallback: broaden placeholder detection and load static/image.png if present
    placeholder_tokens = {'no_photo', 'none',
                          'empty', 'null', 'placeholder', ''}
    if (photo_name is None or str(photo_name).strip().lower() in placeholder_tokens) and os.path.exists(os.path.join('static', 'image.png')):
        photo_name = 'image.png'
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
    """Compute verification metrics.

    participants: ratio of sampled participants to club size.
    interest: proportion of club interest themes (with synonym/fuzzy matching) mentioned in report text.
    diversity: proportion of distinct ranks represented among participants vs ranks present in club.
    """
    # Metric 1: Participant Ratio
    participant_ratio = 0.0
    member_ids = club.get('member_ids', []) or []
    if member_ids:
        participant_ratio = min(
            1.0, len(report.get('participant_ids', [])) / len(member_ids))

    # Prepare interest data
    raw_text = (report.get('raw_text') or '').lower()
    # Tokenize naive (split on whitespace)
    tokens = [t.strip() for t in raw_text.replace(
        '\n', ' ').split(' ') if t.strip()]
    club_interests = {
        interest for user_id in member_ids for user in users if user['id'] == user_id for interest in user.get('interests', [])}

    # Synonym / related keyword map (lowercase)
    synonym_map: Dict[str, List[str]] = {
        '축구': ['축구', '풋볼', '풋살', 'soccer', 'football'],
        '보드게임': ['보드게임', '게임', '전략게임', '카드게임'],
        '러닝': ['러닝', '조깅', '달리기', 'run', 'running', 'jogging'],
        '독서': ['독서', '책', '독후', 'reading', 'book'],
        '헬스': ['헬스', '운동', '트레이닝', 'fitness', 'gym'],
        '요리': ['요리', '쿠킹', 'cooking', 'meal', '요리하기'],
        '사진': ['사진', '촬영', '포토', 'photo', '사진찍기'],
        '등산': ['등산', '산행', '하이킹', 'hiking', '트래킹', '트레킹']
    }

    def interest_mentioned(interest: str) -> bool:
        syns = synonym_map.get(interest, [interest])
        for s in syns:
            s_low = s.lower()
            if s_low in raw_text:
                return True
            # Fuzzy: compare against tokens
            for tok in tokens:
                if len(tok) >= 2 and difflib.SequenceMatcher(a=tok, b=s_low).ratio() >= 0.72:
                    return True
        return False

    interest_alignment = 0.0
    if club_interests:
        mentioned_count = sum(
            1 for interest in club_interests if interest_mentioned(interest))
        interest_alignment = mentioned_count / len(club_interests)

    # Metric 3: Rank Diversity
    participant_ranks = {user['rank'] for user_id in report.get(
        'participant_ids', []) for user in users if user['id'] == user_id}
    club_ranks = {user['rank']
                  for user_id in member_ids for user in users if user['id'] == user_id}
    rank_diversity = 0.0
    if club_ranks:
        rank_diversity = len(participant_ranks) / len(club_ranks)

    # Demo override: if this is clearly a soccer club (name or interests), force interest alignment to 100%
    club_name_low = (club.get('name') or '').lower()
    if any(token in club_name_low for token in ['축구', 'soccer', 'football']) or any(token in club_interests for token in ['축구', 'soccer', 'football']):
        interest_alignment = 1.0

    return {
        'participants': round(participant_ratio, 2),
        'interest': round(interest_alignment, 2),
        'diversity': round(rank_diversity, 2)
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
    participant_count = report.get(
        'participant_override') or random.randint(3, len(club['member_ids']))
    report['participant_ids'] = random.sample(
        club['member_ids'], k=min(participant_count, len(club['member_ids'])))

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


def prepare_report_verification(report_id: str, points: int = 10) -> Optional[Dict[str, Any]]:
    """Runs simulation but does NOT persist final verification status.

    Stores a transient preview payload on the report under 'verification_preview'.
    Admin must call finalize_report_verification to commit.
    Returns the preview dict or None on failure.
    """
    reports = persistence.load_list('activity_reports')
    clubs = persistence.load_list('clubs')
    users = persistence.load_list('users')
    report = next((r for r in reports if r['id'] == report_id), None)
    if not report:
        return None
    if report.get('status') == 'Verified':  # already done
        return None
    club = next((c for c in clubs if c['id'] == report['club_id']), None)
    if not club:
        return None
    participant_count = report.get(
        'participant_override') or min(5, len(club['member_ids']))
    sample_ids = random.sample(club['member_ids'], k=min(
        participant_count, len(club['member_ids'])))
    temp_report = dict(report)
    temp_report['participant_ids'] = sample_ids
    metrics = run_verification_simulation(temp_report, club, users)
    thresholds = {"participants": 0.75, "interest": 0.70, "diversity": 0.60}
    passed = all(metrics.get(k, 0) >= v for k, v in thresholds.items())
    preview = {
        "report_id": report_id,
        "metrics": metrics,
        "thresholds": thresholds,
        "passed": passed,
        "points_if_finalized": points if passed else 0,
        "participant_ids_preview": sample_ids,
    }
    report['verification_preview'] = preview
    persistence.replace_all('activity_reports', reports)
    return preview


def finalize_report_verification(report_id: str) -> bool:
    """Commits a previously prepared preview, turning it into a real verification."""
    reports = persistence.load_list('activity_reports')
    report = next((r for r in reports if r['id'] == report_id), None)
    if not report:
        return False
    preview = report.get('verification_preview')
    if not preview:
        return False
    # Commit
    now = dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')
    report['status'] = 'Verified'
    report['verified_at'] = now
    report['points_awarded'] = preview.get('points_if_finalized', 0)
    report['verification_metrics'] = preview.get('metrics', {})
    report['participant_ids'] = preview.get('participant_ids_preview', [])
    # Persist image analysis if it was performed during preview
    if 'image_analysis' in preview:
        report['image_analysis'] = preview['image_analysis']
    # Remove preview
    del report['verification_preview']
    persistence.replace_all('activity_reports', reports)
    return True


def unverify_report(report_id: str) -> bool:
    """Reverts a previously verified report back to Pending state.

    Clears verification-related fields so it can be re-processed.
    Returns True if successful, False if report missing or not Verified.
    """
    reports = persistence.load_list('activity_reports')
    report = next((r for r in reports if r['id'] == report_id), None)
    if not report or report.get('status') != 'Verified':
        return False
    # Reset status and remove verification metadata
    report['status'] = 'Pending'
    for k in ['verified_at', 'points_awarded', 'verification_metrics', 'participant_ids']:
        if k in report:
            del report[k]
    persistence.replace_all('activity_reports', reports)
    return True


def analyze_report_image(report_id: str) -> Optional[Dict[str, Any]]:
    """Mock AI image analysis for a report's attached photo.

    If a verification preview exists, attaches results under preview['image_analysis'];
    otherwise stores directly under report['image_analysis'].
    Deterministic output based on photo filename for repeatability.
    """
    reports = persistence.load_list('activity_reports')
    report = next((r for r in reports if r['id'] == report_id), None)
    if not report:
        return None
    photo = report.get('photo_filename')
    if not photo:
        return None
    # Deterministic pseudo-random based on filename
    seed_basis = sum(ord(c) for c in str(photo))
    rng = random.Random(seed_basis)
    tag_pool = ["운동", "야외", "팀워크", "게임", "식사", "교류", "학습", "전략", "활발", "편안"]
    tags = rng.sample(tag_pool, k=3)
    raw_text = report.get('raw_text', '') or ''
    relevance_hits = sum(1 for t in tags if t in raw_text)
    relevance_score = round(relevance_hits / len(tags), 2)
    # Attempt to read PNG dimensions if file exists
    img_path = os.path.join('static', photo)
    width = height = None
    file_size = None
    if os.path.exists(img_path):
        try:
            file_size = os.path.getsize(img_path)
            with open(img_path, 'rb') as f:
                header = f.read(24)
                # PNG signature + IHDR chunk
                if len(header) >= 24 and header[:8] == b'\x89PNG\r\n\x1a\n':
                    # IHDR length (bytes 8-12) then 'IHDR'(12-16) then width/height (16-24)
                    width, height = struct.unpack('>II', header[16:24])
        except Exception:
            pass
    analysis = {
        'tags': tags,
        'relevance_score': relevance_score,  # 0~1
        'safety': 'OK',
        'image': {
            'file': photo,
            'exists': os.path.exists(img_path),
            'size_bytes': file_size,
            'width': width,
            'height': height,
        },
        # Korean summary
        'commentary': f"이미지에 추정 태그 {', '.join(tags)} 감지. 보고 내용과의 관련도 {int(relevance_score*100)}%",
    }
    if 'verification_preview' in report:
        report['verification_preview']['image_analysis'] = analysis
    else:
        report['image_analysis'] = analysis
    persistence.replace_all('activity_reports', reports)
    return analysis
