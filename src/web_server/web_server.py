# src/web_server/web_server.py
import uvicorn
import os
import configparser
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from src.api.api_router import router as api_router
from src.routers.upload_router import router as upload_router
from src.routers.download_router import router as download_router
from src.routers.measurement_router import router as measurement_router
from src.routers.pdf_router import router as pdf_router
from src.routers.search_router import router as search_router
from src.routers.grade_standards_router import router as grade_standards_router
from src.logger.logger import get_logger


logger = get_logger('WebServer')

# FastAPI 앱 생성
app = FastAPI(title="Digital PAPS Cloud Server")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# API 라우터 등록
#app.include_router(api_router)
app.include_router(upload_router)
app.include_router(download_router)
app.include_router(measurement_router)
app.include_router(pdf_router)
app.include_router(search_router)
app.include_router(grade_standards_router)

def load_config():
    """option.ini에서 설정 로드"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "option.ini")

    config = configparser.ConfigParser()
    config.read(config_path, encoding="utf-8")

    return {
        "server_ip": config["option"].get("server_ip", "0.0.0.0").strip('"'),
        "server_port": int(config["option"].get("server_port", "8000").strip('"')),
        "upload_path": config["option"].get("upload_path", "./uploads").strip('"'),
        "database_url": config["option"].get("database_url", "").strip('"'),
        "database_name": config["option"].get("database_name", "paps").strip('"'),
    }


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    logger.info("=" * 60)
    logger.info("🚀 웹서버 초기화 시작")
    logger.info("=" * 60)

    # 업로드 디렉토리 생성
    upload_path = os.getenv("UPLOAD_PATH", "./uploads")
    os.makedirs(upload_path, exist_ok=True)
    logger.info(f"📁 업로드 경로: {upload_path}")

    # 데이터베이스 초기화
    try:
        from src.database.db_handler import init_database
        init_database()
        logger.info("✅ 데이터베이스 초기화 완료")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 실패: {str(e)}")
        import traceback
        traceback.print_exc()

    logger.info("=" * 60)
    logger.info("✅ 웹서버 초기화 완료")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 정리"""
    logger.info("🔌 웹서버 종료 중...")


@app.get("/")
def root():
    """서버 상태 확인"""
    return {
        "status": "running",
        "service": "Digital PAPS Cloud Server",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """헬스 체크"""
    return {"status": "healthy"}


def start_web_server():
    """웹서버 시작"""
    # option.ini에서 설정 로드
    config = load_config()

    server_ip = config["server_ip"]
    server_port = config["server_port"]

    logger.info(f"웹서버 시작: {server_ip}:{server_port}")

    uvicorn.run(
        app,
        host="0.0.0.0",  # 외부 접속 허용을 위해 0.0.0.0 유지
        port=server_port,
        log_level="info",
        log_config=None
    )