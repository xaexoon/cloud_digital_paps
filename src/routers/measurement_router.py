"""측정 데이터 API 라우터"""

from fastapi import APIRouter, HTTPException

from src.logger.logger import get_logger
from src.models.request_model import MeasurementData
from src.database.db_handler import insert_measurement

logger = get_logger('MeasurementRouter')
router = APIRouter(prefix="/api", tags=["Measurement"])


@router.post("/measure")
async def receive_measurement(data: MeasurementData):
    """측정값 데이터 수신 (프론트에서 받은 값 그대로 저장)"""
    try:
        logger.info(f"📥 Receive Data: {data}")

        data_dict = data.dict(exclude_none=True)

        logger.info(
            f"📊 저장 데이터: exercise_type={data_dict.get('exercise_type')}, "
            f"value={data_dict.get('value')}, grade={data_dict.get('grade')}"
        )

        result = insert_measurement(data_dict)

        if result:
            return {
                "status": "success",
                "message": "측정 데이터 저장 완료",
                "action": result.get("action"),
                "id": result.get("id")
            }
        else:
            raise HTTPException(status_code=500, detail="DB 저장 실패")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 측정 데이터 수신 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))