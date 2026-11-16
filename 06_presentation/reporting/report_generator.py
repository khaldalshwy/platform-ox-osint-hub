import sys
import os
import io
import json
import time
import datetime
import hashlib
import base64
from collections import Counter
from typing import Dict, Any, List, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ضبط المسار العام
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for sub in ["01_acquisition", "02_storage", "03_processing", "04_orchestration", "06_presentation"]:
    p = os.path.join(BASE_DIR, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

from database import db

# مسارات الأصول والهوية البصرية الرسمية
BRANDING_DIR = os.path.join(BASE_DIR, "assets", "branding")
FONTS_DIR = os.path.join(BASE_DIR, "assets", "fonts")
HEADER_BG_PATH = os.path.join(BRANDING_DIR, "header_background.png")
ICON_SVG_PATH = os.path.join(BRANDING_DIR, "svg", "icon.svg")
ICON_PNG_PATH = os.path.join(BRANDING_DIR, "icon.png")
ICON_ICO_PATH = os.path.join(BRANDING_DIR, "ico", "icon.ico")
ARABIC_FONT_REGULAR = os.path.join(FONTS_DIR, "arial.ttf")
ARABIC_FONT_BOLD = os.path.join(FONTS_DIR, "arialbd.ttf")


def _pdf_to_bytes(pdf_obj) -> bytes:
    """تحويل مخرجات fpdf/fpdf2 إلى bytes بأمان على كافة الإصدارات"""
    try:
        out = pdf_obj.output(dest="S")
    except TypeError:
        out = pdf_obj.output()
    if isinstance(out, (bytes, bytearray)):
        return bytes(out)
    return str(out).encode("latin-1")


def _shape_ar(text: Any) -> str:
    """تشكيل وربط الحروف العربية للعرض السليم في PDF (fpdf2)"""
    s = str(text or "")
    if not s.strip():
        return ""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        reshaped = arabic_reshaper.reshape(s)
        return get_display(reshaped)
    except Exception:
        return s

class ReportGenerator:
    """
    محرك توليد التقارير الاستخباراتية لمنصة OSINT Platform OX
    يصدر تقارير تقدير الموقف، البرقيات العاجلة، والتقارير الإحصائية بصيغ Markdown و HTML
    ممهورة بالهوية الرسمية للمنصة وخلفية الهيدر والفوتير المعتمدة ومتجاوبة مع كافة الشاشات والجوالات.
    """
    def __init__(self):
        self.output_dir = os.path.join(os.path.dirname(__file__), "generated_reports")
        os.makedirs(self.output_dir, exist_ok=True)
        self._load_branding_assets()

    def _load_branding_assets(self):
        """تحميل الأيقونة وخلفية الهيدر وتحويلها إلى Base64 لدمجها ذاتياً في ملفات HTML"""
        self.header_bg_b64 = ""
        self.icon_svg_b64 = ""

        if os.path.exists(HEADER_BG_PATH):
            try:
                with open(HEADER_BG_PATH, "rb") as f:
                    self.header_bg_b64 = base64.b64encode(f.read()).decode("utf-8")
            except Exception:
                pass

        if os.path.exists(ICON_SVG_PATH):
            try:
                with open(ICON_SVG_PATH, "rb") as f:
                    self.icon_svg_b64 = base64.b64encode(f.read()).decode("utf-8")
            except Exception:
                pass

    def generate_situation_report(self, report_type: str = "SITREP", *args, **kwargs) -> Dict[str, str]:
        """
        توليد تقرير استخباراتي احترافي متكامل:
        أنواع التقارير المدعومة:
        - SITREP: تقرير تقدير موقف شامل
        - FLASH: برقية إنذار أمني عاجل
        - MARITIME: ملف الرصد البحري ومضيق باب المندب
        """
        kpis = db.get_kpis()
        events = db.get_events(limit=25)
        vessels = db.get_vessels(limit=15)
        now_dt = datetime.datetime.now()
        now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
        report_id = f"OX-REP-{now_dt.strftime('%Y%m%d-%H%M%S')}"

        if report_type == "FLASH":
            title = "برقية استخباراتية عاجلة (Urgent Intelligence Flash Bulletin)"
            classification = "أولوية قصوى / فوري"
            badge_color = "#ef4444"
            target_events = [e for e in events if e.get("urgency_level") == "قصوى"][:10]
            if not target_events:
                target_events = events[:5]
        elif report_type == "MARITIME":
            title = "ملف الرصد البحري وحركة الملاحة (Maritime OSINT Dossier)"
            classification = "تقييم أمني ملاحي دوري"
            badge_color = "#0284c7"
            target_events = [e for e in events if e.get("event_category") in ["بحري", "إغاثي/تجاري"]][:15]
            if not target_events:
                target_events = events[:10]
        else: # SITREP
            title = "تقرير تقدير موقف استخباراتي شامل (Situation Assessment Report)"
            classification = "رصد علني موثق - مركز العمليات"
            badge_color = "#10b981"
            target_events = events[:15]

        # 1. بناء محتوى Markdown
        md_content = f"""# {title}
**المنظومة المصدرة:** منصة الرصد العلني الاستخباراتية — Platform OX  
**المرجعية:** الإطار المنهجي المعتمد لمركز "معطى"  
**رقم التقرير المرجعي:** `{report_id}`  
**تاريخ وتوقيت الإصدار:** {now_str}  
**درجة التصنيف التشغيلي:** **{classification}**  

---

## 1. المؤشرات التكتيكية والجاهزية الميدانية (Executive KPIs)
* **إجمالي الأحداث المفهرسة والمحللة:** {kpis['total_events']} حدثاً
* **الأحداث ذات الأولوية القصوى (عاجلة):** {kpis['critical_events']}
* **القطع البحرية النشطة قيد التتبع (AIS):** {kpis['active_vessels']} سفينة
* **معدل التحقق والتثليث الميداني:** {kpis['verification_rate']}%

---

## 2. جدول الرصد الميداني والوقائع المفهرسة
| المعرف | عنوان الحدث / البرقية | التصنيف | مستوى التوتر | الموقع | حالة التحقق |
| :---: | :--- | :---: | :---: | :---: | :---: |
"""
        for ev in target_events:
            ev_id = ev.get('id', '-')
            ev_title = ev.get('title', '').replace('\n', ' ')[:75]
            ev_cat = ev.get('event_category', 'عام')
            ev_urgency = ev.get('urgency_level', 'روتينية')
            ev_loc = ev.get('location_name', 'غير محدد')
            ev_status = ev.get('fact_check_status', 'قيد التحقق')
            md_content += f"| {ev_id} | {ev_title}... | {ev_cat} | {ev_urgency} | {ev_loc} | {ev_status} |\n"

        md_content += f"""
---

## 3. وضع الملاحة والقطع البحرية في مضيق باب المندب والبحر الأحمر
| MMSI | اسم السفينة | النوع والنشاط | العلم | الإحداثيات | الوجهة | السرعة | الحالة |
| :---: | :--- | :--- | :---: | :---: | :--- | :---: | :---: |
"""
        for v in vessels[:10]:
            mmsi = v.get('mmsi', '-')
            name = v.get('vessel_name', 'Unknown')
            vtype = v.get('vessel_type', 'Cargo')[:25]
            flag = v.get('flag_country', '-')
            coords = f"{v.get('current_latitude', 0.0):.2f}, {v.get('current_longitude', 0.0):.2f}"
            dest = v.get('destination', '-')
            speed = f"{v.get('speed_knots', 0.0)} عقدة"
            nav = v.get('nav_status', 'Under way')
            md_content += f"| {mmsi} | {name} | {vtype} | {flag} | {coords} | {dest} | {speed} | {nav} |\n"

        md_content += f"""
---

## 4. الاستنتاجات الاستخباراتية وتقدير الموقف
1. **أمن الملاحة والممرات:** حركة الشحن مستمرة بمواكبة قوافل الحماية الدولية في خليج عدن وباب المندب مع رصد دوريات خفر السواحل في محيط ميناء الحديدة والصليف.
2. **التثليث الميداني ومكافحة الشائعات:** مطابقة تقارير هيئة UKMTO مع البث المباشر لإشارات AIS تدعم استبعاد الشائعات المتعلقة بالحوادث البحرية غير الموثقة.
3. **التوصيات العملياتية:** 
   - الإبقاء على وتيرة المسح المتوازي لجميع الخلاصات الإخبارية كل 15 دقيقة.
   - إخطار غرفة العمليات بأي انحراف ملحوظ في مسار ناقلات الطاقة أو سفن الإغاثة.

---
**توقيع ضابط العمليات المناوب:** غرفة العمليات المركزية | منصة الرصد العلني Platform OX  
**البصمة المشفرة للتقرير:** `{hashlib.sha256(md_content.encode('utf-8')).hexdigest()[:32]}`
"""

        # تحضير أكواد الصور بتنسيق Base64 المضمن
        bg_css = f"background: url('data:image/png;base64,{self.header_bg_b64}') center / cover no-repeat;" if self.header_bg_b64 else "background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);"
        icon_img_tag = f'<img src="data:image/svg+xml;base64,{self.icon_svg_b64}" alt="Logo" class="brand-logo" />' if self.icon_svg_b64 else '<div class="brand-fallback-badge">OX</div>'

        # 2. بناء صيغة HTML فائقة التجاوب مع جميع أحجام الشاشات والجوالات
        html_content = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{title} — {report_id}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Cairo', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #030712;
            color: #f8fafc;
            direction: rtl;
            text-align: right;
            padding-top: 130px; /* مسافة لحماية المحتوى تحت الهيدر الثابت */
            padding-bottom: 25px;
            min-height: 100vh;
        }}

        /* ============================================================
           الهيدر الثابت: بعرض الصفحة أفقياً وعمودياً بحجم 120 بكسل
           ============================================================ */
        .fixed-header-banner {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            width: 100%;
            height: 120px !important;
            min-height: 120px;
            max-height: 120px;
            z-index: 9999;
            {bg_css}
            box-shadow: 0 4px 25px rgba(0, 0, 0, 0.7);
            border-bottom: 2px solid #38bdf8;
            overflow: hidden;
        }}

        .header-overlay {{
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, rgba(3, 7, 18, 0.88) 0%, rgba(15, 23, 42, 0.72) 50%, rgba(3, 7, 18, 0.88) 100%);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 30px;
        }}

        .header-title-box {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}

        .brand-logo {{
            width: 58px;
            height: 58px;
            object-fit: contain;
            filter: drop-shadow(0 0 10px rgba(56, 189, 248, 0.5));
        }}

        .brand-fallback-badge {{
            width: 52px;
            height: 52px;
            border-radius: 12px;
            background: #0284c7;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
            font-size: 20px;
            color: white;
            box-shadow: 0 0 12px rgba(56, 189, 248, 0.5);
        }}

        .report-main-title {{
            font-size: clamp(14px, 2.2vw, 22px);
            font-weight: 900;
            color: #38bdf8;
            margin: 0;
            line-height: 1.3;
            text-shadow: 0 2px 8px rgba(0,0,0,0.8);
        }}

        .report-sub-meta {{
            font-size: clamp(10px, 1.2vw, 12px);
            color: #cbd5e1;
            margin-top: 3px;
        }}

        .classification-badge {{
            background-color: {badge_color};
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 800;
            font-size: clamp(11px, 1.3vw, 13px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            white-space: nowrap;
        }}

        /* ============================================================
           حاوية المحتوى المتجاوبة
           ============================================================ */
        .report-container {{
            max-width: 1200px;
            width: 95%;
            margin: 0 auto;
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(14px);
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
        }}

        .section-title {{
            font-size: clamp(15px, 1.8vw, 18px);
            color: #38bdf8;
            border-right: 4px solid #38bdf8;
            padding-right: 12px;
            margin: 28px 0 16px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        /* مؤشرات الأداء المتجاوبة (Grid) */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 16px;
            margin-bottom: 25px;
        }}

        .kpi-card {{
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(56, 189, 248, 0.2);
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            transition: transform 0.2s ease;
        }}

        .kpi-val {{
            font-size: clamp(22px, 3vw, 32px);
            font-weight: 900;
            color: #38bdf8;
            margin: 4px 0;
        }}

        .kpi-label {{
            font-size: 13px;
            color: #94a3b8;
            font-weight: 600;
        }}

        /* الجداول المتجاوبة */
        .table-responsive {{
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            border-radius: 10px;
            margin: 15px 0;
            border: 1px solid #334155;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: clamp(12px, 1.3vw, 14px);
            min-width: 550px;
        }}

        th, td {{
            padding: 12px 14px;
            text-align: right;
            border-bottom: 1px solid #1e293b;
        }}

        th {{
            background-color: #0f172a;
            color: #38bdf8;
            font-weight: 700;
            white-space: nowrap;
        }}

        tr:nth-child(even) {{
            background-color: rgba(30, 41, 59, 0.35);
        }}

        tr:hover {{
            background-color: rgba(56, 189, 248, 0.08);
        }}

        .tag-critical {{
            color: #ef4444;
            font-weight: bold;
        }}

        .tag-normal {{
            color: #10b981;
            font-weight: bold;
        }}

        /* توصيات تقدير الموقف */
        .recommendations-list {{
            background: rgba(30, 41, 59, 0.5);
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 20px 25px;
            margin: 15px 0;
            line-height: 1.8;
            font-size: clamp(12px, 1.3vw, 14px);
            color: #cbd5e1;
        }}

        .recommendations-list li {{
            margin-bottom: 10px;
        }}

        /* ============================================================
           الفوتير: بحجم 120 بكسل ولكن غير ثابت (ينتقل مع نهاية المحتوى)
           ============================================================ */
        .non-fixed-footer-banner {{
            position: relative;
            width: 100%;
            height: 120px !important;
            min-height: 120px;
            max-height: 120px;
            margin-top: 35px;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(56, 189, 248, 0.3);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            {bg_css}
        }}

        .footer-overlay {{
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, rgba(3, 7, 18, 0.90) 0%, rgba(15, 23, 42, 0.75) 50%, rgba(3, 7, 18, 0.90) 100%);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 25px;
        }}

        .footer-text-right {{
            font-size: clamp(11px, 1.2vw, 13px);
            color: #cbd5e1;
            line-height: 1.5;
        }}

        .footer-text-left {{
            font-size: clamp(10px, 1vw, 12px);
            color: #94a3b8;
            text-align: left;
            direction: ltr;
        }}

        /* التجاوب مع شاشات الجوال (Mobile Responsiveness) */
        @media (max-width: 768px) {{
            body {{
                padding-top: 125px;
            }}
            .header-overlay {{
                padding: 0 15px;
            }}
            .report-container {{
                width: 98%;
                padding: 16px 12px;
                border-radius: 10px;
            }}
            .kpi-grid {{
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
            }}
            .footer-overlay {{
                flex-direction: column;
                justify-content: center;
                gap: 8px;
                text-align: center;
            }}
            .footer-text-left {{
                text-align: center;
            }}
        }}

        @media (max-width: 480px) {{
            .kpi-grid {{
                grid-template-columns: 1fr;
            }}
            .brand-logo {{
                width: 44px;
                height: 44px;
            }}
        }}

        /* نمط الطباعة الرسمية */
        @media print {{
            body {{
                background-color: white !important;
                color: black !important;
                padding-top: 130px;
            }}
            .fixed-header-banner {{
                position: fixed;
                top: 0;
            }}
            .report-container {{
                background: white !important;
                border: 1px solid #ccc !important;
                color: black !important;
                box-shadow: none !important;
            }}
        }}
    </style>
