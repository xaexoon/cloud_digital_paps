"""등급 기준표 API 라우터 (클라우드 서버용)"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from src.logger.logger import get_logger

logger = get_logger('GradeStandardsRouter')
router = APIRouter(prefix="/api/grade", tags=["Grade_Standards"])

# grade_standards.py 파일 경로
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STANDARDS_PATH = os.path.join(BASE_DIR, 'src', 'param', 'grade_standards.py')


@router.get("/standards", response_class=PlainTextResponse)
def get_grade_standards():
    """grade_standards.py 코드를 그대로 리턴"""
    try:
        logger.info(f"DIR PATH : {STANDARDS_PATH}")
        with open(STANDARDS_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"파일 없음: {STANDARDS_PATH}")
        raise HTTPException(status_code=404, detail="grade_standards.py 파일을 찾을 수 없습니다")