import os
import math
from dataclasses import dataclass
from io import BytesIO
from typing import Optional, Dict
from src.param.grade_standards import GRADE_STANDARDS
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader, PdfWriter

# ============================================
# 좌표 및 색상 설정
# ============================================
COORDINATES = {
    'name': (542, 18), 'school': (662, 18), 'age': (542, 36),
    'class_info': (662, 36), 'gender': (542, 54),
    'height': (105, 404), 'weight': (220, 404), 'bmi': (335, 404),
    'grade_50m': (532, 170), 'grade_shuttle': (686, 170),
    'grade_rolling_up': (532, 234), 'grade_flexibility': (686, 234),
    'grade_long_jump': (532, 298), 'grade_bmi': (686, 298),
    'grade_grip_left': (532, 362), 'grade_grip_right': (686, 362),
    'grade_total': (626, 424),
    'radar_center': (199, 247), 'radar_radius': 65, 'grid_max': 0.88,
    'bar_50m': 590, 'bar_shuttle': 655, 'bar_rolling_up': 720,
    'bar_flexibility': 785, 'bar_long_jump': 850,
    'bar_grip_right': 915, 'bar_grip_left': 980,
    'bar_base_x': 163, 'bar_width': 549, 'bar_height': 18,
}

OFFSET = {'x': 30, 'y': 30}
COLORS = {
    'text_dark': '#333333', 'grade_blue': '#5D95F3', 'grade_white': '#FFFFFF',
    'bar_blue': '#2A487B', 'radar_fill': (0.23, 0.35, 0.55, 0.5),
    'radar_stroke': '#2B5797', 'radar_grid': '#CCCCCC', 'radar_label': '#333333',
}


@dataclass
class StudentData:
    name: str;
    age: int;
    gender: str;
    school: str;
    class_info: str
    height: float;
    weight: float;
    bmi: float
    run_50m: float;
    shuttle_run: int;
    rolling_up: int;
    flexibility: float
    long_jump: float;
    grip_right: float;
    grip_left: float
    grade_50m: int = 1;
    grade_shuttle: int = 1;
    grade_rolling_up: int = 1
    grade_flexibility: int = 1;
    grade_long_jump: int = 1
    grade_grip_right: int = 1;
    grade_grip_left: int = 1
    grade_bmi: object = 1;
    grade_total: object = 1
    total_score: int = 0;
    score_bmi: int = 0
    agility_exercise: str = "longJump";
    muscle_exercise: str = "gripStrength"