</head>
<body>

    <!-- 1. الهيدر الثابت بعرض الصفحة أفقياً وعمودياً بحجم 120 بكسل -->
    <header class="fixed-header-banner">
        <div class="header-overlay">
            <div class="header-title-box">
                {icon_img_tag}
                <div>
                    <h1 class="report-main-title">{title}</h1>
                    <div class="report-sub-meta">
                        منصة الرصد العلني Platform OX | رقم الوثيقة: <b>{report_id}</b> | التاريخ: <b>{now_str}</b>
                    </div>
                </div>
            </div>
            <span class="classification-badge">{classification}</span>
        </div>
    </header>

    <!-- 2. جسم التقرير الاستخباراتي المتجاوب -->
    <main class="report-container">
        
        <!-- المؤشرات العامة (KPIs) -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">إجمالي الأحداث المفهرسة</div>
                <div class="kpi-val">{kpis['total_events']}</div>
                <div style="font-size: 11px; color: #38bdf8;">رصد علني مباشر</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">الأحداث العاجلة (أولوية قصوى)</div>
                <div class="kpi-val" style="color: #f43f5e;">{kpis['critical_events']}</div>
                <div style="font-size: 11px; color: #f43f5e;">تتطلب تثليثاً ميدانياً</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">القطع البحرية قيد التتبع (AIS)</div>
                <div class="kpi-val" style="color: #10b981;">{kpis['active_vessels']}</div>
                <div style="font-size: 11px; color: #10b981;">تغطية إشارات حية</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">معدل التوثيق والتحقق</div>
                <div class="kpi-val" style="color: #a855f7;">{kpis['verification_rate']}%</div>
                <div style="font-size: 11px; color: #a855f7;">وفق نموذج مركز معطى</div>
            </div>
        </div>

        <!-- جدول الأحداث الميدانية -->
        <h2 class="section-title">📡 جدول الرصد الميداني والوقائع المفهرسة</h2>
        <div class="table-responsive">
            <table>
                <thead>
                    <tr>
                        <th style="width: 60px;">المعرف</th>
                        <th>عنوان الواقعة / البرقية</th>
                        <th>التصنيف</th>
                        <th>مستوى الأهمية</th>
                        <th>الموقع الجغرافي</th>
                        <th>حالة التحقق</th>
                    </tr>
                </thead>
                <tbody>
