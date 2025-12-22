"""
Logger.py
프로그램별로 로그를 남기는 간단한 로깅 시스템
"""
import logging
import logging.handlers
import os


def get_logger(program_name, log_dir="logs/temp", log_level=logging.INFO):

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(program_name)

    if logger.handlers:
        return logger

    logger.setLevel(log_level)

    formatter = logging.Formatter(
        f"[%(asctime)s] [{program_name}] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    log_file = os.path.join(log_dir, f"{program_name}.log")
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_file,
        when='midnight',
        interval=1,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 부모 로거로 전파 방지 (중복 로그 방지)
    logger.propagate = False

    return logger