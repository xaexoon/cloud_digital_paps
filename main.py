# main.py
import os
import configparser
import signal
import sys
from src.logger.logger import get_logger
from src.web_server.web_server import start_web_server

logger = get_logger('Main')


def load_config():
    """option.ini 파일 읽기"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "option.ini")

    logger.info(f"설정 파일 경로: {config_path}")

    try:
        if not os.path.exists(config_path):
            logger.error(f"설정 파일이 없습니다: {config_path}")
            return False

        config = configparser.ConfigParser()
        config.read(config_path, encoding="utf-8")

        if "option" in config:
            # 환경 변수에 저장
            os.environ["DATABASE_URL"] = config["option"]["database_url"].strip('"')
            os.environ["SERVER_PORT"] = config["option"].get("server_port", "8080").strip('"')
            os.environ["UPLOAD_PATH"] = config["option"].get("upload_path", "./uploads").strip('"')

            logger.info("=" * 60)
            logger.info(" 클라우드 서버 설정 로드 완료 ")
            logger.info(f"데이터베이스: {os.environ['DATABASE_URL']}")
            logger.info(f"서버 포트: {os.environ['SERVER_PORT']}")
            logger.info(f"업로드 경로: {os.environ['UPLOAD_PATH']}")
            logger.info("=" * 60)

            os.environ["SMTP_SERVER"] = config["option"]["smtp_server"].strip('"')
            os.environ["SMTP_PORT"] = config["option"]["smtp_port"].strip('"')
            os.environ["SENDER_EMAIL"] = config["option"]["sender_email"].strip('"')
            os.environ["SENDER_PASSWORD"] = config["option"]["sender_password"].strip('"')

            logger.info("=" * 60)
            logger.info(" SMTP 설정 로드 완료 ")
            logger.info(f" SMTP SERVER : {os.environ['SMTP_SERVER']} ")
            logger.info(f" SMTP PORT : {os.environ['SMTP_PORT']} ")
            logger.info(f" SMTP SENDER EMAIL : {os.environ['SENDER_EMAIL']} ")
            logger.info(f" SMTP SENDER PASSWORD : {os.environ['SENDER_PASSWORD']} ")
            logger.info("=" * 60)

            return True
        else:
            logger.error("[option] 섹션을 찾을 수 없습니다")
            return False

    except Exception as e:
        logger.error(f"설정 파일 읽기 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def signal_handler(sig, frame):
    """Ctrl+C 처리"""
    logger.info("\n\n클라우드 서버 종료 신호 받음...")
    logger.info("서버 종료 완료")
    sys.exit(0)


if __name__ == "__main__" :
    # 설정 파일 로드
    if not load_config():
        logger.error("설정 파일 로드 실패. 프로그램을 종료합니다.")
        sys.exit(1)

    # Ctrl+C 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)

    logger.info("=" * 60)
    logger.info("☁️ 클라우드 서버 시작")
    logger.info("=" * 60)

    # 웹서버 시작 (블로킹)
    start_web_server()