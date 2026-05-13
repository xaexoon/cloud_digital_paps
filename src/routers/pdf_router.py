"""PDF 출력 API 라우터"""

import os
import zipfile
from io import BytesIO
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from src.logger.logger import get_logger
from src.models.request_model import PdfSearchRequest
from src.services.pdf_export_service import pdf_export_service
from src.database.db_handler import get_db, get_users_by_school, get_measurements_by_user

logger = get_logger('PdfRouter')
router = APIRouter(prefix="/api/pdf", tags=["PDF"])


@router.post("")
async def print_individual_pdf(request: PdfSearchRequest):
    """개인 PDF 출력 - 태그번호로 조회"""
    try:
        logger.info(
            f"PDF 생성 요청: tag_number={request.tag_number}, "
            f"school_code={request.school_code}, date={request.measure_date}, "
            f"agility={request.agility_exercise}, muscle={request.muscle_exercise}"
        )

        # 1. 학생 검색
        db = get_db()
        query = {"tag_number": str(request.tag_number)}
        if request.school_code:
            query["school_code"] = request.school_code

        user = db.user_info.find_one(query)
        if not user:
            raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다.")

        logger.info(f"학생 조회 완료: {user['name']}, tag_number: {user['tag_number']}")

        # 2. 측정 데이터 검색
        measurement = get_measurements_by_user(
            tag_number=user["tag_number"],
            age=user["age"],
            measure_date=request.measure_date
        )
        if not measurement:
            raise HTTPException(status_code=404, detail="측정 데이터를 찾을 수 없습니다.")

        logger.info(f"측정 데이터 조회 완료")

        # 3. PDF 생성 (★ 대표종목 전달)
        output_path = pdf_export_service.generate_pdf(
            user,
            measurement,
            agility_exercise=request.agility_exercise,
            muscle_exercise=request.muscle_exercise,
        )
        logger.info(f"PDF 생성 완료: {output_path}")

        # 4. 파일 응답
        return FileResponse(
            path=output_path,
            filename=f"{user['name']}_PAPS결과지.pdf",
            media_type="application/pdf"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF 생성 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all/{school_code}/{measure_date}")
async def print_all_pdf(school_code: str, measure_date: str):
    """전체 학생 PDF 출력 - ZIP으로 다운로드"""
    try:
        logger.info(f"전체 PDF 생성 요청: school_code={school_code}, date={measure_date}")

        # 1. 해당 학교 학생 조회
        users = get_users_by_school(school_code)
        if not users:
            raise HTTPException(status_code=404, detail="해당 학교의 학생 정보가 없습니다")

        # 2. ZIP 파일 생성
        zip_buffer = BytesIO()
        pdf_count = 0

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for user in users:
                # 3. 각 학생의 측정 데이터 조회
                measurement = get_measurements_by_user(
                    tag_number=user["tag_number"],
                    age=user["age"],
                    measure_date=measure_date
                )

                if not measurement:
                    logger.warning(f"측정 데이터 없음: {user['name']}")
                    continue

                # 4. PDF 생성 및 ZIP에 추가
                output_path, filename = pdf_export_service.generate_pdf_bytes(user, measurement)
                zip_file.write(output_path, filename)
                pdf_count += 1

                # 임시 파일 삭제
                os.remove(output_path)

        if pdf_count == 0:
            raise HTTPException(
                status_code=404,
                detail="생성할 PDF가 없습니다. 측정 데이터를 확인해주세요."
            )

        zip_buffer.seek(0)
        logger.info(f"전체 PDF 생성 완료: {pdf_count}명")

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=PAPS_results_{measure_date}.zip"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"전체 PDF 생성 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))