"""
        for ev in target_events[:10]:
            is_crit = ev.get('urgency_level') == 'قصوى'
            cls_name = "tag-critical" if is_crit else "tag-normal"
            html_content += f"""
                    <tr>
                        <td><b>#{ev.get('id', '-')}</b></td>
                        <td>{ev.get('title', '')[:75]}...</td>
                        <td>{ev.get('event_category', 'عام')}</td>
                        <td><span class="{cls_name}">{ev.get('urgency_level', 'روتينية')}</span></td>
                        <td>📍 {ev.get('location_name', '-')}</td>
                        <td>{ev.get('fact_check_status', '-')}</td>
                    </tr>
            """

        html_content += f"""
                </tbody>
            </table>
        </div>

        <!-- جدول رادار الملاحة البحرية -->
        <h2 class="section-title">⚓ وضع الملاحة والقطع البحرية في باب المندب والبحر الأحمر</h2>
        <div class="table-responsive">
            <table>
                <thead>
                    <tr>
                        <th>MMSI</th>
                        <th>اسم السفينة</th>
                        <th>النوع والنشاط</th>
                        <th>العلم</th>
                        <th>الإحداثيات</th>
                        <th>الوجهة المجدولة</th>
                        <th>السرعة</th>
                        <th>الحالة الملاحية</th>
                    </tr>
                </thead>
                <tbody>
