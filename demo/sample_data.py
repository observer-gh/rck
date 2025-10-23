from utils.ids import create_id_with_prefix
from domain.models import User
from services.survey import classify_personality
import random
from domain.constants import INTERESTS, REGIONS, RANKS
from services import persistence
from utils.korean_names import generate_canonical_names
from typing import Optional


def make_users(n: int = 15, start_index: Optional[int] = None):
    """Create n demo users with canonical Korean names.

    start_index: optional starting offset for deterministic naming. If not
    provided, derives from current user count to avoid collisions.
    """
    existing_users = persistence.load_list('users')
    existing_names = {u['name'] for u in existing_users if u.get('name')}
    if start_index is None:
        start_index = len(existing_users)  # simple offset
    names = generate_canonical_names(
        n, existing_names, start_index=start_index)

    users = []
    for i, nm in enumerate(names):
        interests_sample = random.sample(INTERESTS, k=random.randint(2, 4))
        answers = [random.randint(1, 5) for _ in range(5)]
        trait = classify_personality(answers)
        users.append(User(
            id=create_id_with_prefix('u'),
            name=nm,
            employee_number=f"E{2024001 + start_index + i}",
            region=random.choice(REGIONS),
            rank=random.choice(RANKS),
            interests=interests_sample,
            personality_trait=trait,
            survey_answers=answers
        ))
    return users
