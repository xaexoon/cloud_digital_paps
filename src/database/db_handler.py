import os

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from src.logger.logger import get_logger

logger = get_logger("Database")

mongo_client = None
db = None

db_name = "paps"
measurement_collect_name = "measurement_data"
upload_files_collect_name = "upload_files"
user_info_collect_name = "user_info"  # 추가



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


def insert_user_info_many(users: list):
    """user_info 여러 명 upsert (tag_number 기준)"""
    try:
        use_db = mongo_client["paps"]
        use_collection = use_db[user_info_collect_name]

        upserted = 0
        for user in users:
            use_collection.update_one(
                {"tag_number": user["tag_number"]},  # 조건
                {"$set": user},                       # 업데이트
                upsert=True                           # 없으면 insert
            )
            upserted += 1

        logger.info(f"✅ user_info upsert 완료: {upserted}명")
        return upserted

    except Exception as e:
        logger.error(f"❌ user_info 저장 오류: {str(e)}")
        return None


def init_database():
    global mongo_client, db

    try:
        database_url = os.getenv("DATABASE_URL", "mongodb://localhost:27017/")
        database_name = os.getenv("DATABASE_NAME", "paps")

        logger.info(f"MongoDB 연결 : {database_url}")

        mongo_client = MongoClient(database_url, serverSelectionTimeoutMS=5000)
        mongo_client.admin.command("ping")

        db = mongo_client[database_name]

        logger.info(f"MongoDB 연결 성공 : {database_name}")

        db.user_info.create_index("tag_number", unique=True)
        db.measurement_data.create_index("tag_number")

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


def find_school_seq(school_name: str):
    try:
        use_db = mongo_client["paps"]
        school_info = use_db["school_info"]

        result = school_info.find_one({"school_name": school_name})

        if result:
            logger.info(f"학교 찾음 : {school_name} -> {result['school_seq']}")
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

def get_users_by_school(school_code: str):
    """학교별 학생 조회"""
    try:
        use_db = mongo_client["paps"]
        return list(use_db.user_info.find({"school_code": school_code}))
    except Exception as e:
        logger.error(f"❌ 학생 조회 오류: {str(e)}")
        return []

def get_measurements_by_school(school_code: str):
    """학교별 측정 데이터 조회"""
    try:
        use_db = mongo_client["paps"]
        return list(use_db.measurement_data.find({"school_code": school_code}))
    except Exception as e:
        logger.error(f"❌ 측정 데이터 조회 오류: {str(e)}")
        return []


def get_measurements_by_tags(tag_numbers: list, target_date=None):
    """태그번호 목록으로 측정 데이터 조회 (최신값만)"""
    try:
        use_db = mongo_client["paps"]

        tag_numbers_str = [str(tag) for tag in tag_numbers]

        query = {"tag_number": {"$in": tag_numbers_str}}

        # 날짜 필터 추가
        if target_date:
            from datetime import datetime, timedelta

            date_str = target_date.strftime("%Y-%m-%d")

            if hasattr(target_date, 'year') and not hasattr(target_date, 'hour'):
                start_dt = datetime.combine(target_date, datetime.min.time())
                end_dt = datetime.combine(target_date, datetime.max.time())
            else:
                start_dt = target_date
                end_dt = target_date + timedelta(days=1)

            query["$or"] = [
                {"timestamp": {"$regex": f"^{date_str}"}},
                {"measured_dt": {"$gte": start_dt, "$lt": end_dt}}
            ]

        result = list(use_db.measurement_data.find(query).sort("timestamp", -1))

        latest_data = {}
        for item in result:
            key = f"{item['tag_number']}_{item['exercise_type']}"
            if key not in latest_data:
                latest_data[key] = item

        final_result = list(latest_data.values())
        logger.info(f"✅ 측정 데이터 조회: {len(final_result)}건 (태그 {len(tag_numbers)}개)")

        return final_result

    except Exception as e:
        logger.error(f"❌ 측정 데이터 조회 오류: {str(e)}")
        return []

def get_school_code_by_name(school_name):
    """학교명으로 school_code 조회"""
    if not school_name:
        return None

    school = db.school_info.find_one(
        {"name": {"$regex": school_name, "$options": "i"}}
    )

    if school:
        return str(school.get("code"))  # code를 문자열로 변환 (user_info의 school_code가 문자열이므로)
    return None


def get_user_by_search(school_name=None, grade_year=None, class_number=None, student_number=None, student_name=None):
    """검색 조건으로 학생 조회"""
    query = {}

    # school_name → school_code 변환
    if school_name:
        school_code = get_school_code_by_name(school_name)
        if school_code:
            query["school_code"] = school_code

    if grade_year:
        query["grade_year"] = int(grade_year)
    if class_number:
        query["class_number"] = int(class_number)
    if student_number:
        query["student_number"] = int(student_number)
    if student_name:
        query["name"] = {"$regex": student_name, "$options": "i"}

    return db.user_info.find_one(query)


