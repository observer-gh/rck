from typing import List

QUESTIONS = [
    "낯선 사람과도 금방 대화를 시작한다.",
    "생각을 정리할 때 혼자 있는 시간을 꼭 필요로 한다.",
    "여러 사람 앞에서 의견을 말하는 것이 편하다.",
    "피곤할 때 사람들과 어울리기보다 조용히 쉰다.",
    "팀 활동에서 분위기를 주도하는 편이다.",
    "즉흥적인 모임 제안이 오면 흔쾌히 참여한다.",
    "아이디어를 다른 사람과 빠르게 공유하는 것을 선호한다."
]


def classify_personality(answers: List[int]) -> str:
    """3점 척도(1~3) 7문항 평균 기반 성향 분류.
    값 의미: 1=아니요, 2=잘 모르겠다, 3=네
    평균 >= 2.4 → 외향, 평균 <= 1.6 → 내향, 그 사이는 중간.
    길이 불일치 시 보수적으로 중간 반환.
    """
    if not answers or len(answers) != len(QUESTIONS):
        return "중간"
    avg = sum(answers) / len(answers)
    if avg >= 2.4:
        return "외향"
    if avg <= 1.6:
        return "내향"
    return "중간"
