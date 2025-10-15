from utils.ids import create_id_with_prefix
from domain.models import User
from .survey import classify_personality
import random

INTERESTS = ["축구", "영화보기", "보드게임", "러닝", "독서", "헬스", "요리", "사진", "등산"]
REGIONS = ["서울", "부산", "대전", "대구"]
RANKS = ["사원", "대리", "과장", "차장", "부장"]

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