def get_measurements_by_user(tag_number, age, measure_date=None):
    """학생의 모든 측정 데이터 조회 (종목별로 합치기)"""
    query = {
        "tag_number": str(tag_number),
    }

    if measure_date:
        # 측정일 필터
        from datetime import datetime, timedelta
        target_date = datetime.strptime(measure_date, "%Y-%m-%d")
        next_date = target_date + timedelta(days=1)

        # 날짜 범위로 조회 (하루 전체)
        query["measured_dt"] = {
            "$gte": target_date,
            "$lt": next_date
        }

    # 해당 학생의 모든 측정 데이터 조회
    measurements = list(db.measurement_data.find(query))

    if not measurements:
        return None

    # 종목별로 데이터 합치기
    result = {
        "tag_number": tag_number,
        "age": age,
        "gender": measurements[0].get("gender", ""),
        "measured_dt": measurements[0].get("measured_dt"),
    }

    for m in measurements:
        m_type = m["exercise_type"]
        result[m_type] = m.get("value")
        result[f"grade_{m_type}"] = m.get("grade")
        result[f"score_{m_type}"] = m.get("score")

        # 악력: right, left 별도 저장
        if m_type == "gripStrength":
            result["gripStrength"] = {
                "rightGrip": m.get("right", 0),
                "leftGrip": m.get("left", 0)
            }
            result["grade_gripStrength"] = {
                "rightGrip": m.get("right_grade"),
                "leftGrip": m.get("left_grade")
            }

        # 신체측정: height, weight 별도 저장
        if m_type == "bodyMeasurement":
            result["height"] = m.get("height", 0)
            result["weight"] = m.get("weight", 0)

    return result


# db_handler.py에 추가할 함수

def insert_measurement(data: dict):
    """
    측정 데이터 저장 (insert or update)

    조건: tag_number + exercise_type + 날짜(시간 무시)
    - 일치하면 update
    - 없으면 insert
    """
    try:
        use_db = mongo_client[db_name]
        use_collection = use_db[measurement_collect_name]

        from datetime import datetime

        # measured_dt 처리
        measured_dt = data.get("measured_dt")
        if isinstance(measured_dt, str):
            measured_dt = datetime.fromisoformat(measured_dt.replace("Z", "+00:00"))
        elif measured_dt is None:
            measured_dt = datetime.now()

        # data에 measured_dt 반영
        data["measured_dt"] = measured_dt

        # 날짜 범위 (같은 날짜인지 비교)
        start_of_day = measured_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = measured_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

        # 조건: tag_number + exercise_type + 같은 날짜
        query = {
            "tag_number": data.get("tag_number"),
            "exercise_type": data.get("exercise_type"),
            "measured_dt": {"$gte": start_of_day, "$lte": end_of_day}
        }

        existing = use_collection.find_one(query)

        if existing:
            # Update (기존 데이터 덮어쓰기)
            result = use_collection.update_one(
                {"_id": existing["_id"]},
                {"$set": data}
            )
            logger.info(f"✅ 측정 데이터 업데이트: tag={data.get('tag_number')}, type={data.get('exercise_type')}")
            return {"action": "update", "id": str(existing["_id"])}
        else:
            # Insert (새로 추가)
            result = use_collection.insert_one(data)
            logger.info(
                f"✅ 측정 데이터 저장: tag={data.get('tag_number')}, type={data.get('exercise_type')}, _id={result.inserted_id}")
            return {"action": "insert", "id": str(result.inserted_id)}

    except Exception as e:
        logger.error(f"❌ 측정 데이터 저장 오류: {str(e)}")
        return None


def search_schools(keyword: str, limit: int = 20):
    """학교명 검색 (school_info에서 조회)"""
    try:
        use_db = mongo_client["paps"]

        results = list(
            use_db.school_info.find(
                {"name": {"$regex": keyword, "$options": "i"}},
                {"_id": 0, "code": 1, "name": 1}
            ).sort("name", 1).limit(limit)
        )

        # 프론트 필드명 맞추기
        schools = [
            {"school_code": str(r["code"]), "school_name": r["name"]}
            for r in results
        ]

        logger.info(f"🔍 학교 검색 '{keyword}': {len(schools)}건")
        return schools

    except Exception as e:
        logger.error(f"❌ 학교 검색 오류: {str(e)}")
        return []


def get_measure_dates(school_code: str):
    """학교별 측정일 목록 조회 (measurement_data에서)"""
    try:
        use_db = mongo_client["paps"]

        # 해당 학교 학생들의 tag_number 목록
        tag_numbers = use_db.user_info.distinct(
            "tag_number",
            {"school_code": school_code}
        )

        if not tag_numbers:
            return []

        # measurement_data에서 해당 학생들의 측정일 목록 (중복 제거)
        pipeline = [
            {"$match": {"tag_number": {"$in": tag_numbers}}},
            {"$project": {
                "date_str": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$measured_dt"}
                }
            }},
            {"$group": {"_id": "$date_str"}},
            {"$sort": {"_id": -1}}
        ]

        results = list(use_db.measurement_data.aggregate(pipeline))
        dates = [r["_id"] for r in results if r["_id"]]

        logger.info(f"📅 측정일 조회 (school_code={school_code}): {len(dates)}건")
        return dates

    except Exception as e:
        logger.error(f"❌ 측정일 조회 오류: {str(e)}")
        return []