import io
import csv
from src.logger.logger import get_logger
from src.database.db_handler import get_db

logger = get_logger("School_Info_Update")


class SchoolInfoUpdateService:

    def __init__(self):
        pass

    def process(self, file):
        """
        학교정보 CSV 파일을 읽어 DB와 비교 후 업데이트
        - 새 파일에만 있는 학교 → 추가
        - 이름이 바뀐 학교 → 수정
        - 새 파일에 없는 학교 → 삭제
        - 중간 오류 시 백업 데이터로 복원
        """
        self.collection = get_db()["school_info"]
        try:
            logger.info("학교정보 업데이트 시작")

            file_content = file.read()
            file.seek(0)

            # ── 1. CSV 파싱 ──
            new_schools = self._parse_csv(file_content)

            if not new_schools:
                return {
                    "success": False,
                    "message": "유효한 학교 데이터가 없습니다"
                }

            # ── 2. 기존 DB 데이터 조회 ──
            existing = {
                doc["code"]: doc["name"]
                for doc in self.collection.find({}, {"_id": 0, "code": 1, "name": 1})
            }

            # ── 3. 비교 ──
            new_map = {s["code"]: s["name"] for s in new_schools}

            to_add = []
            to_modify = []
            to_delete = []

            for code, name in new_map.items():
                if code not in existing:
                    to_add.append({"code": code, "name": name})
                elif existing[code] != name:
                    to_modify.append({"code": code, "before": existing[code], "after": name})

            for code, name in existing.items():
                if code not in new_map:
                    to_delete.append({"code": code, "name": name})

            # ── 4. 백업 (메모리) ──
            backup = [
                {"code": doc["code"], "name": doc["name"]}
                for doc in self.collection.find({}, {"_id": 0, "code": 1, "name": 1})
            ]

            # ── 5. DB 반영 ──
            try:
                if to_add:
                    self.collection.insert_many([
                        {"code": s["code"], "name": s["name"]} for s in to_add
                    ])

                for item in to_modify:
                    self.collection.update_one(
                        {"code": item["code"]},
                        {"$set": {"name": item["after"]}}
                    )

                if to_delete:
                    delete_codes = [s["code"] for s in to_delete]
                    self.collection.delete_many({"code": {"$in": delete_codes}})

            except Exception as e:
                # ── 6. 오류 발생 → 백업으로 복원 ──
                logger.error(f"DB 반영 중 오류 발생, 복원 시작: {str(e)}")
                self._restore_backup(backup)
                return {
                    "success": False,
                    "message": f"업데이트 중 오류가 발생하여 복원되었습니다: {str(e)}"
                }

            logger.info(
                f"업데이트 완료 - 추가: {len(to_add)}, "
                f"수정: {len(to_modify)}, 삭제: {len(to_delete)}"
            )

            return {
                "success": True,
                "message": "학교정보 업데이트 완료",
                "added": to_add,
                "modified": to_modify,
                "deleted": to_delete,
                "unchanged": len(new_map) - len(to_add) - len(to_modify)
            }

        except Exception as e:
            logger.error(f"학교정보 업데이트 오류: {str(e)}")
            return {
                "success": False,
                "message": f"학교정보 업데이트 오류: {str(e)}"
            }

    def _restore_backup(self, backup):
        """기존 데이터 전체 삭제 후 백업 데이터로 복원"""
        try:
            self.collection.delete_many({})
            if backup:
                self.collection.insert_many(backup)
            logger.info(f"백업 복원 완료: {len(backup)}건")
        except Exception as e:
            logger.error(f"백업 복원 실패: {str(e)}")

    def _parse_csv(self, file_content: bytes) -> list:
        """CSV 바이트 → 학교 리스트 파싱"""
        for encoding in ["cp949", "euc-kr", "utf-8"]:
            try:
                text = file_content.decode(encoding)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        else:
            raise ValueError("CSV 파일 인코딩을 인식할 수 없습니다")

        schools = []
        reader = csv.DictReader(io.StringIO(text))

        # ★ 디버깅: 실제 컬럼명 로그 출력
        logger.info(f"CSV 컬럼명: {reader.fieldnames}")

        for row in reader:
            code_str = (row.get("표준학교코드") or row.get("행정표준코드") or "").strip()
            name = row.get("학교명", "").strip()

            if not code_str or not name:
                continue

            try:
                code = int(code_str)
            except ValueError:
                logger.warning(f"[학교정보] 숫자가 아닌 코드 건너뜀: {code_str} ({name})")
                continue

            schools.append({
                "code": code,
                "name": name,
            })

        logger.info(f"파싱된 학교 수: {len(schools)}")
        return schools