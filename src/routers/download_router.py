"""엑셀 다운로드 API 라우터"""

import os
import configparser
from io import BytesIO
from urllib.parse import quote
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from src.logger.logger import get_logger
from src.services.excel_export_service import excel_export_service
from src.database.db_handler import get_users_by_school, get_measurements_by_tags

logger = get_logger('DownloadRouter')
router = APIRouter(prefix="/api/download", tags=["Download"])


def get_upload_path():
    """option.ini에서 upload_path 읽기"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "option.ini")

    config = configparser.ConfigParser()
    config.read(config_path, encoding="utf-8")

    return config["option"].get("upload_path", "./uploads").strip('"')


UPLOAD_PATH = get_upload_path()


@router.get("/excel/{school_code}/{file_name}")
async def download_excel(school_code: str, file_name: str):
    """업로드한 원본 엑셀에 측정 데이터 채워서 다운로드"""
    try:
        # 1. 원본 파일 확인
        file_path = os.path.join(UPLOAD_PATH, file_name)
        logger.info(f"다운로드 경로: {file_path}")

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")

        wb = excel_export_service.load_workbook(file_path)

        # 2. 학생 정보 조회
        users = get_users_by_school(school_code)
        if not users:
            raise HTTPException(status_code=404, detail="해당 학교의 학생 정보가 없습니다")

        tag_numbers = [str(user["tag_number"]) for user in users]
        logger.info(f"학교 {school_code}의 학생 수: {len(tag_numbers)}명")

        # 3. 매핑 생성
        ws_value = wb["기본-1"]
        tag_to_user, number_to_tag = excel_export_service.build_tag_mappings(ws_value, users)

        # 4. 측정일 읽기
        target_date = excel_export_service.get_measure_date(ws_value)
        logger.info(f"엑셀 측정일: {target_date}")

        # 5. 측정 데이터 조회 및 정리
        measurements = get_measurements_by_tags(tag_numbers, target_date)
        measurement_dict = excel_export_service.organize_measurement_data(measurements)
        logger.info(f"측정 데이터: {len(measurement_dict)}명")

        # 6. 기본-1 시트 채우기
        excel_export_service.fill_basic1_sheet(ws_value, measurement_dict)

        # 7. 기본-2 시트 채우기
        if "기본-2" in wb.sheetnames:
            ws_grade = wb["기본-2"]
            excel_export_service.fill_basic2_sheet(ws_value, ws_grade, measurement_dict)

        # 8. 나이스 양식 시트 채우기
        if "나이스 양식" in wb.sheetnames:
            ws_neis = wb["나이스 양식"]
            excel_export_service.fill_neis_sheet(ws_neis, number_to_tag, tag_to_user, measurement_dict)

        # 9. 응답 생성
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        wb.close()

        original_filename = file_name.split('_', 1)[-1] if '_' in file_name else file_name

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{quote(original_filename)}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"다운로드 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))