"""
        for v in vessels[:8]:
            html_content += f"""
                    <tr>
                        <td><code>{v.get('mmsi', '-')}</code></td>
                        <td><b>{v.get('vessel_name', '-')}</b></td>
                        <td>{v.get('vessel_type', '-')}</td>
                        <td>{v.get('flag_country', '-')}</td>
                        <td><code>{v.get('current_latitude', 0.0):.2f}, {v.get('current_longitude', 0.0):.2f}</code></td>
                        <td>{v.get('destination', '-')}</td>
                        <td>{v.get('speed_knots', '-')} عقدة</td>
                        <td>{v.get('nav_status', '-')}</td>
                    </tr>
            """

        html_content += f"""
                </tbody>
            </table>
        </div>

        <!-- التوصيات الاستخباراتية -->
        <h2 class="section-title">🛡️ التوصيات الاستخباراتية وتقدير الموقف الميداني</h2>
        <ul class="recommendations-list">
            <li><b>المراقبة اللحظية للممرات الحيوية:</b> استمرار رفع وتيرة المسح المتوازي لمضيق باب المندب، خليج عدن، ومحيط ميناء الحديدة والصليف.</li>
            <li><b>التثليث الميداني ومكافحة الشائعات:</b> مطابقة إشارات الرادار البحري AIS مع التحذيرات البحرية (UKMTO) للتأكد من دقة أي بلاغ بحري قبل رفعه لصناع القرار.</li>
            <li><b>تأمين سلاسل الإمداد الإغاثي:</b> متابعة مرافقة وتفريغ سفن الحبوب والمواد التموينية بانتظام والتنسيق مع خفر السواحل ومؤسسات الموانئ.</li>
        </ul>

        <!-- 3. الفوتير: بحجم 120 بكسل ولكن غير ثابت (ينتقل مع نهاية المحتوى) -->
        <footer class="non-fixed-footer-banner">
            <div class="footer-overlay">
                <div class="footer-text-right">
                    <p style="font-weight: 700; color: #38bdf8;">مركز الرصد والتحليل الاستخباراتي — Platform OX</p>
                    <p style="font-size: 11px;">مبني وفق المعايير المعمارية العالمية لمنهجية مركز معطى الخماسية</p>
                </div>
                <div class="footer-text-left">
                    <p>Document Security Hash:</p>
                    <code>{hashlib.sha256(md_content.encode('utf-8')).hexdigest()[:24]}</code>
                </div>
            </div>
        </footer>

    </main>

