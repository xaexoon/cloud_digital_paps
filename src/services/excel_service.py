import io
import uuid
from datetime import datetime
import pandas as pd
import os
from src.logger.logger import get_logger
from src.services.excel_school_info_update import SchoolInfoUpdateService

logger = get_logger("Excel_Service")

# ─── 학교정보 업데이트 트리거 파일명 ───
SCHOOL_UPDATE_TRIGGER = "학교정보_업데이트"


class ExcelService:

    def __init__(self):
        self.school_update_service = SchoolInfoUpdateService()

    # ================================================================
    #  ★ CSV / Excel 분기 헬퍼
    # ================================================================
    def _read_file(self, file_content, filename=None, **kwargs):
        """파일 확장자에 따라 Excel 또는 CSV로 읽기"""
        if filename and filename.lower().endswith('.csv'):
            return pd.read_csv(io.BytesIO(file_content), **kwargs)
        else:
            return pd.read_excel(io.BytesIO(file_content), **kwargs)

    # ================================================================
    #  파일명 체크 → 분기 처리
    # ================================================================
    def handle_upload(self, file, original_filename):
        """
        업로드 진입점
        - 파일명이 "학교정보_업데이트"이면 → 학교정보 DB 업데이트
        - 그 외 → 기존 엑셀 검증/처리 로직
        """
        name_without_ext = os.path.splitext(original_filename)[0]

        if name_without_ext == SCHOOL_UPDATE_TRIGGER:
            logger.info(f"[학교정보 업데이트] 트리거 파일 감지: {original_filename}")
            return self.school_update_service.process(file)

        # ── 기존 로직 ──
        logger.info(f"[일반 업로드] 파일: {original_filename}")
        return self._handle_normal_upload(file, original_filename)

    def _handle_normal_upload(self, file, original_filename):
        """기존 엑셀 업로드 처리 (검증 → 추출 → 기록)"""
        # 1. 검증
        validation = self.excel_data_validate(file, original_filename)
        if not validation["valid"]:
            return validation

        # 2. 데이터 추출
        user_data = self.extract_user_data(file, original_filename)
        if not user_data["success"]:
            return user_data

        # 3. 업로드 기록 생성
        upload_record = self.create_upload_record(file, original_filename)

        return {
            "success": True,
            "validation": validation,
            "user_data": user_data,
            "upload_record": upload_record
        }

    # ================================================================
    #  기존 메서드들 (CSV 지원 추가)
    # ================================================================

    def excel_data_validate(self, file, filename=None):
        """엑셀/CSV 파일 검증"""
        try:
            logger.info("파일 검증 시작")
            if not file:
                logger.error("파일이 존재하지 않습니다")
                raise FileNotFoundError("파일이 존재하지 않습니다")

            file_content = file.read()
            file.seek(0)

            df_raw = self._read_file(file_content, filename, header=None, nrows=8)

            # 검증 항목
            required_fields = {
                0: "학교명",
                1: "학교코드",
                2: "학년",
                3: "반",
                4: "나이",
                5: "작성자명",
                6: "측정일"
            }

            errors = []
            meta_data = {}

            # ============= 상단 필수 정보 검증 =============
            for row_idx, field_name in required_fields.items():
                if df_raw.iloc[row_idx, 0] != field_name:
                    errors.append(f"'{field_name}' 필드가 없습니다")
                    continue

                value = df_raw.iloc[row_idx, 1]
                if pd.isna(value) or str(value).strip() == '':
                    errors.append(f"'{field_name}' 값이 없습니다")
                else:
                    meta_data[field_name] = value

            # ============= 태그번호, 이름 검증 =============
            df_data = self._read_file(file_content, filename, header=8)

            if "태그번호" not in df_data.columns or "이름" not in df_data.columns:
                errors.append("'태그번호' 또는 '이름' 컬럼이 없습니다")
            else:
                invalid_rows = []
                tag_numbers = []

                for idx, row in df_data.iterrows():
                    tag = row["태그번호"]
                    name = row["이름"]

                    tag_exists = pd.notna(tag) and str(tag).strip() != ''
                    name_exists = pd.notna(name) and str(name).strip() != ''

                    row_num = idx + 10

                    if not tag_exists and not name_exists:
                        continue

                    if tag_exists and not name_exists:
                        invalid_rows.append(f"{row_num}행 : 태그번호는 있으나 이름이 없습니다")
                    elif name_exists and not tag_exists:
                        invalid_rows.append(f"{row_num}행 : 이름은 있으나 태그번호가 없습니다")
                    else:
                        tag_str = str(tag).strip()
                        if tag_str in tag_numbers:
                            invalid_rows.append(f"{row_num}행 : 태그번호 '{tag_str}'가 중복됩니다")
                        else:
                            tag_numbers.append(tag_str)

                if invalid_rows:
                    errors.extend(invalid_rows)

                valid_data = df_data[
                    df_data["태그번호"].notna() & df_data["이름"].notna()
                ]

                if valid_data.empty:
                    errors.append("유효한 학생 데이터가 없습니다")

            if errors:
                logger.warning(f"검증 실패: {errors}")
                return {
                    "valid": False,
                    "message": "필수 정보가 누락되었습니다",
                    "errors": errors
                }

            logger.info(f"검증 성공 : {meta_data}")
            return {
                "valid": True,
                "message": "검증 성공",
                "meta_data": meta_data
            }

        except Exception as e:
            logger.error(f"파일 읽기 오류: {str(e)}")
            return {
                "valid": False,
                "message": f"파일 읽기 오류: {str(e)}"
            }

    def extract_user_data(self, file, filename=None):
        """엑셀/CSV에서 user_info 데이터 추출"""
        try:
            file_content = file.read()
            file.seek(0)

            df_raw = self._read_file(file_content, filename, header=None, nrows=8)
            school_code = str(df_raw.iloc[1, 1]).strip()
            grade_year = int(df_raw.iloc[2, 1])
            class_number = int(df_raw.iloc[3, 1])
            age = int(df_raw.iloc[4, 1])

            df_data = self._read_file(file_content, filename, header=8)

            users = []
            for idx, row in df_data.iterrows():
                number = row.get("번호")
                tag = row.get("태그번호")
                name = row.get("이름")
                gender = row.get("성별", None)

                tag_exists = pd.notna(tag) and str(tag).strip() != ''
                name_exists = pd.notna(name) and str(name).strip() != ''

                if tag_exists and name_exists:
                    user = {
                        "school_code": school_code,
                        "tag_number": str(int(float(tag))),
                        "student_number": int(float(number)) if pd.notna(number) else None,
                        "name": str(name).strip(),
                        "grade_year": grade_year,
                        "class_number": class_number,
                        "age": age,
                        "gender": str(gender).strip() if pd.notna(gender) else None,
                        "created_dt": datetime.now()
                    }
                    users.append(user)

            return {
                "success": True,
                "users": users,
                "count": len(users)
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"데이터 추출 오류: {str(e)}"
            }

    def create_upload_record(self, file, original_filename):
        """upload_files 기록 생성"""
        try:
            file_content = file.read()
            file.seek(0)

            df_raw = self._read_file(file_content, original_filename, header=None, nrows=8)
            school_code = str(df_raw.iloc[1, 1]).strip()

            df_data = self._read_file(file_content, original_filename, header=8)
            valid_count = df_data[
                df_data["태그번호"].notna() & df_data["이름"].notna()
            ].shape[0]

            file_uuid = str(uuid.uuid4())
            file_ext = os.path.splitext(original_filename)[1]
            new_filename = f"{file_uuid}{file_ext}"

            upload_record = {
                "school_code": school_code,
                "file_name": new_filename,
                "file_name_origin": original_filename,
                "upload_dt": datetime.now(),
                "status": "completed",
                "record_count": valid_count
            }

            return {
                "success": True,
                "record": upload_record
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"업로드 기록 생성 오류: {str(e)}"
            }
excel_service = ExcelService()