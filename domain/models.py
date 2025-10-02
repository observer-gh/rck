from dataclasses import dataclass, field
from typing import List, Dict, Optional
import datetime as _dt


def _now_iso():
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


@dataclass
class User:
    id: str
    name: str
    region: str
    rank: str
    interests: List[str]
    preferred_atmosphere: str
    created_at: str = field(default_factory=_now_iso)


@dataclass
class Club:
    id: str
    member_ids: List[str]
    leader_id: str
    status: str = 'Matched'  # Matched | Active
    chat_link: Optional[str] = None
    match_score_breakdown: Dict[str, int] = field(default_factory=dict)
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
    status: str = 'Pending'  # Pending | Verified
    verified_at: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)


@dataclass
class MatchRun:
    id: str
    created_at: str
    target_size: int
    user_count: int
    club_count: int
    superseded: bool = False
