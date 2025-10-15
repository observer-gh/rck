from dataclasses import dataclass, field
from typing import List, Dict, Optional
import datetime as _dt


def _now_iso():
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


from typing import List, Dict, Optional

@dataclass
class User:
    id: str
    name: str
    employee_number: str
    region: str
    rank: str
    interests: List[str]
    personality_trait: str  # 외향, 내향, 중간
    survey_answers: Optional[List[int]] = None
    created_at: str = field(default_factory=_now_iso)


@dataclass
class Club:
    id: str
    member_ids: List[str]
    leader_id: str
    name: Optional[str] = None
    primary_interest: Optional[str] = None
    status: str = 'Matched'  # Matched | Active
    chat_link: Optional[str] = None
    match_score_breakdown: Dict[str, int] = field(default_factory=dict)
    explanations: Dict[str, Dict[str, str]] = field(
        default_factory=dict)  # user_id -> other_user_id -> reason string
    match_run_id: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)


@dataclass
class ActivityReport:
    id: str
    club_id: str
    date: str  # YYYY-MM-DD
    photo_filename: str
    raw_text: str
    formatted_report: str
    participant_override: Optional[int] = None
    verification_metrics: Optional[Dict[str, float]] = None
    status: str = 'Pending'  # Pending | Verified
    verified_at: Optional[str] = None
    points_awarded: int = 0
    created_at: str = field(default_factory=_now_iso)


@dataclass
class MatchRun:
    id: str
    created_at: str
    target_size: int
    user_count: int
    club_count: int
    superseded: bool = False
