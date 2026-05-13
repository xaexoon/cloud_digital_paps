from pydantic import BaseModel
from typing import Optional, Union, Dict


class EmailData(BaseModel):
    email: str
    file_id: str = None


class ExportRequest(BaseModel):
    message: str = None
    file_id: str = None
    origin_file_name: str = None


class MeasurementData(BaseModel):
    tag_number: str
    exercise_type: str
    value: Union[float, Dict]  # 숫자 또는 객체
    unit: Optional[str] = ""
    gender: Optional[str] = ""
    age: Optional[int] = 0
    grade: Optional[Union[int, str, Dict]] = None  # 프론트에서 계산한 등급
    timestamp: str

    # 악력 전용 필드 추가
    right: Optional[float] = None
    left: Optional[float] = None
    right_grade: Optional[int] = None
    right_score: Optional[int] = None
    left_grade: Optional[int] = None
    left_score: Optional[int] = None

    # 제자리멀리뛰기 전용 필드 추가
    jump_1: Optional[float] = None
    jump_2: Optional[float] = None

    # 50m 달리기 전용 필드 추가
    lane_id: Optional[int] = None

    # 신체측정 전용 추가
    height: Optional[float] = None
    weight: Optional[float] = None
    bmi: Optional[float] = None
    score: Optional[int] = None


class PdfSearchRequest(BaseModel):
    """PDF 검색 요청 모델"""
    tag_number: Optional[str] = None
    school_code: Optional[str] = None
    measure_date: Optional[str] = None
    grade_year: Optional[str] = None
    class_number: Optional[str] = None
    student_number: Optional[str] = None
    student_name: Optional[str] = None
    agility_exercise: Optional[str] = "longJump"  # ★ 순발력 대표종목
    muscle_exercise: Optional[str] = "gripStrength"  # ★ 근력·근지구력 대표종목