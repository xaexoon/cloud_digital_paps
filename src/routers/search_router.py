"""검색 API 라우터 - 학교 검색, 측정일 조회"""

from fastapi import APIRouter, HTTPException, Query

from src.logger.logger import get_logger
from src.database.db_handler import search_schools, get_measure_dates

logger = get_logger('SearchRouter')
router = APIRouter(prefix="/api/search", tags=["Search"])


@router.get("/schools")
async def search_schools_api(keyword: str = Query(..., min_length=1, description="학교명 검색어")):
    """학교명 검색 - 키워드로 학교 목록 반환"""
    try:
        results = search_schools(keyword)
        return {
            "success": True,
            "schools": results
        }
    except Exception as e:
        logger.error(f"학교 검색 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/measure-dates/{school_code}")
async def get_measure_dates_api(school_code: str):
    """학교별 측정일 목록 조회"""
    try:
        dates = get_measure_dates(school_code)
        return {
            "success": True,
            "dates": dates
        }
    except Exception as e:
        logger.error(f"측정일 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))