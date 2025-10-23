"""
This module contains centralized constants used throughout the application,
ensuring a single source of truth for values like regions, ranks, and interests.
"""

# These constants are used across multiple views to ensure consistency.

# List of available regions for users
REGIONS = [
    "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
    "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"
]

# List of available job ranks for users
RANKS = ["사원", "대리", "과장", "차장", "부장"]

# List of available interests for users
INTERESTS = ["축구", "영화보기", "보드게임", "러닝", "독서", "헬스", "요리", "사진", "등산"]

# Hard-coded demo user baseline (always present in session)
DEMO_USER = {
    'id': 'demo_user',
    'name': '데모사용자',
    'nickname': 'nemo',
    'employee_number': 'D0000001',
    'region': '서울',
    'rank': '사원',
    'interests': ['축구', '영화보기'],
    'personality_trait': '중간',
    'survey_answers': [2] * 7,
}