</body>
</html>
"""

        # حفظ الملفات
        filename_prefix = f"report_{report_type.lower()}_{now_dt.strftime('%Y%m%d_%H%M%S')}"
        md_path = os.path.join(self.output_dir, f"{filename_prefix}.md")
        html_path = os.path.join(self.output_dir, f"{filename_prefix}.html")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # بناء حزمة الأرشفة الشاملة بكامل النصوص والكيانات (التحسين 4.2 و 7.3)
        snapshots = self._build_full_snapshots(
            report_type=report_type,
            kpis=kpis,
            events=target_events,
            vessels=vessels[:15],
            selection_reason=f"تصنيف التقرير: {classification} | الحد الأقصى للأحداث: {len(target_events)}"
        )

        html_bytes = html_content.encode("utf-8")
        md_bytes = md_content.encode("utf-8")
        html_hash = hashlib.sha256(html_bytes).hexdigest()
        md_hash = hashlib.sha256(md_bytes).hexdigest()

        archive_html_id = db.save_report_archive({
            "report_type": report_type,
            "report_format": "html",
            "generated_at": now_str,
            "content": html_content,
            "file_size": len(html_bytes),
            "kpis_snapshot": snapshots["kpis_json"],
            "events_count": len(target_events),
            "vessels_count": len(vessels[:15]),
            "sha256_hash": html_hash,
            "file_path": html_path,
            "full_events_json": snapshots["events_json"],
            "full_vessels_json": snapshots["vessels_json"],
            "full_entities_json": snapshots["entities_json"],
            "metadata_json": snapshots["metadata_json"],
        })
        db.save_report_archive({
            "report_type": report_type,
            "report_format": "md",
            "generated_at": now_str,
            "content": md_content,
            "file_size": len(md_bytes),
            "kpis_snapshot": snapshots["kpis_json"],
            "events_count": len(target_events),
            "vessels_count": len(vessels[:15]),
            "sha256_hash": md_hash,
            "file_path": md_path,
            "full_events_json": snapshots["events_json"],
            "full_vessels_json": snapshots["vessels_json"],
            "full_entities_json": snapshots["entities_json"],
            "metadata_json": snapshots["metadata_json"],
        })

        return {
            "report_id": report_id,
            "report_type": report_type,
            "title": title,
            "classification": classification,
            "md_path": md_path,
            "html_path": html_path,
            "md_content": md_content,
            "html_content": html_content,
            "kpis": kpis,
            "events": target_events,
            "vessels": vessels[:15],
            "snapshots": snapshots,
            "archive_id": archive_html_id,
            "sha256_hash": html_hash,
            "timestamp": now_str,
        }

    def _build_full_snapshots(
        self,
        report_type: str,
        kpis: Dict[str, Any],
        events: List[Dict[str, Any]],
        vessels: List[Dict[str, Any]],
        selection_reason: str = ""
    ) -> Dict[str, str]:
        """تجميع اللقطة الكاملة للأحداث والسفن والكيانات المستخرجة لأغراض الأرشفة (التحسين 7)"""
        try:
            from nlp_engine.nlp_processor import NLPProcessor
            nlp = NLPProcessor()
        except Exception:
            nlp = None

        all_entities = {"LOCATION": set(), "ORGANIZATION": set(), "VESSEL": set(), "WEAPON_SYSTEM": set()}
        enriched_events = []
        for ev in events:
            full_txt = f"{ev.get('title', '')} {ev.get('raw_content', '')}".strip()
            raw_ents = nlp.extract_entities(full_txt) if nlp else []
            ents_grouped: Dict[str, List[str]] = {"LOCATION": [], "ORGANIZATION": [], "VESSEL": [], "WEAPON_SYSTEM": []}
            if isinstance(raw_ents, list):
                for item in raw_ents:
                    if isinstance(item, dict):
                        etype = item.get("type", "")
                        ename = item.get("entity", "")
                        if etype in ents_grouped and ename:
                            if ename not in ents_grouped[etype]:
                                ents_grouped[etype].append(ename)
                            all_entities[etype].add(ename)
            elif isinstance(raw_ents, dict):
                for k in all_entities:
                    for val in raw_ents.get(k, []):
                        ents_grouped[k].append(val)
                        all_entities[k].add(val)
            enriched_events.append({
                "id": ev.get("id"),
                "title": ev.get("title", ""),
                "raw_content": ev.get("raw_content", ""),
                "cleaned_content": ev.get("cleaned_content", ""),
                "event_category": ev.get("event_category", ""),
                "urgency_level": ev.get("urgency_level", ""),
                "sentiment_score": ev.get("sentiment_score", 0.0),
                "sentiment_label": ev.get("sentiment_label", ""),
                "location_name": ev.get("location_name", ""),
                "latitude": ev.get("latitude"),
                "longitude": ev.get("longitude"),
                "fact_check_status": ev.get("fact_check_status", ""),
                "raw_data_url": ev.get("raw_data_url", ""),
                "source_label": ev.get("source_label", ""),
                "published_at": ev.get("published_at", ""),
                "captured_at": ev.get("captured_at", ""),
                "extracted_entities": ents_grouped,
                "selection_context": selection_reason,
            })

        entities_serializable = {k: sorted(list(v)) for k, v in all_entities.items()}
        meta = {
            "report_type": report_type,
            "selection_reason": selection_reason,
            "storage_backend": db.get_backend_name(),
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        return {
            "kpis_json": json.dumps(kpis, ensure_ascii=False),
            "events_json": json.dumps(enriched_events, ensure_ascii=False),
            "vessels_json": json.dumps(vessels, ensure_ascii=False),
            "entities_json": json.dumps(entities_serializable, ensure_ascii=False),
            "metadata_json": json.dumps(meta, ensure_ascii=False),
        }

    def generate_pdf(self, report_type: str = "SITREP", base_report: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        التحسين 1: توليد تقرير PDF عربي احترافي مباشرة (باستخدام fpdf2 + arabic-reshaper + python-bidi)
        مع دعم الشعار والهوية البصرية وحفظه في generated_reports_archive.
        """
        from fpdf import FPDF

        rep = base_report or self.generate_situation_report(report_type)
        now_dt = datetime.datetime.now()
        now_str = rep.get("timestamp") or now_dt.strftime("%Y-%m-%d %H:%M:%S")
        pdf_filename = f"report_{report_type.lower()}_{now_dt.strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(self.output_dir, pdf_filename)

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # تحميل الخط العربي المضمن لضمان عمله على Windows و Streamlit Cloud Linux
        font_name = "ArialAr"
        if os.path.exists(ARABIC_FONT_REGULAR):
            pdf.add_font(font_name, "", ARABIC_FONT_REGULAR, uni=True)
            bold_path = ARABIC_FONT_BOLD if os.path.exists(ARABIC_FONT_BOLD) else ARABIC_FONT_REGULAR
            pdf.add_font(font_name, "B", bold_path, uni=True)
        else:
            font_name = "Helvetica"

        # ترويسة رسمية داكنة مع الشعار
        pdf.set_fill_color(15, 23, 42)
        pdf.rect(0, 0, 210, 32, "F")
        if os.path.exists(ICON_PNG_PATH):
            try:
                pdf.image(ICON_PNG_PATH, x=178, y=5, w=22)
            except Exception:
                pass

        pdf.set_font(font_name, "B", 15)
        pdf.set_text_color(56, 189, 248)
        pdf.set_xy(10, 7)
        pdf.cell(165, 8, _shape_ar(rep.get("title", "تقرير استخباراتي - Platform OX")), align="R", ln=1)

        pdf.set_font(font_name, "", 10)
        pdf.set_text_color(226, 232, 240)
        pdf.set_x(10)
        meta_line = f"منصة الرصد العلني Platform OX | المرجع: {rep.get('report_id', '')} | التاريخ: {now_str}"
        pdf.cell(165, 7, _shape_ar(meta_line), align="R", ln=1)

        pdf.ln(12)
        pdf.set_text_color(15, 23, 42)

        # 1. المؤشرات التكتيكية
        kpis = rep.get("kpis", db.get_kpis())
        pdf.set_font(font_name, "B", 12)
        pdf.set_text_color(2, 132, 199)
        pdf.cell(0, 8, _shape_ar("1. المؤشرات التكتيكية (KPIs)"), align="R", ln=1)
        pdf.set_font(font_name, "", 10)
        pdf.set_text_color(30, 41, 59)
        kpi_text = (
            f"إجمالي الأحداث: {kpis.get('total_events', 0)}  |  "
            f"الأحداث القصوى: {kpis.get('critical_events', 0)}  |  "
            f"السفن النشطة: {kpis.get('active_vessels', 0)}  |  "
            f"نسبة التحقق: {kpis.get('verification_rate', 0)}%"
        )
        pdf.multi_cell(0, 7, _shape_ar(kpi_text), align="R")
        pdf.ln(3)

        # 2. جدول الرصد الميداني بكامل تفاصيله
        pdf.set_font(font_name, "B", 12)
        pdf.set_text_color(2, 132, 199)
        pdf.cell(0, 8, _shape_ar("2. الوقائع والأحداث المرصودة"), align="R", ln=1)
        pdf.set_font(font_name, "", 9.5)
        pdf.set_text_color(15, 23, 42)
        for idx, ev in enumerate(rep.get("events", [])[:15], 1):
            ev_line = f"{idx}. [{ev.get('urgency_level', 'روتينية')} | {ev.get('event_category', 'عام')} | {ev.get('location_name', 'اليمن')}] {ev.get('title', '')}"
            pdf.multi_cell(0, 6, _shape_ar(ev_line), align="R")
            if ev.get("raw_data_url"):
                pdf.set_text_color(71, 85, 105)
                pdf.set_font(font_name, "", 8)
                pdf.multi_cell(0, 5, f"   URL: {str(ev.get('raw_data_url'))[:95]}", align="L")
                pdf.set_font(font_name, "", 9.5)
                pdf.set_text_color(15, 23, 42)

        pdf.ln(3)
        # 3. وضع الملاحة والسفن
        pdf.set_font(font_name, "B", 12)
        pdf.set_text_color(2, 132, 199)
        pdf.cell(0, 8, _shape_ar("3. وضع الملاحة والقطع البحرية (AIS)"), align="R", ln=1)
        pdf.set_font(font_name, "", 9)
        pdf.set_text_color(15, 23, 42)
        for v in rep.get("vessels", [])[:10]:
            v_line = (
                f"- {v.get('vessel_name', 'Unknown')} (MMSI: {v.get('mmsi', '-')}) | "
                f"{v.get('flag_country', '-')} -> {v.get('destination', '-')} | "
                f"{v.get('speed_knots', 0)} kn | ({v.get('current_latitude', 0):.2f}, {v.get('current_longitude', 0):.2f})"
            )
            pdf.multi_cell(0, 5.5, _shape_ar(v_line), align="R")

        pdf.ln(4)
        # تذييل SHA-256
        pdf.set_font(font_name, "B", 9)
        pdf.set_text_color(100, 116, 139)
        pdf.multi_cell(0, 5, _shape_ar(f"منصة الرصد العلني Platform OX — بصمة التحقق الرقمية: {rep.get('sha256_hash', '')[:32]}"), align="R")

        pdf_bytes = _pdf_to_bytes(pdf)
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)

        pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")
        pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
        snapshots = rep.get("snapshots") or self._build_full_snapshots(
            report_type, kpis, rep.get("events", []), rep.get("vessels", [])
        )

        archive_id = db.save_report_archive({
            "report_type": report_type,
            "report_format": "pdf",
            "generated_at": now_str,
            "content": pdf_b64,
            "file_size": len(pdf_bytes),
            "kpis_snapshot": snapshots["kpis_json"],
            "events_count": len(rep.get("events", [])),
            "vessels_count": len(rep.get("vessels", [])),
            "sha256_hash": pdf_hash,
            "file_path": pdf_path,
            "full_events_json": snapshots["events_json"],
            "full_vessels_json": snapshots["vessels_json"],
            "full_entities_json": snapshots["entities_json"],
            "metadata_json": snapshots["metadata_json"],
        })

        return {
            "report_id": rep.get("report_id"),
            "report_type": report_type,
            "filename": pdf_filename,
            "file_path": pdf_path,
            "bytes": pdf_bytes,
            "archive_id": archive_id,
            "sha256_hash": pdf_hash,
        }

    def generate_docx(self, report_type: str = "SITREP", base_report: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        التحسين 2: توليد مستند Word (.docx) احترافي متكامل RTL
        يضم الترويسة والشعار، KPIs، جدول الأحداث بكامل النصوص والروابط، جدول السفن، التوصيات، وتذييل SHA-256.
        """
        from docx import Document
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn

        rep = base_report or self.generate_situation_report(report_type)
        now_dt = datetime.datetime.now()
        now_str = rep.get("timestamp") or now_dt.strftime("%Y-%m-%d %H:%M:%S")
        docx_filename = f"report_{report_type.lower()}_{now_dt.strftime('%Y%m%d_%H%M%S')}.docx"
        docx_path = os.path.join(self.output_dir, docx_filename)

        doc = Document()

        def _set_rtl_paragraph(p):
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            pPr = p._p.get_or_add_pPr()
            bidi = OxmlElement("w:bidi")
            pPr.append(bidi)

        def _set_rtl_table(table):
            tblPr = table._tbl.tblPr
            bidiVisual = OxmlElement("w:bidiVisual")
            tblPr.append(bidiVisual)

        # الترويسة والشعار
        if os.path.exists(ICON_PNG_PATH):
            try:
                p_logo = doc.add_paragraph()
                _set_rtl_paragraph(p_logo)
                p_logo.add_run().add_picture(ICON_PNG_PATH, width=Inches(0.75))
            except Exception:
                pass

        h_title = doc.add_heading(rep.get("title", "تقرير تقدير موقف - Platform OX"), level=1)
        _set_rtl_paragraph(h_title)

        p_meta = doc.add_paragraph(
            f"منصة الرصد العلني Platform OX | رقم التقرير: {rep.get('report_id', '')} | "
            f"التاريخ: {now_str} | التصنيف: {rep.get('classification', '')}"
        )
        _set_rtl_paragraph(p_meta)

        # 1. جدول المؤشرات التكتيكية KPIs
        h1 = doc.add_heading("1. المؤشرات التكتيكية والجاهزية الميدانية (KPIs)", level=2)
        _set_rtl_paragraph(h1)
        kpis = rep.get("kpis", db.get_kpis())
        t_kpi = doc.add_table(rows=2, cols=4)
        t_kpi.style = "Table Grid"
        _set_rtl_table(t_kpi)
        kpi_headers = ["إجمالي الأحداث", "الأحداث القصوى", "السفن النشطة", "نسبة التحقق"]
        kpi_vals = [
            str(kpis.get("total_events", 0)),
            str(kpis.get("critical_events", 0)),
            str(kpis.get("active_vessels", 0)),
            f"{kpis.get('verification_rate', 0)}%",
        ]
        for idx, htxt in enumerate(kpi_headers):
            t_kpi.rows[0].cells[idx].text = htxt
            t_kpi.rows[1].cells[idx].text = kpi_vals[idx]

        # 2. جدول الأحداث الكامل (مع النص الكامل والرابط الأصلي)
        h2 = doc.add_heading("2. سجل الأحداث المفهرسة بكامل التفاصيل", level=2)
        _set_rtl_paragraph(h2)
        ev_list = rep.get("events", [])
        t_ev = doc.add_table(rows=1, cols=7)
        t_ev.style = "Table Grid"
        _set_rtl_table(t_ev)
        ev_headers = ["العنوان", "التصنيف", "الأهمية", "الموقع", "التاريخ", "الرابط الأصلي", "النص الكامل"]
        for i, htxt in enumerate(ev_headers):
            t_ev.rows[0].cells[i].text = htxt
        for ev in ev_list:
            row_cells = t_ev.add_row().cells
            row_cells[0].text = str(ev.get("title", ""))
            row_cells[1].text = str(ev.get("event_category", ""))
            row_cells[2].text = str(ev.get("urgency_level", ""))
            row_cells[3].text = str(ev.get("location_name", ""))
            row_cells[4].text = str(ev.get("published_at") or ev.get("captured_at") or "")
            row_cells[5].text = str(ev.get("raw_data_url", ""))
            row_cells[6].text = str(ev.get("raw_content", ""))[:600]

        # 3. جدول السفن
        h3 = doc.add_heading("3. وضع الملاحة والقطع البحرية (AIS)", level=2)
        _set_rtl_paragraph(h3)
        v_list = rep.get("vessels", [])[:15]
        t_v = doc.add_table(rows=1, cols=6)
        t_v.style = "Table Grid"
        _set_rtl_table(t_v)
        for i, htxt in enumerate(["اسم السفينة", "MMSI", "النوع", "العلم", "الوجهة", "السرعة/الإحداثيات"]):
            t_v.rows[0].cells[i].text = htxt
        for v in v_list:
            rc = t_v.add_row().cells
            rc[0].text = str(v.get("vessel_name", ""))
            rc[1].text = str(v.get("mmsi", ""))
            rc[2].text = str(v.get("vessel_type", ""))
            rc[3].text = str(v.get("flag_country", ""))
            rc[4].text = str(v.get("destination", ""))
            rc[5].text = f"{v.get('speed_knots', 0)} kn | ({v.get('current_latitude', 0):.2f}, {v.get('current_longitude', 0):.2f})"

        # 4. الاستنتاجات والتوصيات والتذييل
        h4 = doc.add_heading("4. الاستنتاجات الاستخباراتية والتوصيات", level=2)
        _set_rtl_paragraph(h4)
        for line in [
            "1. متابعة الملاحة البحرية ومواكبة قوافل الشحن في البحر الأحمر ومضيق باب المندب.",
            "2. مواصلة التثليث الميداني بين المصادر اليمنية المباشرة وبيانات AIS وإشعارات UKMTO.",
            "3. الإبقاء على دورة الرصد الآلي وتدقيق قسم سياسي/عام عبر فلتر الصلة اليمنية.",
        ]:
            p_c = doc.add_paragraph(line)
            _set_rtl_paragraph(p_c)

        buf = io.BytesIO()
        doc.save(buf)
        docx_bytes = buf.getvalue()
        docx_hash = hashlib.sha256(docx_bytes).hexdigest()

        # تذييل بالبصمة بعد الحساب الأولي وإعادة الحفظ
        p_foot = doc.add_paragraph(f"البصمة الرقمية للوثيقة (SHA-256): {docx_hash}")
        _set_rtl_paragraph(p_foot)
        buf2 = io.BytesIO()
        doc.save(buf2)
        docx_bytes = buf2.getvalue()
        docx_hash = hashlib.sha256(docx_bytes).hexdigest()

        with open(docx_path, "wb") as f:
            f.write(docx_bytes)

        snapshots = rep.get("snapshots") or self._build_full_snapshots(
            report_type, kpis, ev_list, v_list
        )
        docx_b64 = base64.b64encode(docx_bytes).decode("ascii")
        archive_id = db.save_report_archive({
            "report_type": report_type,
            "report_format": "docx",
            "generated_at": now_str,
            "content": docx_b64,
            "file_size": len(docx_bytes),
            "kpis_snapshot": snapshots["kpis_json"],
            "events_count": len(ev_list),
            "vessels_count": len(v_list),
            "sha256_hash": docx_hash,
            "file_path": docx_path,
            "full_events_json": snapshots["events_json"],
            "full_vessels_json": snapshots["vessels_json"],
            "full_entities_json": snapshots["entities_json"],
            "metadata_json": snapshots["metadata_json"],
        })

        return {
            "report_id": rep.get("report_id"),
            "report_type": report_type,
            "filename": docx_filename,
            "file_path": docx_path,
            "bytes": docx_bytes,
            "archive_id": archive_id,
            "sha256_hash": docx_hash,
        }

    def generate_filter_performance_report(self) -> Dict[str, Any]:
        """
        التحسين 3.2: توليد تقرير دقة الفلترة (Filter Performance Report) بصيغتي HTML + PDF
        """
        from fpdf import FPDF

        events = db.get_events(limit=1000)
        rejected = db.get_rejected_news(limit=1000)
        total_acc = len(events)
        total_rej = len(rejected)
        total_all = max(1, total_acc + total_rej)
        acc_rate = round((total_acc / total_all) * 100, 1)
        rej_rate = round((total_rej / total_all) * 100, 1)

        reasons_counter = Counter(str(r.get("reason") or r.get("rejection_reason") or "no_yemen_link") for r in rejected)
        rej_words = Counter()
        for r in rejected:
            for w in str(r.get("title", "")).split():
                if len(w) >= 3:
                    rej_words[w.strip(".,:!؟\"'()[]")] += 1
        acc_words = Counter()
        for e in events:
            for w in str(e.get("title", "")).split():
                if len(w) >= 3:
                    acc_words[w.strip(".,:!؟\"'()[]")] += 1

        top_rej = rej_words.most_common(10)
        top_acc = acc_words.most_common(10)
        now_dt = datetime.datetime.now()
        now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

        reasons_rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in reasons_counter.items())
        rej_rows = "".join(f"<tr><td>{w}</td><td>{c}</td></tr>" for w, c in top_rej)
        acc_rows = "".join(f"<tr><td>{w}</td><td>{c}</td></tr>" for w, c in top_acc)

        html_out = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl"><head><meta charset="UTF-8"><title>تقرير دقة الفلترة - Platform OX</title>
<style>
body {{ font-family: 'Cairo', Tahoma, sans-serif; background:#f8fafc; color:#0f172a; padding:24px; }}
.box {{ max-width:950px; margin:0 auto; background:#fff; border:1px solid #cbd5e1; border-radius:14px; padding:24px; }}
h1 {{ color:#0284c7; margin-top:0; }}
table {{ width:100%; border-collapse:collapse; margin:14px 0; }}
th, td {{ border:1px solid #cbd5e1; padding:8px 10px; text-align:right; }}
th {{ background:#e0f2fe; color:#0369a1; }}
</style></head><body><div class="box">
<h1>🛡️ تقرير دقة الفلترة (Filter Performance Report)</h1>
<p><b>التاريخ:</b> {now_str} | <b>إجمالي المقبول:</b> {total_acc} ({acc_rate}%) | <b>إجمالي المرفوض:</b> {total_rej} ({rej_rate}%)</p>
<h3>1. أسباب الرفض المجمعة</h3><table><tr><th>السبب</th><th>العدد</th></tr>{reasons_rows}</table>
<h3>2. أعلى 10 كلمات تسببت في الرفض</h3><table><tr><th>الكلمة</th><th>التكرار</th></tr>{rej_rows}</table>
<h3>3. أعلى 10 كلمات تسببت في القبول</h3><table><tr><th>الكلمة</th><th>التكرار</th></tr>{acc_rows}</table>
</div></body></html>"""

        pdf = FPDF()
        pdf.add_page()
        font_name = "ArialAr"
        if os.path.exists(ARABIC_FONT_REGULAR):
            pdf.add_font(font_name, "", ARABIC_FONT_REGULAR, uni=True)
            pdf.add_font(font_name, "B", ARABIC_FONT_BOLD if os.path.exists(ARABIC_FONT_BOLD) else ARABIC_FONT_REGULAR, uni=True)
        else:
            font_name = "Helvetica"
        pdf.set_font(font_name, "B", 14)
        pdf.cell(0, 10, _shape_ar("تقرير دقة الفلترة - Platform OX"), align="R", ln=1)
        pdf.set_font(font_name, "", 10)
        pdf.multi_cell(0, 7, _shape_ar(f"التاريخ: {now_str} | المقبول: {total_acc} ({acc_rate}%) | المرفوض: {total_rej} ({rej_rate}%)"), align="R")
        pdf.ln(3)
        pdf.set_font(font_name, "B", 11)
        pdf.cell(0, 7, _shape_ar("أسباب الرفض المجمعة:"), align="R", ln=1)
        pdf.set_font(font_name, "", 10)
        for k, v in reasons_counter.items():
            pdf.cell(0, 6, _shape_ar(f"- {k}: {v}"), align="R", ln=1)
        pdf.ln(2)
        pdf.set_font(font_name, "B", 11)
        pdf.cell(0, 7, _shape_ar("أعلى 10 كلمات في المرفوضات:"), align="R", ln=1)
        pdf.set_font(font_name, "", 10)
        pdf.multi_cell(0, 6, _shape_ar(" | ".join(f"{w} ({c})" for w, c in top_rej)), align="R")
        pdf.ln(2)
        pdf.set_font(font_name, "B", 11)
        pdf.cell(0, 7, _shape_ar("أعلى 10 كلمات في المقبولات:"), align="R", ln=1)
        pdf.set_font(font_name, "", 10)
        pdf.multi_cell(0, 6, _shape_ar(" | ".join(f"{w} ({c})" for w, c in top_acc)), align="R")

        pdf_bytes = _pdf_to_bytes(pdf)
        html_path = os.path.join(self.output_dir, f"filter_performance_{now_dt.strftime('%Y%m%d_%H%M%S')}.html")
        pdf_path = os.path.join(self.output_dir, f"filter_performance_{now_dt.strftime('%Y%m%d_%H%M%S')}.pdf")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_out)
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)

        db.save_report_archive({
            "report_type": "FILTER_AUDIT",
            "report_format": "html",
            "generated_at": now_str,
            "content": html_out,
            "file_size": len(html_out.encode("utf-8")),
            "kpis_snapshot": json.dumps({"accepted": total_acc, "rejected": total_rej, "acc_rate": acc_rate}, ensure_ascii=False),
            "events_count": total_acc,
            "vessels_count": 0,
            "sha256_hash": hashlib.sha256(html_out.encode("utf-8")).hexdigest(),
            "file_path": html_path,
            "full_events_json": "[]",
            "full_vessels_json": "[]",
            "full_entities_json": json.dumps({"top_rejected_words": top_rej, "top_accepted_words": top_acc}, ensure_ascii=False),
            "metadata_json": json.dumps({"reasons": dict(reasons_counter)}, ensure_ascii=False),
        })

        return {
            "html_content": html_out,
            "pdf_bytes": pdf_bytes,
            "html_path": html_path,
            "pdf_path": pdf_path,
            "stats": {
                "total_accepted": total_acc,
                "total_rejected": total_rej,
                "acc_rate": acc_rate,
                "rej_rate": rej_rate,
                "reasons": dict(reasons_counter),
                "top_rejected_words": top_rej,
                "top_accepted_words": top_acc,
            },
        }

    def cleanup_old_reports(self, days: int = 30) -> int:
        """التحسين 4.4: حذف الملفات المحلية الأقدم من X يوماً مع الإبقاء على سجلات Turso/SQLite"""
        cutoff = time.time() - (days * 86400)
        removed = 0
        if not os.path.exists(self.output_dir):
            return 0
        for fname in os.listdir(self.output_dir):
            fpath = os.path.join(self.output_dir, fname)
            if os.path.isfile(fpath) and os.path.getmtime(fpath) < cutoff:
                try:
                    os.remove(fpath)
                    removed += 1
                except Exception:
                    pass
        return removed

if __name__ == "__main__":
    rep = ReportGenerator()
    res = rep.generate_situation_report("SITREP")
    print(f"[*] تم توليد التقرير بنجاح: {res['report_id']}")
    print(f"    - Markdown: {res['md_path']}")
    print(f"    - HTML: {res['html_path']}")
