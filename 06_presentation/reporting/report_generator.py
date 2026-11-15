import sys
import os
import datetime
import hashlib
import base64
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
HEADER_BG_PATH = os.path.join(BRANDING_DIR, "header_background.png")
ICON_SVG_PATH = os.path.join(BRANDING_DIR, "svg", "icon.svg")
ICON_ICO_PATH = os.path.join(BRANDING_DIR, "ico", "icon.ico")

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

        return {
            "report_id": report_id,
            "report_type": report_type,
            "title": title,
            "md_path": md_path,
            "html_path": html_path,
            "md_content": md_content,
            "html_content": html_content,
            "timestamp": now_str
        }

if __name__ == "__main__":
    rep = ReportGenerator()
    res = rep.generate_situation_report("SITREP")
    print(f"[*] تم توليد التقرير بنجاح: {res['report_id']}")
    print(f"    - Markdown: {res['md_path']}")
    print(f"    - HTML: {res['html_path']}")
