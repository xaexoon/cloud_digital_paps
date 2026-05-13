"""측정 데이터 관련 비즈니스 로직"""

from typing import Dict, Optional, Tuple
from src.utils.grade_utils import get_grade, get_score, calculate_total_grade_by_score, calculate_bmi


class MeasurementService:
    """측정 데이터 처리 서비스"""

    @staticmethod
    def extract_grip_data(measurement: Dict) -> Tuple[float, float]:
        """악력 데이터 추출 (좌, 우)"""
        grip_data = measurement.get("gripStrength", {})
        if isinstance(grip_data, dict):
            grip_left = grip_data.get("leftGrip", 0) or 0
            grip_right = grip_data.get("rightGrip", 0) or 0
        else:
            grip_left = 0
            grip_right = 0
        return grip_left, grip_right

    @staticmethod
    def extract_grip_grades(measurement: Dict) -> Tuple[Optional[int], Optional[int]]:
        """악력 등급 추출 (좌, 우)"""
        grip_grade = measurement.get("grade_gripStrength", {})
        if isinstance(grip_grade, dict):
            grade_grip_left = grip_grade.get("leftGrip")
            grade_grip_right = grip_grade.get("rightGrip")
        else:
            grade_grip_left = None
            grade_grip_right = None

        # None이면 5등급으로 처리
        return grade_grip_left or 5, grade_grip_right or 5

    @staticmethod
    def calculate_total_by_score(measurement: Dict, bmi: float,
                                  agility_exercise: str = "longJump",
                                  muscle_exercise: str = "gripStrength") -> Tuple[int, Optional[int]]:
        """5개 체력요인 score 합산 → 종합 등급 계산"""

        agility_score = get_score(
            measurement.get(agility_exercise, 0),
            measurement.get(f"score_{agility_exercise}")
        )
        muscle_score = get_score(
            measurement.get(muscle_exercise, 0),
            measurement.get(f"score_{muscle_exercise}")
        )
        flexibility_score = get_score(
            measurement.get("sitAndReach", 0),
            measurement.get("score_sitAndReach")
        )
        cardio_score = get_score(
            measurement.get("shuttleRun", 0),
            measurement.get("score_shuttleRun")
        )
        bmi_score = get_score(
            bmi,
            measurement.get("score_bodyMeasurement")
        )

        scores = [agility_score, muscle_score, flexibility_score, cardio_score, bmi_score]
        if any(s == 0 for s in scores):
            return 0, None

        total_score = sum(scores)
        total_grade = calculate_total_grade_by_score(total_score)
        return total_score, total_grade

    @staticmethod
    def process_measurement_data(measurement: Dict,
                                  agility_exercise: str = "longJump",
                                  muscle_exercise: str = "gripStrength") -> Dict:
        """측정 데이터를 처리하여 필요한 모든 값 계산"""
        height = measurement.get("height", 0) or 0
        weight = measurement.get("weight", 0) or 0
        bmi = calculate_bmi(height, weight)

        grip_left, grip_right = MeasurementService.extract_grip_data(measurement)
        grade_grip_left, grade_grip_right = MeasurementService.extract_grip_grades(measurement)

        total_score, grade_total = MeasurementService.calculate_total_by_score(
            measurement, bmi,
            agility_exercise=agility_exercise,
            muscle_exercise=muscle_exercise
        )

        bmi_score = get_score(bmi, measurement.get("score_bodyMeasurement"))

        return {
            "height": height,
            "weight": weight,
            "bmi": bmi,
            "grip_left": grip_left,
            "grip_right": grip_right,
            "grade_grip_left": grade_grip_left,
            "grade_grip_right": grade_grip_right,
            "grade_total": grade_total,
            "total_score": total_score,
            "grade_50m": get_grade(measurement.get("50mRun"), measurement.get("grade_50mRun")),
            "grade_shuttle": get_grade(measurement.get("shuttleRun"), measurement.get("grade_shuttleRun")),
            "grade_rolling_up": get_grade(measurement.get("rollingUp"), measurement.get("grade_rollingUp")),
            "grade_flexibility": get_grade(measurement.get("sitAndReach"), measurement.get("grade_sitAndReach")),
            "grade_long_jump": get_grade(measurement.get("longJump"), measurement.get("grade_longJump")),
            "grade_bmi": get_grade(bmi, measurement.get("grade_bodyMeasurement")),
            "score_bmi": bmi_score,
        }


measurement_service = MeasurementService()