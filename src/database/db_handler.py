import os

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from src.logger.logger import get_logger

logger = get_logger("Database")

mongo_client = None
db = None

db_name="paps"
measurement_collect_name="measurement_data"
upload_files_collect_name = "upload_files"


def insert_upload_file(file_data: dict):
    """업로드 파일 정보 DB 저장"""
    try:
        use_db = mongo_client["paps"]
        use_collection = use_db[upload_files_collect_name]

        result = use_collection.insert_one(file_data)
        logger.info(f"✅ 파일 정보 저장 완료, _id: {result.inserted_id}")

        return result.inserted_id

    except Exception as e:
        logger.error(f"❌ 파일 정보 저장 오류: {str(e)}")
        return None

def init_database():
    global mongo_client, db

    try :
        database_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017/")
        database_name = os.getenv("DATABASE_NAME", "digital_paps")

        logger.info(f"MongoDB 연결 : {database_url}")

        mongo_client = MongoClient(database_url, serverSelectionTimeoutMS=5000)
        mongo_client.admin.command("ping")

        db = mongo_client[database_name]

        logger.info(f"MongoDB 연결 성공 : {database_name}")

        db.students.create_index("tag_number", unique=True)
        db.measurement.create_index("tag_number")

        return True

    except ConnectionFailure as e:
        logger.error(f"❌ MongoDB 연결 실패: {str(e)}")
        return False

    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def get_db():
    global db
    if db is None:
        init_database()
    return db

def find_school_seq(school_name : str):
    try:
        paps_test_db = mongo_client["paps_test"]
        school_info = paps_test_db["school_info"]

        result = school_info.find_one({"school_name":school_name})

        if result:
            logger.info(f"학교 찾음 : {school_name} -> {result['school_seq']}" )
            return result["school_seq"]
        else:
            logger.warning(f"학교를 찾을 수 없음 : {school_name}")
            return None

    except Exception as e:
        logger.error(f"school_seq 조회 오류 : {str(e)}")
        return None

def close_database():
    global mongo_client
    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB 연결 종료")


def insert_data(data):
    use_db = mongo_client[db_name]
    use_collection = use_db[measurement_collect_name]


