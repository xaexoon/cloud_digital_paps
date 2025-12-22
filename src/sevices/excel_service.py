import io

import pandas as pd
import os


class ExcelService():


    def excel_data_validate(self, file):
        try:

            if not file :
                raise FileNotFoundError(f"파일이 존재하지 않습니다")

            file_content = file.read()
            file.seek(0)

            df_raw = pd.read_excel(io.BytesIO(file_content), header=None, nrows=6)

            required_fields = {
                0: "학교명",
                1: "학년",
                2: "반",
                3: "작성자명",
                4: "측정일"
            }

            errors = []
            meta_data = {}
            # ============= 상단 필수 정보 검증 =============
            for row_idx, field_name in required_fields.items():
                if df_raw.iloc[row_idx,0] != field_name :
                    errors.append(f"'{field_name}' 필드가 없습니다")
                    continue

                value = df_raw.iloc[row_idx, 1]
                if pd.isna(value) or str(value).strip() == '':
                    errors.append(f"'{field_name}' 값이 없습니다")
                else:
                    meta_data[field_name] = value


            # ============= 태그번호, 이름 검증 =============

            df_data = pd.read_excel(io.BytesIO(file_content), header=6)

            if "태그번호" not in df_data.columns or "이름" not in df_data.columns:
                errors.append("'태그번호' 또는 '이름' 컬럼이 없습니다")
            else:
                invalid_rows = []

                for idx, row in df_data.iterrows():
                    tag = row["태그번호"]
                    name = row["이름"]

                    tag_exists = pd.notna(tag) and str(tag).strip() != ''
                    name_exists = pd.notna(name) and str(name).strip() != ''

                    row_num = idx + 8

                    if tag_exists and not name_exists :
                        invalid_rows.append(f"{row_num} 행 : 태그번호는 있으나 이름이 없습니다")
                    elif name_exists and not tag_exists:
                        invalid_rows.append(f"{row_num} 행 : 이름은 있으나 태그번호가 없습니다")

                if invalid_rows:
                    errors.extend(invalid_rows)

                valid_data = df_data[
                    df_data["태그번호"].notna(),
                    df_data["이름"].notna(),
                ]
                if valid_data.empty:
                    errors.append("유효한 학생 데이터가 없습니다 (태그번호와 이름이 모두 입력된 행이 없음)")

            if errors:
                return {
                    "valid": False,
                    "message": "필수 정보가 누락되었습니다",
                    "errors": errors
                }

            return {
                "valid": True,
                "message": "검증 성공",
                "meta_data": meta_data
            }

        except Exception as e:
            return {
                "valid": False,
                "message": f"파일 읽기 오류: {str(e)}"
            }

    def read_excel_data(self, file_path):  # self 추가, file_path 파라미터로 변경
        """엑셀 파일에서 이름 데이터 읽기"""
        try:
            # 파일 존재 여부 확인
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

            # 엑셀 파일 읽기
            df = pd.read_excel(file_path, header=5)

            # '이름' 열이 있는지 확인
            if '이름' not in df.columns:
                raise ValueError(f"'이름' 열을 찾을 수 없습니다. 사용 가능한 열: {df.columns.tolist()}")

            data = df[['번호', '이름']].dropna()

            tag_name_dict = dict(zip(data['번호'], data['이름']))

            print(f"✅ 추출된 데이터 개수: {len(tag_name_dict)}개")
            print(f"📋 샘플 데이터: {dict(list(tag_name_dict.items())[:5])}")

            return tag_name_dict

        except Exception as e:
            print(f"❌ 엑셀 파일 읽기 오류: {str(e)}")
            raise

    def check_data_form(self, file_path):

        try:
            df = pd.read_excel(file_path, header=5)
            if '이름' not in df.columns or '번호' not in df.columns:
                return False



            return True

        except Exception as e:
            raise



excel_service = ExcelService()