# src/api/api_router.py
from io import BytesIO

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse
from datetime import datetime
from pydantic import BaseModel
import os
from src.logger.logger import get_logger
from src.sevices.excel_service import excel_service
from src.excel.excel_manager import ExcelManager
from src.database.db_handler import insert_upload_file

logger = get_logger('API')
router = APIRouter()

# 업로드 경로
UPLOAD_PATH = os.getenv("UPLOAD_PATH", "./uploads")

# 전역 변수
stored_email = None
stored_file_id = None
stored_origin_file_name = None

class EmailData(BaseModel):
    email: str
    file_id: str = None


class ExportRequest(BaseModel):
    message: str = None
    file_id: str = None
    origin_file_name: str = None

class MeasurementData(BaseModel):
    tag_number:int
    exercise_type:str
    value:float
    timestamp:str


# ============================================
# 1. 엑셀 파일 업로드
# ============================================

@router.post("/api/upload/excel")
async def upload_excel(request: Request, file: UploadFile = File(...)):
    """학생 명단 엑셀 업로드 → DB 저장"""
    global stored_file_id, stored_origin_file_name
    form_data = await request.form()
    try:
        logger.info(f"파일 수신: {file.filename}")

        # 파일 검증
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="엑셀 파일만 업로드 가능합니다")

        stored_origin_file_name = form_data.get("origin_file_name")
        logger.info(f"UPLOAD FILE ORIGIN: {stored_origin_file_name}")

        # 파일 내용 읽기
        contents = await file.read()

        # ✅ 엑셀에서 B2 셀 (학교코드) 추출
        excel = ExcelManager(contents)
        school_code = excel.get_school_code()
        excel.close()

        # ✅ 검증 로직 추가
        validation_result = excel_service.excel_data_validate(BytesIO(contents))

        if not validation_result["valid"]:
            logger.warning(f"엑셀 검증 실패 : {validation_result}")
            raise HTTPException(
                status_code=400,
                detail={
                    "message": validation_result["message"],
                    "errors": validation_result.get("errors", [])
                }
            )

        # 파일 저장
        file_path = os.path.join(UPLOAD_PATH, file.filename)
        with open(file_path, "wb") as f:
            f.write(contents)

        logger.info(f"파일 저장: {file.filename}")

        stored_file_id = file.filename
        logger.info(f"✅ stored_file_id 저장: {stored_file_id}")

        # ✅ DB에 데이터 추가
        file_id = insert_upload_file({
            "school_code": school_code,
            "file_name": file.filename,
            "file_name_origin": stored_origin_file_name,
            "file_path": UPLOAD_PATH,
            "file_size": len(contents),
            "upload_dt": datetime.now(),
            "status": "completed"
        })

        logger.info(f"✅ DB 저장 완료, _id: {file}")

        return {
            "success": True,
            "message": "학생 명단 업로드 완료",
            "file_name": file.filename,
            "file_id": str(file_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"업로드 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# 2. 데이터 export
# ============================================

@router.post("/api/export/excel")
async def export_excel(request: Request, file: UploadFile = File(...)):
    """학생 명단 엑셀 업로드 → DB 저장"""




# ============================================
# 4. 측정값 데이터 receive
# ============================================
@router.post("/api/measure")
async def sensor_endpoint(data: MeasurementData):
    try:
        logger.info(f"Receive Data : {data}")


        # 받은 데이터 DB에 저장하는 로직

        return {
            "status" : "success",
            "message" : "측정 데이터 저장 완료 "
        }
    except Exception as e:
        logger.error(f"측정 데이터 수신 중 오류 :{str(e)}")