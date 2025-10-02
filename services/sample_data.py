from utils.ids import create_id_with_prefix
from domain.models import User
import random

INTERESTS = ["축구", "영화보기", "보드게임", "러닝", "독서", "헬스", "요리", "사진", "등산"]
REGIONS = ["서울", "부산", "대전", "대구"]
RANKS = ["사원", "주임", "대리", "과장"]
ATMOS = ["외향", "내향", "밸런스"]


def make_users(n: int = 15):
    users = []
    for i in range(n):
        k = random.sample(INTERESTS, k=random.randint(2, 4))
        users.append(User(
            id=create_id_with_prefix('u'),
            name=f"사용자{i+1}",
            region=random.choice(REGIONS),
            rank=random.choice(RANKS),
            interests=k,
            preferred_atmosphere=random.choice(ATMOS)
        ))
    return users
