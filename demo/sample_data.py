from utils.ids import create_id_with_prefix
from domain.models import User
from services.survey import classify_personality
import random
from domain.constants import INTERESTS, REGIONS, RANKS

def make_users(n: int = 15):
    users = []
    for i in range(n):
        k = random.sample(INTERESTS, k=random.randint(2, 4))
        answers = [random.randint(1, 5) for _ in range(5)]
        trait = classify_personality(answers)
        users.append(User(
            id=create_id_with_prefix('u'),
            name=f"사용자{i+1}",
            employee_number=f"E{2024001+i}",
            region=random.choice(REGIONS),
            rank=random.choice(RANKS),
            interests=k,
            personality_trait=trait,
            survey_answers=answers
        ))
    return users