# ============================================
# PDF 생성기 클래스
# ============================================
class PapsPdfGenerator:
    def __init__(self, template_path: str, font_path: str = None):
        self.template_path = template_path
        self.width, self.height = A4
        self.img_width, self.img_height = 794, 1123
        self._register_fonts(font_path)

    def _register_fonts(self, font_path: str = None):
        try:
            if font_path:
                pdfmetrics.registerFont(TTFont('SUIT-Bold', f'{font_path}/SUIT-Bold.ttf'))
            self.font_regular = 'SUIT-Bold'
            self.font_bold = 'SUIT-Bold'
        except:
            self.font_regular = 'Helvetica'
            self.font_bold = 'Helvetica-Bold'

    def _img_to_pdf(self, img_x: float, img_y: float) -> tuple:
        pdf_x = (img_x + OFFSET['x']) * self.width / self.img_width
        pdf_y = self.height - ((img_y + OFFSET['y']) * self.height / self.img_height)
        return pdf_x, pdf_y

    def _get_agility_label(self, exercise):
        return {"50mRun": "50m 달리기", "longJump": "제자리 멀리뛰기"}.get(exercise, exercise)

    def _get_muscle_label(self, exercise):
        return {"rollingUp": "윗몸 말아올리기", "gripStrength": "악력"}.get(exercise, exercise)

    def _get_cutoff_from_standards(self, standard_key: str, gender: str, age: int, is_reverse: bool):
        """GRADE_STANDARDS에서 동적으로 1등급 커트라인 추출"""
        print(f"[CUTOFF] 호출: key={standard_key}, gender={gender}, age={age}, reverse={is_reverse}", flush=True)

        g_str = str(gender).strip()
        gender_key = 'male' if ('남' in g_str or 'M' in g_str.upper()) else 'female'

        try:
            age_str = str(age).replace('세', '').strip()
            target_age = int(age_str)
            print(f"[CUTOFF] gender_key={gender_key}, target_age={target_age}", flush=True)

            if standard_key not in GRADE_STANDARDS:
                print(f"[CUTOFF ERROR] '{standard_key}' not in GRADE_STANDARDS. keys={list(GRADE_STANDARDS.keys())}", flush=True)
                return None

            if gender_key not in GRADE_STANDARDS[standard_key]:
                print(f"[CUTOFF ERROR] '{gender_key}' not in GRADE_STANDARDS['{standard_key}']", flush=True)
                return None

            if target_age not in GRADE_STANDARDS[standard_key][gender_key]:
                print(f"[CUTOFF ERROR] age {target_age} not in GRADE_STANDARDS['{standard_key}']['{gender_key}']. ages={list(GRADE_STANDARDS[standard_key][gender_key].keys())}", flush=True)
                return None

            standards = GRADE_STANDARDS[standard_key][gender_key][target_age]
            grade_1_items = [item for item in standards if item['grade'] == 1]

            if not grade_1_items:
                print(f"[CUTOFF WARN] No grade 1 items: {standard_key}/{gender_key}/{target_age}", flush=True)
                return None

            if is_reverse:
                result = max(item['max'] for item in grade_1_items)
            else:
                result = min(item['min'] for item in grade_1_items)

            print(f"[CUTOFF OK] {standard_key}/{gender_key}/{target_age} = {result}", flush=True)
            return result

        except Exception as e:
            print(f"[CUTOFF ERROR] {standard_key}/{gender_key}/{age} -> {type(e).__name__}: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return None

    def _draw_bar_charts(self, c: canvas.Canvas, data: StudentData):
        """막대 그래프 동적 기준점 적용"""
        print(f"DATA AGE : {data.age}", flush=True)
        print(f"DATA GENDER : {data.gender}", flush=True)
        print("=" * 30, flush=True)

        cutoff_50m = self._get_cutoff_from_standards("50mRun", data.gender, data.age, True)
        if cutoff_50m is None: cutoff_50m = 8.6

        cutoff_shuttle = self._get_cutoff_from_standards("shuttleRun", data.gender, data.age, False)
        if cutoff_shuttle is None: cutoff_shuttle = 55

        cutoff_rolling = self._get_cutoff_from_standards("rollingUp", data.gender, data.age, False)
        if cutoff_rolling is None: cutoff_rolling = 40

        cutoff_flex = self._get_cutoff_from_standards("sitAndReach", data.gender, data.age, False)
        if cutoff_flex is None: cutoff_flex = 17.0

        cutoff_jump = self._get_cutoff_from_standards("longJump", data.gender, data.age, False)
        if cutoff_jump is None: cutoff_jump = 186.1

        cutoff_grip = self._get_cutoff_from_standards("gripStrength", data.gender, data.age, False)
        if cutoff_grip is None: cutoff_grip = 37.5

        print(f"[CUTOFF FINAL] 50m={cutoff_50m}, shuttle={cutoff_shuttle}, rolling={cutoff_rolling}, flex={cutoff_flex}, jump={cutoff_jump}, grip={cutoff_grip}", flush=True)

        bar_config = [
            (COORDINATES['bar_50m'], data.run_50m, cutoff_50m, True, "초"),
            (COORDINATES['bar_shuttle'], data.shuttle_run, cutoff_shuttle, False, "회"),
            (COORDINATES['bar_rolling_up'], data.rolling_up, cutoff_rolling, False, "회"),
            (COORDINATES['bar_flexibility'], data.flexibility, cutoff_flex, False, "cm"),
            (COORDINATES['bar_long_jump'], data.long_jump, cutoff_jump, False, "cm"),
            (COORDINATES['bar_grip_right'], data.grip_right, cutoff_grip, False, "kg"),
            (COORDINATES['bar_grip_left'], data.grip_left, cutoff_grip, False, "kg"),
        ]

        base_x = COORDINATES['bar_base_x']
        bar_width_total = COORDINATES['bar_width']
        bar_height_total = COORDINATES['bar_height']

        for bar_y_coord, value, max_val, reverse, unit in bar_config:
            pdf_x, pdf_y = self._img_to_pdf(base_x, bar_y_coord)
            pdf_bar_width = bar_width_total * self.width / self.img_width
            pdf_bar_height = bar_height_total * self.height / self.img_height

            cutoff_text = f"{max_val}{unit}"
            c.setFillColor(colors.HexColor(COLORS['text_dark']))
            c.setFont(self.font_regular, 8)
            c.drawString(pdf_x + pdf_bar_width * 0.80 + 8, pdf_y + pdf_bar_height / 2 + 7, cutoff_text)

            if value == 0:
                c.setFont(self.font_regular, 8)
                c.drawString(pdf_x + 5, pdf_y - 3, f"0{unit}")
                continue

            if reverse:
                ratio = (12 - value) / (12 - max_val) * 0.80
            else:
                ratio = (value / max_val) * 0.80

            ratio = max(0.05, ratio)
            fill_width = pdf_bar_width * ratio

            c.setFillColor(colors.HexColor(COLORS['bar_blue']))
            c.roundRect(pdf_x, pdf_y - pdf_bar_height / 2, fill_width, pdf_bar_height, pdf_bar_height / 4, fill=1, stroke=0)

            c.setFillColor(colors.HexColor(COLORS['text_dark']))
            c.setFont(self.font_regular, 8)
            c.drawString(pdf_x + fill_width + 5, pdf_y - 4, f"{value}{unit}")

    def _draw_text_values(self, c: canvas.Canvas, data: StudentData):
        c.setFillColor(colors.HexColor(COLORS['text_dark']))
        c.setFont(self.font_regular, 8)
        fields = [('name', data.name), ('school', data.school), ('age', f"{data.age}세"),
                  ('class_info', data.class_info), ('gender', data.gender)]
        for key, val in fields:
            x, y = self._img_to_pdf(*COORDINATES[key])
            c.drawString(x, y, val)

        c.setFillColor(colors.HexColor(COLORS['grade_blue']))
        c.setFont(self.font_bold, 10)
        for key, val, unit in [('height', data.height, 'cm'), ('weight', data.weight, 'kg'), ('bmi', data.bmi, '')]:
            x, y = self._img_to_pdf(*COORDINATES[key])
            c.drawCentredString(x, y, f"{val:.1f}{unit}" if unit else f"{val:.2f}")

        grades = [('grade_50m', data.grade_50m), ('grade_shuttle', data.grade_shuttle),
                  ('grade_rolling_up', data.grade_rolling_up), ('grade_flexibility', data.grade_flexibility),
                  ('grade_long_jump', data.grade_long_jump), ('grade_grip_left', data.grade_grip_left),
                  ('grade_grip_right', data.grade_grip_right)]
        for key, g in grades:
            x, y = self._img_to_pdf(*COORDINATES[key])
            c.drawCentredString(x, y, f"{g}등급")

        # BMI 등급 - DB 문자열 값 그대로 표시
        x, y = self._img_to_pdf(*COORDINATES['grade_bmi'])
        c.drawCentredString(x, y, str(data.grade_bmi))

        c.setFillColor(colors.white)
        c.setFont(self.font_bold, 14)
        x, y = self._img_to_pdf(*COORDINATES['grade_total'])
        c.drawCentredString(x, y, f"{data.grade_total}등급" if data.grade_total else "-")

    def _draw_radar_chart(self, c: canvas.Canvas, data: StudentData):
        cx, cy = self._img_to_pdf(*COORDINATES['radar_center'])
        radius = COORDINATES['radar_radius']
        g_max = COORDINATES['grid_max']

        def g_to_r(g):
            return {1: 1.0, 2: 0.83, 3: 0.66, 4: 0.47, 5: 0.30}.get(g, 0.5)

        a_grade = data.grade_50m if data.agility_exercise == "50mRun" else data.grade_long_jump
        m_grade = data.grade_rolling_up if data.muscle_exercise == "rollingUp" else min(
            data.grade_grip_left or 5,
            data.grade_grip_right or 5
        )

        factors = [g_to_r(data.grade_shuttle), g_to_r(m_grade), g_to_r(data.grade_flexibility),
                   self._bmi_score_to_ratio(data.score_bmi), g_to_r(a_grade)]

        n = 5
        angles = [math.pi / 2 - (2 * math.pi * i / n) for i in range(n)]

        c.setFillColor(colors.Color(*COLORS['radar_fill']))
        c.setStrokeColor(colors.HexColor(COLORS['radar_stroke']))
        path = c.beginPath()
        for i, (ang, rat) in enumerate(zip(angles, factors)):
            r = radius * max(0.2, rat) * g_max
            x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.close()
        c.drawPath(path, fill=1, stroke=1)

        sub_labels = [
            "(왕복달리기)",
            f"({self._get_muscle_label(data.muscle_exercise)})",
            "(앉아 윗몸 앞으로 굽히기)",
            "(BMI)",
            f"({self._get_agility_label(data.agility_exercise)})",
        ]

        label_offsets = [
            (15, 0, -10),
            (15, 22, -6),
            (15, 12, -6),
            (15, -8.5, -6),
            (15, -13, -10),
        ]

        c.setFillColor(colors.HexColor(COLORS['radar_label']))
        c.setFont(self.font_regular, 6)

        for i, sub_label in enumerate(sub_labels):
            ang = angles[i]
            margin, dx, dy = label_offsets[i]
            lx = cx + (radius * g_max + margin) * math.cos(ang) + dx
            ly = cy + (radius * g_max + margin) * math.sin(ang) + dy
            c.drawCentredString(lx, ly, sub_label)

    def _bmi_score_to_ratio(self, score):
        if score >= 16:
            return 1.0   # 1등급
        elif score >= 12:
            return 0.83  # 2등급
        elif score >= 8:
            return 0.66  # 3등급
        elif score >= 4:
            return 0.47  # 4등급
        return 0.30      # 5등급

    def generate(self, data: StudentData, output_path: str) -> str:
        overlay_buffer = BytesIO()
        c = canvas.Canvas(overlay_buffer, pagesize=A4)
        self._draw_text_values(c, data)
        self._draw_bar_charts(c, data)
        self._draw_radar_chart(c, data)
        c.save()

        overlay_buffer.seek(0)
        template_pdf = PdfReader(self.template_path)
        overlay_pdf = PdfReader(overlay_buffer)
        writer = PdfWriter()
        page = template_pdf.pages[0]
        page.scale_to(self.width, self.height)
        page.merge_page(overlay_pdf.pages[0])
        writer.add_page(page)
        with open(output_path, 'wb') as f: writer.write(f)
        return output_path