"""등급 관련 유틸리티 함수"""

from src.param.total_grade import TOTAL_GRADE


def get_grade(value, grade) -> int:
    """측정값이 0이면 5등급 반환, 아니면 계산된 등급 반환"""
    if value == 0 or value is None:
        return 5
    return grade if grade else 5


def get_score(value, score) -> int:
    """측정값이 0이면 0점 반환, 아니면 해당 점수 반환"""
    if value == 0 or value is None:
        return 0
    return score if score else 0


def calculate_total_grade_by_score(total_score: int) -> int:
    """5개 체력요인 score 합산으로 종합 등급 계산

    Args:
        total_score: 5개 체력요인 점수 합산 (0~100)

    Returns:
        종합 등급 (1~5)
    """
    for grade, range_info in TOTAL_GRADE.items():
        if range_info["min"] <= total_score <= range_info["max"]:
            return grade

    # 범위 밖이면 5등급
    return 5


def calculate_total_grade(grades: list) -> int:
    """(하위 호환용) 유효한 등급들의 평균을 계산하여 종합 등급 반환"""
    valid_grades = [g for g in grades if g and g > 0]
    if not valid_grades:
        return 5
    return round(sum(valid_grades) / len(valid_grades))


def calculate_bmi(height: float, weight: float) -> float:
    """BMI 계산"""
    if not height or not weight or height <= 0:
        return 0
    height_m = height / 100
    return round(weight / (height_m ** 2), 2)