from typing import List

QUESTIONS = [
    "나는 새로운 사람들을 만나는 것을 즐긴다.",
    "나는 대규모 모임보다는 소규모 모임을 선호한다.",
    "나는 대화의 중심에 있는 것을 좋아한다.",
    "나는 혼자 시간을 보내며 재충전한다.",
    "나는 즉흥적인 계획을 세우는 것을 좋아한다."
]

def classify_personality(answers: List[int]) -> str:
    """
    Classifies personality based on survey answers.
    - 5 questions, Likert scale 1-5.
    - Questions 2 and 4 are reverse-scored.
    - Score >= 18: 외향 (Extrovert)
    - Score <= 10: 내향 (Introvert)
    - Otherwise: 중간 (Ambivert)
    """
    if len(answers) != 5:
        raise ValueError("Expected 5 answers.")

    scores = answers.copy()
    # Reverse score questions 2 and 4
    scores[1] = 6 - scores[1]
    scores[3] = 6 - scores[3]

    total_score = sum(scores)

    if total_score >= 18:
        return "외향"
    elif total_score <= 10:
        return "내향"
    else:
        return "중간"