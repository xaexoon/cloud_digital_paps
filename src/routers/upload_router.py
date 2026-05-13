
import os
import configparser
from io import BytesIO
from fastapi import APIRouter, UploadFile, File, HTTPException, Request

from src.logger.logger import get_logger
from src.services.excel_service import excel_service
from src.database.db_handler import insert_upload_file, insert_user_info_many

logger = get_logger('UploadRouter')
router = APIRouter(prefix="/api/upload", tags=["Upload"])


def get_upload_path():
    """option.ini에서 upload_path 읽기"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "option.ini")

    config = configparser.ConfigParser()
    config.read(config_path, encoding="utf-8")

    return config["option"].get("upload_path", "./uploads").strip('"')


UPLOAD_PATH = get_upload_path()

@router.post("/excel")
async def upload_excel(request: Request, file: UploadFile = File(...)):
    """학생 명단 엑셀 업로드 → DB 저장"""
    try:
        logger.info(f"파일 수신: {file.filename}")
        logger.info(f"업로드 경로: {UPLOAD_PATH}")

        # 파일 검증
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(status_code=400, detail="엑셀 또는 CSV 파일만 업로드 가능합니다")

        contents = await file.read()
        file_bytes = BytesIO(contents)

        # ★ 학교정보 업데이트 파일 분기
        name_without_ext = os.path.splitext(file.filename)[0]
        if name_without_ext == "학교정보_업데이트":
            result = excel_service.handle_upload(file_bytes, file.filename)
            if not result.get("success"):
                raise HTTPException(status_code=400, detail=result.get("message", "업데이트 실패"))
            return result

        # 1. 엑셀 검증
        validation_result = excel_service.excel_data_validate(file_bytes, file.filename)
        file_bytes.seek(0)

        if not validation_result["valid"]:
            logger.warning(f"엑셀 검증 실패 : {validation_result}")
            raise HTTPException(
                status_code=400,
                detail={
                    "message": validation_result["message"],
                    "errors": validation_result.get("errors", [])
                }
            )

        # 2. user_info 데이터 추출 및 저장
        user_data = excel_service.extract_user_data(file_bytes, file.filename)
        file_bytes.seek(0)

        if not user_data["success"]:
            raise HTTPException(status_code=400, detail=user_data["message"])

        if user_data["users"]:
            insert_user_info_many(user_data["users"])
            logger.info(f"✅ user_info 저장 완료: {user_data['count']}명")

        # 3. upload_files 기록 생성 및 저장
        upload_data = excel_service.create_upload_record(file_bytes, file.filename)
        file_bytes.seek(0)

        if not upload_data["success"]:
            raise HTTPException(status_code=400, detail=upload_data["message"])

        file_id = insert_upload_file(upload_data["record"])
        logger.info(f"✅ upload_files 저장 완료, _id: {file_id}")

        # 4. 파일 저장
        os.makedirs(UPLOAD_PATH, exist_ok=True)
        saved_filename = upload_data["record"]["file_name"]
        file_path = os.path.join(UPLOAD_PATH, saved_filename)
        with open(file_path, "wb") as f:
            f.write(contents)
        logger.info(f"✅ 파일 저장: {file_path}")

        return {
            "success": True,
            "message": "학생 명단 업로드 완료",
            "file_name": saved_filename,
            "file_id": str(file_id),
            "user_count": user_data["count"],
            "school_code": upload_data["record"]["school_code"],
            "measure_date": validation_result["meta_data"]["측정일"].strftime("%Y-%m-%d")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"업로드 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))