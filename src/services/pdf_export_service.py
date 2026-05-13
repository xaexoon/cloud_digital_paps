"""PDF 생성 관련 비즈니스 로직"""

import os
from typing import Dict
from src.services.pdf_service import PapsPdfGenerator, StudentData
from src.services.measurement_service import measurement_service


class PdfExportService:
    """PDF 생성 서비스"""

    def __init__(self, template_path: str = "src/templates/template.pdf",
                 font_path: str = "src/fonts",
                 output_dir: str = "src/output"):
        self.template_path = template_path
        self.font_path = font_path
        self.output_dir = output_dir

    def _ensure_output_dir(self):
        """출력 디렉토리 생성"""
        os.makedirs(self.output_dir, exist_ok=True)

    def create_student_data(self, user: Dict, measurement: Dict,
                            agility_exercise: str = "longJump",
                            muscle_exercise: str = "gripStrength") -> StudentData:
        """측정 데이터로부터 StudentData 객체 생성"""
        processed = measurement_service.process_measurement_data(
            measurement,
            agility_exercise=agility_exercise,
            muscle_exercise=muscle_exercise
        )

        return StudentData(
            name=user["name"],
            age=user["age"],
            gender="남" if measurement.get("gender", "").upper().startswith("M") else "여",
            school=user.get("school_name", ""),
            class_info=f"{user.get('grade_year', '')}학년 {user.get('class_number', '')}반 {user.get('student_number', '')}번",
            height=processed["height"],
            weight=processed["weight"],
            bmi=processed["bmi"],
            run_50m=measurement.get("50mRun", 0) or 0,
            shuttle_run=measurement.get("shuttleRun", 0) or 0,
            rolling_up=measurement.get("rollingUp", 0) or 0,
            flexibility=measurement.get("sitAndReach", 0) or 0,
            long_jump=measurement.get("longJump", 0) or 0,
            grip_right=processed["grip_right"],
            grip_left=processed["grip_left"],
            grade_50m=processed["grade_50m"],
            grade_shuttle=processed["grade_shuttle"],
            grade_rolling_up=processed["grade_rolling_up"],
            grade_flexibility=processed["grade_flexibility"],
            grade_long_jump=processed["grade_long_jump"],
            grade_grip_right=processed["grade_grip_right"],
            grade_grip_left=processed["grade_grip_left"],
            grade_bmi=processed["grade_bmi"],
            grade_total=processed["grade_total"],
            total_score=processed["total_score"],
            score_bmi=processed["score_bmi"],
            agility_exercise=agility_exercise,
            muscle_exercise=muscle_exercise,
        )

    def generate_pdf(self, user: Dict, measurement: Dict,
                     agility_exercise: str = "longJump",
                     muscle_exercise: str = "gripStrength") -> str:
        """단일 학생 PDF 생성, 파일 경로 반환"""
        self._ensure_output_dir()

        student = self.create_student_data(
            user, measurement,
            agility_exercise=agility_exercise,
            muscle_exercise=muscle_exercise
        )
        output_path = os.path.join(self.output_dir, f"{user['name']}_PAPS결과지.pdf")

        generator = PapsPdfGenerator(
            template_path=self.template_path,
            font_path=self.font_path
        )
        generator.generate(student, output_path)

        return output_path

    def generate_pdf_bytes(self, user: Dict, measurement: Dict,
                           agility_exercise: str = "longJump",
                           muscle_exercise: str = "gripStrength") -> tuple:
        """PDF 생성 후 파일명과 경로 반환 (ZIP용)"""
        output_path = self.generate_pdf(
            user, measurement,
            agility_exercise=agility_exercise,
            muscle_exercise=muscle_exercise
        )
        filename = f"{user['name']}_PAPS결과지.pdf"
        return output_path, filename


pdf_export_service = PdfExportService()