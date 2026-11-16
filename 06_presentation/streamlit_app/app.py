import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
import glob
import json
import math
import html as html_lib
import datetime

# ضبط المسار العام للوصول لكافة الطبقات
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(APP_DIR))
for sub in ["01_acquisition", "02_storage", "03_processing", "04_orchestration", "06_presentation"]:
    p = os.path.join(PROJECT_ROOT, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

import importlib
import base64
import database
importlib.reload(database)
from database import db
import pipeline_runner
importlib.reload(pipeline_runner)
from pipeline_runner import run_full_osint_cycle
from nlp_engine.nlp_processor import NLPProcessor
from sentiment.sentiment_analyzer import SentimentAnalyzer
from spatial_gis.spatial_analyzer import SpatialGISAnalyzer
from network_analysis.network_graph import EntityNetworkGraph
import reporting.report_generator
importlib.reload(reporting.report_generator)
from reporting.report_generator import ReportGenerator

# مسارات الهوية البصرية الرسمية
BRANDING_DIR = os.path.join(PROJECT_ROOT, "assets", "branding")
ICON_ICO_PATH = os.path.join(BRANDING_DIR, "ico", "icon.ico")
ICON_SVG_PATH = os.path.join(BRANDING_DIR, "svg", "icon.svg")
ICON_PNG_PATH = os.path.join(BRANDING_DIR, "icon.png")
HEADER_BG_PATH = os.path.join(BRANDING_DIR, "header_background.png")

svg_b64 = ""
if os.path.exists(ICON_SVG_PATH):
    try:
        with open(ICON_SVG_PATH, "rb") as f:
            svg_b64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        pass

# إعدادات صفحة Streamlit بالهوية الرسمية (.ico) — متجاوبة مع كافة الشاشات (الكمبيوتر، التابلت، الجوال)
st.set_page_config(
    page_title="Platform OX — OSINT Hub",
    page_icon=ICON_ICO_PATH if os.path.exists(ICON_ICO_PATH) else (ICON_PNG_PATH if os.path.exists(ICON_PNG_PATH) else "🛡️"),
    layout="wide",
    initial_sidebar_state="auto"
)

# ==============================================================================
# إعدادات الواجهة والمظهر (Theme System: Snow White Primary & Dark Secondary)
# ==============================================================================
LOGO_PATH = os.path.join(APP_DIR, "assets", "icon.png")
if not os.path.exists(LOGO_PATH):
    LOGO_PATH = os.path.join(PROJECT_ROOT, "imags", "icon.png")

with st.sidebar:
    brand_logo_sidebar = ICON_SVG_PATH if os.path.exists(ICON_SVG_PATH) else (ICON_PNG_PATH if os.path.exists(ICON_PNG_PATH) else LOGO_PATH)
    if os.path.exists(brand_logo_sidebar):
        st.image(brand_logo_sidebar, width=95)
    
    st.markdown("""
    <div style="margin-top: 5px; margin-bottom: 8px;">
        <h2 style="margin: 0; color: #0284c7; font-weight: 900; font-size: 1.45rem;">منصة الرصد العلني</h2>
        <span style="font-size: 0.85rem; color: #64748b; font-weight: 600;">Platform OX — OSINT Hub</span>
    </div>
    """, unsafe_allow_html=True)
    
    # محول المظهر — الأبيض الثلجي كخيار رئيسي افتراضي، والداكن كخيار ثانٍ
    theme_mode = st.radio(
        "🎨 مظهر واجهات البرنامج:",
        ["⚪ الأبيض الثلجي (الخيار الرئيسي)", "🌙 النمط الداكن (خيار ثانوي)"],
        index=0,
        horizontal=False
    )
    is_dark = (theme_mode == "🌙 النمط الداكن (خيار ثانوي)")
    st.markdown("---")

# تحديد متغيرات النمط والألوان بحسب المظهر المختار
if not is_dark:
    # ⚪ نمط الأبيض الثلجي الفاخر (Snow White Primary Theme)
    theme_bg = "linear-gradient(180deg, #ffffff 0%, #f8fafc 60%, #f1f5f9 100%)"
    theme_header_bg = "rgba(255, 255, 255, 0.95)"
    theme_text_color = "#0f172a"
    theme_heading_color = "#0f172a"
    theme_muted_color = "#475569"
    theme_card_bg = "#ffffff"
    theme_card_border = "#e2e8f0"
    theme_card_shadow = "0 4px 18px rgba(15, 23, 42, 0.05)"
    theme_card_hover_border = "#0284c7"
    theme_metric_val = "#0284c7"
    theme_metric_lbl = "#334155"
    theme_mission_box_bg = "linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)"
    theme_mission_box_border = "#0284c7"
    theme_mission_box_title = "#0369a1"
    theme_mission_box_text = "#1e293b"
    theme_event_card_bg = "#ffffff"
    theme_event_card_border = "#cbd5e1"
    theme_event_card_title = "#0369a1"
    theme_event_card_meta = "#475569"
    theme_plotly_template = "plotly_white"
    theme_plotly_font = "#0f172a"
    theme_section_header_border = "#cbd5e1"
    theme_threat_red = "background: #fef2f2; border-right: 5px solid #ef4444; color: #991b1b; border: 1px solid #fecaca; border-right-width: 5px;"
    theme_threat_orange = "background: #fffbeb; border-right: 5px solid #f59e0b; color: #92400e; border: 1px solid #fde68a; border-right-width: 5px;"
    theme_threat_green = "background: #f0fdf4; border-right: 5px solid #10b981; color: #166534; border: 1px solid #bbf7d0; border-right-width: 5px;"
    sidebar_bg = "#ffffff"
    sidebar_border = "#e2e8f0"
    input_bg = "#ffffff"
    input_border = "#cbd5e1"
    expander_bg = "#ffffff"
else:
    # 🌙 النمط الداكن الاستخباراتي (Cyber Dark Secondary Theme)
    theme_bg = "radial-gradient(circle at 15% 15%, #0f172a 0%, #030712 100%)"
    theme_header_bg = "rgba(15, 23, 42, 0.92)"
    theme_text_color = "#f8fafc"
    theme_heading_color = "#f8fafc"
    theme_muted_color = "#94a3b8"
    theme_card_bg = "rgba(30, 41, 59, 0.78)"
    theme_card_border = "rgba(56, 189, 248, 0.25)"
    theme_card_shadow = "0 8px 32px 0 rgba(0, 0, 0, 0.37)"
    theme_card_hover_border = "rgba(56, 189, 248, 0.65)"
    theme_metric_val = "#38bdf8"
    theme_metric_lbl = "#94a3b8"
    theme_mission_box_bg = "rgba(15, 23, 42, 0.78)"
    theme_mission_box_border = "#38bdf8"
    theme_mission_box_title = "#38bdf8"
    theme_mission_box_text = "#cbd5e1"
    theme_event_card_bg = "rgba(15, 23, 42, 0.75)"
    theme_event_card_border = "#334155"
    theme_event_card_title = "#38bdf8"
    theme_event_card_meta = "#94a3b8"
    theme_plotly_template = "plotly_dark"
    theme_plotly_font = "#f8fafc"
    theme_section_header_border = "#1e293b"
    theme_threat_red = "background: linear-gradient(90deg, rgba(239, 68, 68, 0.25) 0%, rgba(15, 23, 42, 0.85) 100%); border-right: 5px solid #ef4444; color: #fca5a5;"
    theme_threat_orange = "background: linear-gradient(90deg, rgba(245, 158, 11, 0.25) 0%, rgba(15, 23, 42, 0.85) 100%); border-right: 5px solid #f59e0b; color: #fcd34d;"
    theme_threat_green = "background: linear-gradient(90deg, rgba(16, 185, 129, 0.25) 0%, rgba(15, 23, 42, 0.85) 100%); border-right: 5px solid #10b981; color: #6ee7b7;"
    sidebar_bg = "#0f172a"
    sidebar_border = "#1e293b"
    input_bg = "#1e293b"
    input_border = "#334155"
    expander_bg = "rgba(15, 23, 42, 0.8)"

# حقن ملفات التنسيق CSS الشاملة المتوافقة مع الأبيض الثلجي (الرئيسي) والداكن (الثانوي)
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Cairo', sans-serif !important;
    }}

    .main, section[data-testid="stSidebar"], .stMarkdown, .stMarkdown p, .stMarkdown li,
    h1, h2, h3, h4, h5, h6, label, input, textarea, button,
    .metric-card, .threat-banner-red, .threat-banner-orange, .threat-banner-green {{
        font-family: 'Cairo', sans-serif !important;
        direction: rtl;
    }}

    /* حماية أيقونات Material Symbols وشريط أدوات Streamlit العلوي من تداخل الخط أو انعكاس الاتجاه */
    header[data-testid="stHeader"],
    header[data-testid="stHeader"] * {{
        direction: ltr !important;
    }}
    [data-testid="stIconMaterial"],
    .material-symbols-rounded,
    .material-icons,
    span[data-testid="stIconMaterial"] {{
        font-family: "Material Symbols Rounded", "Material Icons", sans-serif !important;
        direction: ltr !important;
        unicode-bidi: isolate !important;
    }}

    /* حماية جداول Glide Data Grid من قصّ الأعمدة الناتج عن فرض RTL على حاوية Canvas */
    [data-testid="stDataFrame"],
    [data-testid="stDataFrame"] * {{
        direction: ltr !important;
        font-family: 'Cairo', 'Segoe UI', Tahoma, sans-serif !important;
    }}

    /* إصلاح محاذاة القوائم النقطية والمرقمة في Markdown لتلتصق بالنص العربي يميناً */
    .stMarkdown ul,
    .stMarkdown ol {{
        direction: rtl !important;
        text-align: right !important;
        padding-right: 1.65rem !important;
        padding-left: 0 !important;
        margin-right: 0 !important;
        list-style-position: outside !important;
    }}
    .stMarkdown li {{
        direction: rtl !important;
        text-align: right !important;
        margin-bottom: 6px !important;
        line-height: 1.7 !important;
    }}
    
    .stApp, [data-testid="stAppViewContainer"], main {{
        background: {theme_bg} !important;
        color: {theme_text_color} !important;
    }}
    
    header[data-testid="stHeader"] {{
        background: {theme_header_bg} !important;
        color: {theme_text_color} !important;
        border-bottom: 1px solid {theme_card_border} !important;
    }}
    
    section[data-testid="stSidebar"] {{
        background: {sidebar_bg} !important;
        border-left: 1px solid {sidebar_border} !important;
    }}
    
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        color: {theme_text_color} !important;
    }}
    
    h1, h2, h3, h4, h5, h6 {{
        color: {theme_heading_color} !important;
        font-family: 'Cairo', sans-serif !important;
    }}
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    div[data-baseweb="select"] > div {{
        background-color: {input_bg} !important;
        color: {theme_text_color} !important;
        border-color: {input_border} !important;
        border-radius: 10px !important;
    }}
    
    details, [data-testid="stExpander"] {{
        background-color: {expander_bg} !important;
        border: 1px solid {theme_card_border} !important;
        border-radius: 12px !important;
        color: {theme_text_color} !important;
    }}
    
    .metric-card {{
        background: {theme_card_bg} !important;
        backdrop-filter: blur(12px);
        border: 1px solid {theme_card_border} !important;
        border-radius: 14px;
        padding: 18px;
        text-align: center;
        box-shadow: {theme_card_shadow};
        transition: transform 0.2s ease, border-color 0.2s ease;
    }}
    
    .metric-card:hover {{
        transform: translateY(-4px);
        border-color: {theme_card_hover_border} !important;
    }}
    
    .metric-val {{
        font-size: 2.2rem;
        font-weight: 900;
        color: {theme_metric_val} !important;
        margin: 5px 0;
    }}
    
    .metric-label {{
        font-size: 0.95rem;
        color: {theme_metric_lbl} !important;
        font-weight: 700;
    }}

    .status-badge-critical {{
        background-color: #ef4444;
        color: white !important;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }}

    .status-badge-verified {{
        background-color: #f59e0b;
        color: white !important;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }}

    .status-badge-routine {{
        background-color: #10b981;
        color: white !important;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }}

    .threat-banner-red {{
        {theme_threat_red}
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 20px;
        font-weight: 700;
    }}

    .threat-banner-orange {{
        {theme_threat_orange}
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 20px;
        font-weight: 700;
    }}

    .threat-banner-green {{
        {theme_threat_green}
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 20px;
        font-weight: 700;
    }}

    .section-header {{
        border-bottom: 2px solid {theme_section_header_border};
        padding-bottom: 10px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
    }}
    
    .section-header h2 {{
        color: {theme_heading_color} !important;
        margin: 0 !important;
        font-size: clamp(1.1rem, 2.2vw, 1.65rem) !important;
        line-height: 1.35 !important;
    }}

    /* ==========================================================================
       نظام التجاوب الشامل (Responsive Design: 1920px+ / 1366px / iPad / Mobile)
       ========================================================================== */
    html, body, .stApp, [data-testid="stAppViewContainer"] {{
        max-width: 100vw !important;
        overflow-x: hidden !important;
    }}

    .main .block-container {{
        max-width: 100% !important;
        padding-top: 1.4rem !important;
        padding-bottom: 2rem !important;
    }}

    img, svg, canvas, video, iframe {{
        max-width: 100% !important;
    }}

    /* ضمان قابلية التمرير الأفقي للجداول على جميع الشاشات دون انضغاط */
    [data-testid="stDataFrame"],
    [data-testid="stTable"],
    .stDataFrame {{
        width: 100% !important;
        max-width: 100% !important;
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
    }}

    [data-testid="stIFrame"],
    [data-testid="stIFrame"] > iframe,
    [data-testid="stPlotlyChart"] {{
        width: 100% !important;
        max-width: 100% !important;
    }}

    /* أزرار مريحة للمس (Touch-friendly) */
    .stButton > button,
    .stDownloadButton > button {{
        min-height: 42px !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        white-space: normal !important;
        word-break: break-word !important;
        line-height: 1.35 !important;
    }}

    /* 1) شاشات الكمبيوتر الكبيرة (1920px+) */
    @media (min-width: 1920px) {{
        .main .block-container {{
            padding-left: 3rem !important;
            padding-right: 3rem !important;
        }}
        .metric-val {{
            font-size: 2.5rem !important;
        }}
    }}

    /* 2) شاشات اللابتوب (<= 1366px) */
    @media (max-width: 1366px) {{
        .main .block-container {{
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }}
        .metric-card {{
            padding: 14px 12px !important;
        }}
        .metric-val {{
            font-size: 1.95rem !important;
        }}
    }}

    /* 3) الأجهزة اللوحية (iPad: 768px - 1024px) */
    @media (max-width: 1024px) and (min-width: 768px) {{
        .main .block-container {{
            padding: 1.1rem 1.1rem !important;
        }}
        [data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap !important;
            gap: 0.75rem !important;
        }}
        [data-testid="stHorizontalBlock"] > [data-testid="column"],
        [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {{
            flex: 1 1 calc(50% - 0.75rem) !important;
            min-width: calc(50% - 0.75rem) !important;
        }}
        .metric-val {{
            font-size: 1.75rem !important;
        }}
        .metric-label {{
            font-size: 0.88rem !important;
        }}
        .stButton > button,
        .stDownloadButton > button {{
            min-height: 44px !important;
            font-size: 0.92rem !important;
        }}
    }}

    /* 4) الجوالات الكبيرة والمتوسطة (<= 767px: Pro Max 430px, iPhone 14 390px) */
    @media (max-width: 767px) {{
        .main .block-container {{
            padding: 0.85rem 0.75rem 1.8rem 0.75rem !important;
        }}
        h1 {{
            font-size: 1.35rem !important;
            line-height: 1.35 !important;
        }}
        h2 {{
            font-size: 1.15rem !important;
            line-height: 1.35 !important;
        }}
        h3 {{
            font-size: 1.02rem !important;
            line-height: 1.35 !important;
        }}
        p, li, span, label, .stMarkdown {{
            font-size: 0.94rem !important;
        }}

        /* تكديس الأعمدة عمودياً بالكامل لمنع تداخل أو انضغاط العناصر */
        [data-testid="stHorizontalBlock"] {{
            flex-direction: column !important;
            flex-wrap: nowrap !important;
            gap: 0.65rem !important;
        }}
        [data-testid="stHorizontalBlock"] > [data-testid="column"],
        [data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {{
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            flex: 1 1 100% !important;
        }}

        /* بطاقات المؤشرات مريحة ومقروءة على الجوال */
        .metric-card {{
            padding: 12px 10px !important;
            border-radius: 12px !important;
            margin-bottom: 4px !important;
        }}
        .metric-val {{
            font-size: 1.65rem !important;
        }}
        .metric-label {{
            font-size: 0.86rem !important;
        }}

        /* أزرار بحجم لمس قياسي (>= 44px) وبعرض كامل */
        .stButton > button,
        .stDownloadButton > button {{
            width: 100% !important;
            min-height: 46px !important;
            font-size: 0.95rem !important;
            padding: 0.55rem 0.85rem !important;
        }}

        /* الخرائط والـ IFrames لا تخرج عن الشاشة ولا تحتل ارتفاعاً مفرطاً */
        [data-testid="stIFrame"],
        [data-testid="stIFrame"] > iframe {{
            width: 100% !important;
            max-width: 100% !important;
            max-height: 455px !important;
            border-radius: 12px !important;
        }}

        /* تنسيق شرائط التنبيه وبطاقات الأحداث */
        .threat-banner-red,
        .threat-banner-orange,
        .threat-banner-green {{
            padding: 11px 12px !important;
            font-size: 0.9rem !important;
            line-height: 1.5 !important;
        }}

        /* قائمة التبويبات إن وُجدت تلتف بسلاسة */
        [data-baseweb="tab-list"] {{
            flex-wrap: wrap !important;
            gap: 6px !important;
        }}
    }}

    /* 5) الجوالات الصغيرة (iPhone SE <= 390px و 375px) */
    @media (max-width: 390px) {{
        .main .block-container {{
            padding: 0.65rem 0.5rem 1.5rem 0.5rem !important;
        }}
        h1 {{
            font-size: 1.22rem !important;
        }}
        h2 {{
            font-size: 1.06rem !important;
        }}
        .metric-val {{
            font-size: 1.48rem !important;
        }}
        .metric-label {{
            font-size: 0.82rem !important;
        }}
        .stButton > button,
        .stDownloadButton > button {{
            min-height: 44px !important;
            font-size: 0.9rem !important;
            padding: 0.45rem 0.7rem !important;
        }}
        [data-testid="stIFrame"],
        [data-testid="stIFrame"] > iframe {{
            max-height: 410px !important;
        }}
    }}
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# محرك خرائط Google Earth التفاعلي الحقيقي وتصدير ملفات KML (الخطوة 5.3)
# ==============================================================================
from maritime_ais.ais_tracker import STRATEGIC_PORTS


def generate_google_earth_kml(events_list: list, vessels_list: list) -> str:
    """توليد ملف KML قياسي لفتحه مباشرة في برنامج Google Earth Pro بعلامات ملونة"""
    kml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        '<Document>',
        '  <name>منصة الرصد العلني Platform OX — الخريطة الاستخباراتية وحركة السفن</name>',
        '  <description>تصدير حي للأحداث الأمنية والقطع البحرية والموانئ الاستراتيجية على Google Earth</description>',
        '  <Style id="criticalStyle"><IconStyle><color>ff4444ef</color><scale>1.3</scale><Icon><href>http://maps.google.com/mapfiles/kml/paddle/red-stars.png</href></Icon></IconStyle></Style>',
        '  <Style id="moderateStyle"><IconStyle><color>ff0b9ef5</color><scale>1.15</scale><Icon><href>http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png</href></Icon></IconStyle></Style>',
        '  <Style id="routineStyle"><IconStyle><color>ff81b910</color><scale>1.05</scale><Icon><href>http://maps.google.com/mapfiles/kml/paddle/grn-circle.png</href></Icon></IconStyle></Style>',
        '  <Style id="vesselStyle"><IconStyle><color>fff8bd38</color><scale>1.25</scale><Icon><href>http://maps.google.com/mapfiles/kml/shapes/sailing.png</href></Icon></IconStyle></Style>',
        '  <Style id="portStyle"><IconStyle><color>ffffd700</color><scale>1.2</scale><Icon><href>http://maps.google.com/mapfiles/kml/shapes/marina.png</href></Icon></IconStyle></Style>',
    ]

    # مجلد الأحداث الاستخباراتية
    kml.append('  <Folder><name>الأحداث والوقائع الاستخباراتية (OSINT Events)</name>')
    for ev in (events_list or []):
        lat = ev.get("latitude")
        lon = ev.get("longitude")
        if lat is None or lon is None:
            continue
        urg = ev.get("urgency_level", "روتينية")
        style_id = "criticalStyle" if urg == "قصوى" else ("moderateStyle" if urg == "متوسطة" else "routineStyle")
        title = html_lib.escape(str(ev.get("title", "حدث مرصود")))
        loc = html_lib.escape(str(ev.get("location_name", "غير محدد")))
        cat = html_lib.escape(str(ev.get("event_category", "عام")))
        fact = html_lib.escape(str(ev.get("fact_check_status", "قيد التحقق")))
        raw = html_lib.escape(str(ev.get("raw_content", ""))[:400])
        kml.append(f"""    <Placemark>
      <name>[{urg}] {title[:70]}</name>
      <styleUrl>#{style_id}</styleUrl>
      <description><![CDATA[
        <div dir="rtl" style="font-family:Tahoma,Arial;padding:8px;">
          <h3 style="color:#0284c7;margin:0 0 6px 0;">{title}</h3>
          <p><b>الموقع:</b> {loc} ({lat:.4f}, {lon:.4f})</p>
          <p><b>التصنيف:</b> {cat} | <b>الأولوية:</b> {urg} | <b>التحقق:</b> {fact}</p>
          <hr/>
          <p>{raw}</p>
        </div>
      ]]></description>
      <Point><coordinates>{lon},{lat},0</coordinates></Point>
    </Placemark>""")
    kml.append('  </Folder>')

    # مجلد السفن والقطع البحرية
    kml.append('  <Folder><name>الرادار البحري وحركة السفن (AIS Vessels)</name>')
    for v in (vessels_list or []):
        lat = v.get("current_latitude")
        lon = v.get("current_longitude")
        if lat is None or lon is None:
            continue
        vname = html_lib.escape(str(v.get("vessel_name", "سفينة")))
        vtype = html_lib.escape(str(v.get("vessel_type", "")))
        flag = html_lib.escape(str(v.get("flag_country", "")))
        dest = html_lib.escape(str(v.get("destination", "")))
        spd = v.get("speed_knots", 0)
        nav = html_lib.escape(str(v.get("nav_status", "")))
        kml.append(f"""    <Placemark>
      <name>🚢 {vname} ({spd} kn)</name>
      <styleUrl>#vesselStyle</styleUrl>
      <description><![CDATA[
        <div dir="rtl" style="font-family:Tahoma,Arial;padding:8px;">
          <h3 style="color:#0369a1;margin:0 0 6px 0;">🚢 {vname}</h3>
          <p><b>النوع:</b> {vtype} | <b>العلم:</b> {flag}</p>
          <p><b>الوجهة:</b> {dest} | <b>السرعة:</b> {spd} عقدة</p>
          <p><b>الحالة الملاحية:</b> {nav}</p>
        </div>
      ]]></description>
      <Point><coordinates>{lon},{lat},0</coordinates></Point>
    </Placemark>""")
    kml.append('  </Folder>')

    # مجلد الموانئ الاستراتيجية
    kml.append('  <Folder><name>الموانئ والممرات الاستراتيجية (Strategic Ports)</name>')
    for p in STRATEGIC_PORTS:
        pname = html_lib.escape(p["name"])
        ptype = html_lib.escape(p["type"])
        kml.append(f"""    <Placemark>
      <name>⚓ {pname}</name>
      <styleUrl>#portStyle</styleUrl>
      <description>{ptype}</description>
      <Point><coordinates>{p['lon']},{p['lat']},0</coordinates></Point>
    </Placemark>""")
    kml.append('  </Folder>')

    kml.append('</Document></kml>')
    return "\n".join(kml)


def render_google_earth_map(
    events_list=None,
    vessels_list=None,
    show_ports=True,
    default_layer="hybrid",
    center_lat=13.8,
    center_lon=44.2,
    zoom=6,
    height=680,
    is_dark=False
):
    """
    محرك عرض خريطة قوقل إيرث التفاعلية الحقيقية عالية الدقة (Google Earth Satellite & Hybrid Map)
    يعرض صور الأقمار الصناعية الحقيقية من Google Earth مع الأسماء العربية للمدن والموانئ والممرات
    بدون أي شاشات سوداء، مع دعم كامل للنقر والتكبير والانتقال الجغرافي السريع والربط مع Google Earth 3D.
    """
    events_prepared = []
    coord_counts = {}

    if events_list:
        for idx, ev in enumerate(events_list):
            lat = ev.get("latitude")
            lon = ev.get("longitude")
            if lat is None or lon is None:
                continue
            try:
                lat = float(lat)
                lon = float(lon)
            except Exception:
                continue

            # منع تراكب النقاط المتطابقة في نفس المدينة عبر إزاحة حلزونية دقيقة
            key = (round(lat, 3), round(lon, 3))
            count = coord_counts.get(key, 0)
            coord_counts[key] = count + 1
            if count > 0:
                angle = count * 1.15
                radius = 0.025 * math.sqrt(count)
                lat = lat + radius * math.cos(angle)
                lon = lon + radius * math.sin(angle)

            events_prepared.append({
                "id": ev.get("id", idx + 1),
                "title": str(ev.get("title", "حدث مرصود"))[:110],
                "location": str(ev.get("location_name", "البحر الأحمر")),
                "category": str(ev.get("event_category", "عام")),
                "urgency": str(ev.get("urgency_level", "روتينية")),
                "fact": str(ev.get("fact_check_status", "قيد التحقق")),
                "sentiment": str(ev.get("sentiment_label", "محايد")),
                "time": str(ev.get("captured_at", "")),
                "url": str(ev.get("raw_data_url", "")),
                "lat": round(lat, 5),
                "lon": round(lon, 5)
            })

    vessels_prepared = []
    if vessels_list:
        for v in vessels_list:
            lat = v.get("current_latitude")
            lon = v.get("current_longitude")
            if lat is None or lon is None:
                continue
            try:
                lat = float(lat)
                lon = float(lon)
            except Exception:
                continue
            is_live_flag = bool(v.get("is_live", 0))
            badge_str = "🟢 حي مباشر" if is_live_flag else "🟡 محاكاة"
            vessels_prepared.append({
                "mmsi": v.get("mmsi", 0),
                "name": str(v.get("vessel_name", "سفينة")),
                "type": str(v.get("vessel_type", "شحن")),
                "flag": str(v.get("flag_country", "دولي")),
                "dest": str(v.get("destination", "غير محدد")),
                "speed": float(v.get("speed_knots", 0.0) or 0.0),
                "course": float(v.get("course_degrees", 0.0) or 0.0),
                "status": str(v.get("nav_status", "قيد الإبحار")),
                "mode_badge": badge_str,
                "signal": str(v.get("last_signal_at", "")),
                "lat": round(lat, 5),
                "lon": round(lon, 5)
            })

    events_json = json.dumps(events_prepared, ensure_ascii=False)
    vessels_json = json.dumps(vessels_prepared, ensure_ascii=False)
    ports_json = json.dumps(STRATEGIC_PORTS if show_ports else [], ensure_ascii=False)

    panel_bg = "rgba(15, 23, 42, 0.90)" if is_dark else "rgba(255, 255, 255, 0.95)"
    panel_text = "#f8fafc" if is_dark else "#0f172a"
    panel_border = "#334155" if is_dark else "#cbd5e1"
    btn_bg = "#1e293b" if is_dark else "#f1f5f9"
    btn_hover = "#0284c7"

    map_html = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
        <style>
            * {{
                box-sizing: border-box;
                font-family: 'Cairo', Tahoma, sans-serif;
            }}
            html, body {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                background: #0b192c;
                overflow: hidden;
            }}
            #map-wrapper {{
                position: relative;
                width: 100%;
                height: {height - 10}px;
                border-radius: 14px;
                overflow: hidden;
                border: 2px solid {panel_border};
                box-shadow: 0 10px 30px rgba(0,0,0,0.12);
            }}
            #earth-map {{
                width: 100%;
                height: 100%;
                background: #0a192f;
            }}
            /* شريط الانتقال السريع للمناطق الاستراتيجية على Google Earth */
            .fly-bar {{
                position: absolute;
                top: 12px;
                right: 12px;
                z-index: 1000;
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
                background: {panel_bg};
                backdrop-filter: blur(10px);
                padding: 8px 12px;
                border-radius: 12px;
                border: 1px solid {panel_border};
                box-shadow: 0 4px 16px rgba(0,0,0,0.2);
                max-width: calc(100% - 260px);
            }}
            .fly-title {{
                font-size: 0.82rem;
                font-weight: 800;
                color: #0284c7;
                margin-left: 6px;
                display: flex;
                align-items: center;
                gap: 4px;
            }}
            .fly-btn {{
                background: {btn_bg};
                color: {panel_text};
                border: 1px solid {panel_border};
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 0.78rem;
                font-weight: 700;
                cursor: pointer;
                transition: all 0.18s ease;
            }}
            .fly-btn:hover {{
                background: {btn_hover};
                color: #ffffff;
                border-color: {btn_hover};
                transform: translateY(-1px);
            }}
            /* مفتاح الخريطة التوضيحي */
            .map-legend {{
                position: absolute;
                bottom: 24px;
                right: 12px;
                z-index: 1000;
                background: {panel_bg};
                color: {panel_text};
                backdrop-filter: blur(10px);
                padding: 10px 14px;
                border-radius: 12px;
                border: 1px solid {panel_border};
                box-shadow: 0 4px 18px rgba(0,0,0,0.22);
                font-size: 0.8rem;
                min-width: 195px;
            }}
            .legend-title {{
                font-weight: 800;
                font-size: 0.85rem;
                margin-bottom: 6px;
                color: #0284c7;
                border-bottom: 1px solid {panel_border};
                padding-bottom: 4px;
            }}
            .legend-item {{
                display: flex;
                align-items: center;
                gap: 8px;
                margin: 4px 0;
                font-weight: 600;
            }}
            .dot {{
                width: 12px;
                height: 12px;
                border-radius: 50%;
                display: inline-block;
            }}
            /* شريط الإحداثيات الحية وشارة Google Earth */
            .coords-hud {{
                position: absolute;
                bottom: 24px;
                left: 12px;
                z-index: 1000;
                background: {panel_bg};
                color: {panel_text};
                padding: 6px 12px;
                border-radius: 10px;
                border: 1px solid {panel_border};
                font-size: 0.78rem;
                font-weight: 700;
                box-shadow: 0 4px 14px rgba(0,0,0,0.2);
                direction: ltr;
            }}
            /* نبض راداري للأحداث الحرجة */
            @keyframes pulse-red {{
                0% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.85); }}
                70% {{ box-shadow: 0 0 0 14px rgba(239, 68, 68, 0); }}
                100% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }}
            }}
            .marker-critical {{
                width: 18px;
                height: 18px;
                background: #ef4444;
                border: 2.5px solid #ffffff;
                border-radius: 50%;
                animation: pulse-red 1.8s infinite;
            }}
            .marker-moderate {{
                width: 15px;
                height: 15px;
                background: #f59e0b;
                border: 2.5px solid #ffffff;
                border-radius: 50%;
                box-shadow: 0 0 8px rgba(245, 158, 11, 0.8);
            }}
            .marker-routine {{
                width: 14px;
                height: 14px;
                background: #10b981;
                border: 2px solid #ffffff;
                border-radius: 50%;
                box-shadow: 0 0 6px rgba(16, 185, 129, 0.7);
            }}
            .leaflet-popup-content-wrapper {{
                border-radius: 12px !important;
                padding: 2px !important;
                direction: rtl;
                text-align: right;
            }}
            .popup-card {{
                font-family: 'Cairo', sans-serif;
                min-width: 250px;
                max-width: 310px;
                direction: rtl;
                text-align: right;
            }}
            .popup-header {{
                font-weight: 800;
                font-size: 0.95rem;
                color: #0369a1;
                margin-bottom: 6px;
                border-bottom: 1px solid #e2e8f0;
                padding-bottom: 5px;
            }}
            .popup-meta {{
                font-size: 0.8rem;
                color: #334155;
                margin: 3px 0;
            }}
            .popup-actions {{
                display: flex;
                gap: 6px;
                margin-top: 8px;
                padding-top: 6px;
                border-top: 1px solid #e2e8f0;
            }}
            .popup-link {{
                flex: 1;
                text-align: center;
                background: #0284c7;
                color: #ffffff !important;
                text-decoration: none;
                padding: 5px 8px;
                border-radius: 7px;
                font-size: 0.76rem;
                font-weight: 700;
            }}
            .popup-link.secondary {{
                background: #0f172a;
            }}
            .leaflet-control-layers {{
                border-radius: 10px !important;
                border: 1px solid {panel_border} !important;
                font-family: 'Cairo', sans-serif !important;
                font-weight: 700;
                direction: rtl;
                text-align: right;
            }}
            @media (max-width: 768px) {{
                #map-wrapper {{
                    height: 440px;
                    border-radius: 12px;
                }}
                .fly-bar {{
                    max-width: calc(100% - 64px);
                    top: 8px;
                    right: 8px;
                    padding: 6px 8px;
                    gap: 4px;
                }}
                .fly-title {{
                    font-size: 0.72rem;
                    width: 100%;
                }}
                .fly-btn {{
                    font-size: 0.7rem;
                    padding: 4px 7px;
                    min-height: 28px;
                }}
                .map-legend {{
                    bottom: 10px;
                    right: 8px;
                    padding: 6px 8px;
                    font-size: 0.7rem;
                    min-width: 135px;
                }}
                .legend-title {{
                    font-size: 0.74rem;
                }}
                .coords-hud {{
                    bottom: 10px;
                    left: 8px;
                    padding: 4px 8px;
                    font-size: 0.68rem;
                }}
                .popup-card {{
                    min-width: 190px;
                    max-width: 240px;
                }}
                .popup-header {{
                    font-size: 0.85rem;
                }}
                .popup-meta {{
                    font-size: 0.74rem;
                }}
            }}
            @media (max-width: 480px) {{
                #map-wrapper {{
                    height: 395px;
                }}
                .coords-hud {{
                    display: none;
                }}
            }}
        </style>
    </head>
    <body>
        <div id="map-wrapper">
            <!-- شريط الانتقال الفوري للمناطق الاستراتيجية على Google Earth -->
            <div class="fly-bar">
                <span class="fly-title">🌍 انتقال فوري (Google Earth):</span>
                <button class="fly-btn" onclick="flyToZone(12.586, 43.342, 10)">🎯 مضيق باب المندب</button>
                <button class="fly-btn" onclick="flyToZone(14.850, 42.900, 10)">⚓ الحديدة والصليف</button>
                <button class="fly-btn" onclick="flyToZone(12.785, 44.978, 11)">⚓ ميناء وخليج عدن</button>
                <button class="fly-btn" onclick="flyToZone(13.750, 42.750, 9)">🏝️ جزر حنيش والبحر الأحمر</button>
                <button class="fly-btn" onclick="flyToZone(12.463, 53.823, 9)">🌴 أرخبيل سقطرى</button>
                <button class="fly-btn" onclick="flyToZone(14.0, 44.5, 6)">🌐 المسرح الإقليمي الشامل</button>
            </div>

            <!-- عنصر الخريطة -->
            <div id="earth-map"></div>

            <!-- مفتاح الخريطة -->
            <div class="map-legend">
                <div class="legend-title">🗺️ مفتاح خريطة قوقل إيرث</div>
                <div class="legend-item"><span class="dot" style="background:#ef4444;box-shadow:0 0 6px #ef4444;"></span> حدث عاجل / أولوية قصوى</div>
                <div class="legend-item"><span class="dot" style="background:#f59e0b;"></span> حدث متوسط الأهمية</div>
                <div class="legend-item"><span class="dot" style="background:#10b981;"></span> حدث روتيني / ملاحة طبيعية</div>
                <div class="legend-item"><span class="dot" style="background:#38bdf8;border:2px solid #0284c7;"></span> سفينة / قطعة بحرية (AIS)</div>
                <div class="legend-item"><span class="dot" style="background:#eab308;"></span> ميناء / ممر استراتيجي</div>
            </div>

            <!-- شريط الإحداثيات الحية -->
            <div class="coords-hud" id="coords-box">
                🌍 Google Earth Satellite | Lat: {center_lat:.4f}° N, Lon: {center_lon:.4f}° E
            </div>
        </div>

        <script>
            // طبقات قوقل إيرث الحقيقية (Google Earth Official Tile Servers)
            const googleHybrid = L.tileLayer('https://mt1.google.com/vt/lyrs=y&hl=ar&x={{x}}&y={{y}}&z={{z}}', {{
                maxZoom: 20,
                attribution: '🌍 Google Earth Satellite Hybrid'
            }});

            const googleSatellite = L.tileLayer('https://mt1.google.com/vt/lyrs=s&hl=ar&x={{x}}&y={{y}}&z={{z}}', {{
                maxZoom: 20,
                attribution: '🛰️ Google Earth Satellite'
            }});

            const googleTerrain = L.tileLayer('https://mt1.google.com/vt/lyrs=p&hl=ar&x={{x}}&y={{y}}&z={{z}}', {{
                maxZoom: 20,
                attribution: '🏔️ Google Terrain'
            }});

            const googleRoadmap = L.tileLayer('https://mt1.google.com/vt/lyrs=m&hl=ar&x={{x}}&y={{y}}&z={{z}}', {{
                maxZoom: 20,
                attribution: '🗺️ Google Maps'
            }});

            const esriSatellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
                maxZoom: 19,
                attribution: 'Esri World Imagery'
            }});

            const defaultLayerMap = {{
                "hybrid": googleHybrid,
                "satellite": googleSatellite,
                "terrain": googleTerrain,
                "roadmap": googleRoadmap
            }};

            const map = L.map('earth-map', {{
                center: [{center_lat}, {center_lon}],
                zoom: {zoom},
                layers: [defaultLayerMap["{default_layer}"] || googleHybrid],
                zoomControl: false
            }});

            L.control.zoom({{ position: 'topleft' }}).addTo(map);

            // مجموعات الطبقات التفاعلية
            const eventsGroup = L.layerGroup().addTo(map);
            const vesselsGroup = L.layerGroup().addTo(map);
            const portsGroup = L.layerGroup().addTo(map);

            const baseLayers = {{
                "🌍 قوقل إيرث هجين (قمر صناعي + أسماء المدن)": googleHybrid,
                "🛰️ قوقل إيرث صافي (قمر صناعي عالي الدقة)": googleSatellite,
                "🏔️ قوقل إيرث تضاريس (الجبال والسواحل)": googleTerrain,
                "🗺️ خرائط قوقل التفصيلية (الطرق والموانئ)": googleRoadmap,
                "🌐 أقمار Esri العالمية (World Imagery)": esriSatellite
            }};

            const overlays = {{
                "📡 الأحداث والوقائع الاستخباراتية": eventsGroup,
                "🚢 حركة السفن والرادار البحري (AIS)": vesselsGroup,
                "⚓ الموانئ والممرات الاستراتيجية": portsGroup
            }};

            L.control.layers(baseLayers, overlays, {{ position: 'topleft', collapsed: false }}).addTo(map);

            // تحديث الإحداثيات الحية عند تحريك الماوس
            map.on('mousemove', function(e) {{
                document.getElementById('coords-box').innerHTML =
                    '🌍 Google Earth | Lat: ' + e.latlng.lat.toFixed(4) + '° N, Lon: ' + e.latlng.lng.toFixed(4) + '° E';
            }});

            function flyToZone(lat, lon, z) {{
                map.flyTo([lat, lon], z, {{ duration: 1.4 }});
            }}

            // 1. رسم الموانئ والممرات الاستراتيجية
            const portsData = {ports_json};
            portsData.forEach(function(p) {{
                const portIcon = L.divIcon({{
                    className: '',
                    html: '<div style="background:#eab308;color:#0f172a;border:2px solid #fff;border-radius:50%;width:22px;height:22px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:bold;box-shadow:0 0 10px rgba(234,179,8,0.9);">⚓</div>',
                    iconSize: [22, 22],
                    iconAnchor: [11, 11]
                }});
                const m = L.marker([p.lat, p.lon], {{ icon: portIcon }});
                const earth3dUrl = 'https://earth.google.com/web/@' + p.lat + ',' + p.lon + ',200a,18000d,35y,0h,45t,0r';
                const gmapsUrl = 'https://www.google.com/maps?q=' + p.lat + ',' + p.lon + '&hl=ar&t=k&z=13';
                m.bindPopup(
                    '<div class="popup-card">' +
                        '<div class="popup-header">⚓ ' + p.name + '</div>' +
                        '<div class="popup-meta"><b>التصنيف:</b> ' + p.type + '</div>' +
                        '<div class="popup-meta"><b>الإحداثيات:</b> ' + p.lat.toFixed(4) + ', ' + p.lon.toFixed(4) + '</div>' +
                        '<div class="popup-meta"><b>نطاق المراقبة:</b> ' + p.radius_km + ' كم</div>' +
                        '<div class="popup-actions">' +
                            '<a class="popup-link" href="' + earth3dUrl + '" target="_blank">🌍 Google Earth 3D</a>' +
                            '<a class="popup-link secondary" href="' + gmapsUrl + '" target="_blank">📍 Google Maps</a>' +
                        '</div>' +
                    '</div>'
                );
                m.bindTooltip(p.name, {{ direction: 'top', offset: [0, -10] }});
                portsGroup.addLayer(m);

                // دائرة النطاق الاستراتيجي
                const circle = L.circle([p.lat, p.lon], {{
                    radius: p.radius_km * 1000,
                    color: '#eab308',
                    weight: 1.2,
                    dashArray: '5, 5',
                    fillColor: '#eab308',
                    fillOpacity: 0.06
                }});
                portsGroup.addLayer(circle);
            }});

            // 2. رسم الأحداث الاستخباراتية المرصودة
            const eventsData = {events_json};
            eventsData.forEach(function(ev) {{
                let cls = 'marker-routine';
                let badgeBg = '#10b981';
                let sz = 14;
                if (ev.urgency === 'قصوى') {{
                    cls = 'marker-critical';
                    badgeBg = '#ef4444';
                    sz = 18;
                }} else if (ev.urgency === 'متوسطة') {{
                    cls = 'marker-moderate';
                    badgeBg = '#f59e0b';
                    sz = 15;
                }}

                const evIcon = L.divIcon({{
                    className: '',
                    html: '<div class="' + cls + '"></div>',
                    iconSize: [sz, sz],
                    iconAnchor: [sz/2, sz/2]
                }});

                const marker = L.marker([ev.lat, ev.lon], {{ icon: evIcon }});
                const earth3dUrl = 'https://earth.google.com/web/@' + ev.lat + ',' + ev.lon + ',300a,28000d,35y,0h,40t,0r';
                const gmapsUrl = 'https://www.google.com/maps?q=' + ev.lat + ',' + ev.lon + '&hl=ar&t=k&z=12';

                marker.bindPopup(
                    '<div class="popup-card">' +
                        '<div class="popup-header">#' + ev.id + ' — ' + ev.title + '</div>' +
                        '<div class="popup-meta"><span style="background:' + badgeBg + ';color:#fff;padding:2px 8px;border-radius:12px;font-size:0.74rem;font-weight:700;">الأولوية: ' + ev.urgency + '</span></div>' +
                        '<div class="popup-meta">📍 <b>الموقع:</b> ' + ev.location + ' (' + ev.lat.toFixed(3) + ', ' + ev.lon.toFixed(3) + ')</div>' +
                        '<div class="popup-meta">🏷️ <b>التصنيف:</b> ' + ev.category + ' | <b>النبرة:</b> ' + ev.sentiment + '</div>' +
                        '<div class="popup-meta">✅ <b>حالة التحقق:</b> ' + ev.fact + '</div>' +
                        '<div class="popup-meta">⏱️ <b>التوقيت:</b> ' + ev.time + '</div>' +
                        '<div class="popup-actions">' +
                            '<a class="popup-link" href="' + earth3dUrl + '" target="_blank">🌍 Google Earth 3D</a>' +
                            '<a class="popup-link secondary" href="' + gmapsUrl + '" target="_blank">📍 Google Maps</a>' +
                        '</div>' +
                    '</div>'
                );
                marker.bindTooltip('[' + ev.urgency + '] ' + ev.location + ': ' + ev.title.substring(0, 45) + '...', {{ direction: 'top', offset: [0, -8] }});
                eventsGroup.addLayer(marker);
            }});

            // 3. رسم السفن والقطع البحرية الحية (AIS Vessels)
            const vesselsData = {vessels_json};
            vesselsData.forEach(function(v) {{
                const shipHtml = '<div style="transform: rotate(' + v.course + 'deg); width:26px; height:26px; display:flex; align-items:center; justify-content:center; background:#0284c7; color:#fff; border:2px solid #38bdf8; border-radius:50%; box-shadow:0 0 12px rgba(56,189,248,0.95); font-size:13px;">🚢</div>';
                const vIcon = L.divIcon({{
                    className: '',
                    html: shipHtml,
                    iconSize: [26, 26],
                    iconAnchor: [13, 13]
                }});

                const vMarker = L.marker([v.lat, v.lon], {{ icon: vIcon }});
                const earth3dUrl = 'https://earth.google.com/web/@' + v.lat + ',' + v.lon + ',100a,12000d,35y,0h,45t,0r';
                const gmapsUrl = 'https://www.google.com/maps?q=' + v.lat + ',' + v.lon + '&hl=ar&t=k&z=12';

                vMarker.bindPopup(
                    '<div class="popup-card">' +
                        '<div class="popup-header">🚢 ' + v.name + ' (MMSI: ' + v.mmsi + ')</div>' +
                        '<div class="popup-meta">📡 <b>مصدر الإشارة:</b> ' + (v.mode_badge || '🟡 محاكاة') + '</div>' +
                        '<div class="popup-meta">⚓ <b>النوع:</b> ' + v.type + '</div>' +
                        '<div class="popup-meta">🏳️ <b>دولة العلم:</b> ' + v.flag + ' | <b>الوجهة:</b> ' + v.dest + '</div>' +
                        '<div class="popup-meta">⚡ <b>السرعة:</b> ' + v.speed + ' عقدة | <b>الاتجاه:</b> ' + v.course + '°</div>' +
                        '<div class="popup-meta">📡 <b>الحالة الملاحية:</b> ' + v.status + '</div>' +
                        '<div class="popup-meta">📍 <b>الإحداثيات:</b> ' + v.lat.toFixed(4) + ', ' + v.lon.toFixed(4) + '</div>' +
                        '<div class="popup-actions">' +
                            '<a class="popup-link" href="' + earth3dUrl + '" target="_blank">🌍 Google Earth 3D</a>' +
                            '<a class="popup-link secondary" href="' + gmapsUrl + '" target="_blank">📍 Google Maps</a>' +
                        '</div>' +
                    '</div>'
                );
                vMarker.bindTooltip('🚢 ' + v.name + ' [' + (v.mode_badge || '🟡 محاكاة') + '] (' + v.speed + ' عقدة → ' + v.dest + ')', {{ direction: 'top', offset: [0, -12] }});
                vesselsGroup.addLayer(vMarker);

                // خط اتجاه حركة السفينة (Heading Vector)
                if (v.speed > 0.5) {{
                    const rad = (90 - v.course) * Math.PI / 180.0;
                    const dLat = 0.22 * Math.sin(rad);
                    const dLon = 0.22 * Math.cos(rad);
                    const line = L.polyline([[v.lat, v.lon], [v.lat + dLat, v.lon + dLon]], {{
                        color: '#38bdf8',
                        weight: 2.2,
                        dashArray: '4, 6'
                    }});
                    vesselsGroup.addLayer(line);
                }}
            }});
        </script>
    </body>
    </html>
    """
    st.components.v1.html(map_html, height=height, scrolling=False)


def render_sources_status_panel(key_prefix="main"):
    """عرض جدول حالة المصادر وأزرار اختبار المصادر وإيقاف/تشغيل أي مصدر."""
    from apis.news_api import NewsAggregator
    from ais.ais_stream_client import AISStreamClient

    news_agg = NewsAggregator()
    ais_client = AISStreamClient()
    src_rows = news_agg.get_sources_status_table()

    # إضافة سطر مصدر AIS البحري إلى جدول حالة المصادر
    ais_live = ais_client.has_api_key()
    src_rows_display = []
    for r in src_rows:
        src_rows_display.append({
            "المصدر": r["المصدر"],
            "النوع": r["النوع"],
            "درجة الثقة": r.get("درجة الثقة", 70),
            "الحالة": r["الحالة"],
            "آخر سحب": r["آخر سحب"],
            "عدد الأخبار": r["عدد الأخبار"],
        })
    src_rows_display.append({
        "المصدر": "رادار الملاحة البحرية (AISStream.io)",
        "النوع": "AIS WebSocket",
        "درجة الثقة": 95 if ais_live else 65,
        "الحالة": "🟢 حي مباشر" if ais_live else "🟡 محاكاة",
        "آخر سحب": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "عدد الأخبار": len(db.get_vessels(limit=100)),
    })

    ctrl_s1, ctrl_s2, ctrl_s3 = st.columns([1.3, 1.8, 1.1])
    with ctrl_s1:
        if st.button("🔄 اختبار المصادر", key=f"{key_prefix}_test_sources_btn", use_container_width=True, type="primary"):
            with st.spinner("جاري فحص كافة خلاصات RSS والتحقق من استجابتها (HTTP 200 + XML)..."):
                results = news_agg.test_all_sources()
                ok_cnt = sum(1 for x in results if "🟢" in x.get("status", ""))
                st.success(f"اكتمل فحص المصادر: {ok_cnt} من أصل {len(results)} مصدر يعمل بنجاح (🟢 متصل).")
                st.rerun()

    with ctrl_s2:
        source_names = [r["المصدر"] for r in src_rows]
        selected_src = st.selectbox(
            "اختر مصدراً لإيقافه أو تشغيله:",
            source_names,
            key=f"{key_prefix}_select_src_toggle",
            label_visibility="collapsed"
        )
    with ctrl_s3:
        if st.button("⏸️ إيقاف/تشغيل مصدر", key=f"{key_prefix}_toggle_src_btn", use_container_width=True):
            curr_row = next((r for r in src_rows if r["المصدر"] == selected_src), None)
            if curr_row is not None:
                new_state = not bool(curr_row.get("enabled", True))
                db.set_source_enabled(selected_src, new_state)
                state_label = "تشغيل (🟢)" if new_state else "إيقاف مؤقت (⏸️)"
                st.info(f"تم {state_label} المصدر: {selected_src}")
                st.rerun()

    df_sources = pd.DataFrame(src_rows_display)
    st.dataframe(
        df_sources[["المصدر", "النوع", "درجة الثقة", "الحالة", "آخر سحب", "عدد الأخبار"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "المصدر": st.column_config.TextColumn("المصدر", width="large"),
            "النوع": st.column_config.TextColumn("النوع", width="small"),
            "درجة الثقة": st.column_config.NumberColumn("درجة الثقة", format="%d", width="small"),
            "الحالة": st.column_config.TextColumn("الحالة", width="medium"),
            "آخر سحب": st.column_config.TextColumn("آخر سحب", width="medium"),
            "عدد الأخبار": st.column_config.NumberColumn("عدد الأخبار", format="%d", width="small"),
        }
    )


# استكمال محتويات الشريط الجانبي (القوائم والتحكم)
with st.sidebar:
    menu = st.radio(
        "لوحات التحكم والعمليات:",
        [
            "غرفة العمليات المركزية (Live Ops)",
            "إدارة وحالة المصادر (Sources Status)",
            "الرادار البحري وتتبع السفن (AIS)",
            "الخريطة الاستخباراتية (Geospatial GIS)",
            "محلل المحتوى والتحقق (NLP Analyzer)",
            "شبكة الكيانات والعلاقات (Network Graph)",
            "محرك إصدار التقارير (Reports Engine)",
            "عن المنصة ومنهجية معطى"
        ]
    )
    
    st.markdown("---")
    st.subheader("⚡ التحكم الميداني السريع")
    if st.button("🚀 تشغيل دورة استخبارات شاملة", use_container_width=True):
        with st.spinner("جاري سحب المصادر المفتوحة، تحليل الكيانات والمشاعر، وتحديث رادار السفن..."):
            importlib.reload(pipeline_runner)
            res = pipeline_runner.run_full_osint_cycle()
            if isinstance(res, dict):
                st.success(f"اكتملت الدورة! تم رصد {res.get('inserted_events', 0)} حدثاً جديداً وتتبع {res.get('active_vessels', 0)} سفينة.")
            else:
                kpis_curr = db.get_kpis()
                st.success(f"اكتملت الدورة بنجاح! إجمالي الأحداث: {kpis_curr['total_events']} | السفن النشطة: {kpis_curr['active_vessels']}")
            st.rerun()

    storage_badge = "☁️ Turso Cloud (SQLite السحابي)" if (hasattr(db, "is_turso_active") and db.is_turso_active()) else "💾 SQLite محلي (Fallback)"
    st.caption(f"🗄️ **محرك التخزين النشط:** `{storage_badge}`")

# استرجاع مؤشرات الأداء والبيانات الأساسية (مع تهيئة أولية تلقائية عند التشغيل لأول مرة على السحابة)
kpis = db.get_kpis()
vessels = db.get_vessels(limit=100)
if not vessels:
    try:
        from ais.ais_stream_client import AISStreamClient
        vessels = AISStreamClient().fetch_vessels(duration_seconds=3).get("vessels", [])
        kpis = db.get_kpis()
    except Exception:
        pass

# ==============================================================================
# الشاشة 1: غرفة العمليات المركزية (Live Ops)
# ==============================================================================
if menu == "غرفة العمليات المركزية (Live Ops)":
    st.markdown(f"""
    <div class='section-header' style="display: flex; align-items: center; gap: 12px;">
        {f'<img src="data:image/svg+xml;base64,{svg_b64}" width="34" height="34" />' if svg_b64 else ''}
        <h2 style="margin: 0; color: {theme_heading_color};">غرفة العمليات والإنذار المبكر (Live Operations Center)</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # شريط القيادة والتحكم الفوري المباشر
    st.markdown(f"""
    <div style="background: {theme_mission_box_bg}; border: 1.5px solid {theme_mission_box_border}; border-radius: 12px; padding: 16px; margin-bottom: 20px; box-shadow: {theme_card_shadow};">
        <div style="display: flex; align-items: center; gap: 10px;">
            {f'<img src="data:image/svg+xml;base64,{svg_b64}" width="22" height="22" />' if svg_b64 else ''}
            <span style="font-size: 1.15rem; font-weight: 700; color: {theme_mission_box_title};">مركز القيادة والتحكم الميداني المباشر (Full-Capacity Mission Control)</span>
        </div>
        <p style="color: {theme_mission_box_text}; font-size: 0.88rem; margin: 6px 0 0 0;">
            تشغيل محركات الرصد العلني بكامل طاقتها لسحب وتحليل الخلاصات المفتوحة (Google News، BBC، الملاحة البحرية، تحذيرات UKMTO، ورادار AIS) وإصدار التقارير بلحظتها.
        </p>
    </div>
    """, unsafe_allow_html=True)

    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 2, 1])
    with ctrl_col1:
        if st.button("⚡ تشغيل دورة استخبارات شاملة بكامل طاقتها", use_container_width=True, type="primary"):
            prog = st.progress(0, text="بدء مسح الخلاصات المتعددة بالتوازي...")
            prog.progress(30, text="سحب الأخبار والبرقيات وتحذيرات الملاحة...")
            importlib.reload(pipeline_runner)
            res = pipeline_runner.run_full_osint_cycle()
            prog.progress(70, text="استخراج الكيانات، تحليل التهديد ومستوى التوتر...")
            prog.progress(100, text="اكتمل التحديث والفهرسة بنجاح!")
            if isinstance(res, dict):
                st.success(f"✅ تم الانتهاء في {res.get('elapsed_seconds', 0)} ثانية! تم مسح وتحليل {res.get('inserted_events', 0)} حدثاً وتحديث {res.get('active_vessels', 0)} سفينة.")
            else:
                kpis_curr = db.get_kpis()
                st.success(f"✅ تم الانتهاء من دورة الرصد بنجاح! إجمالي الأحداث: {kpis_curr['total_events']} | السفن النشطة: {kpis_curr['active_vessels']}")
            st.rerun()

    with ctrl_col2:
        report_choice = st.selectbox(
            "نوع التقرير المراد إصداره فوراً:",
            ["تقدير موقف شامل (SITREP)", "برقية إنذار أمني عاجل (FLASH)", "ملف الرصد البحري (MARITIME)"],
            label_visibility="collapsed"
        )
    with ctrl_col3:
        if st.button("📑 إصدار التقرير فوراً", use_container_width=True):
            r_type = "FLASH" if "FLASH" in report_choice else ("MARITIME" if "MARITIME" in report_choice else "SITREP")
            import reporting.report_generator
            importlib.reload(reporting.report_generator)
            rep_gen = reporting.report_generator.ReportGenerator()
            try:
                report_result = rep_gen.generate_situation_report(report_type=r_type)
            except TypeError:
                report_result = rep_gen.generate_situation_report()
            
            if isinstance(report_result, str):
                filepath = report_result
                with open(filepath, "r", encoding="utf-8") as f:
                    txt = f.read()
                report_result = {
                    "report_id": os.path.basename(filepath),
                    "report_type": r_type,
                    "title": "تقرير تقدير موقف استخباراتي",
                    "md_path": filepath,
                    "html_path": filepath,
                    "md_content": txt,
                    "html_content": f"<pre>{txt}</pre>",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            st.session_state["latest_ops_report"] = report_result
            st.success(f"تم إصدار التقرير {report_result.get('report_id', '')} بنجاح!")

    # نافذة عرض التقرير الصادر من غرفة العمليات إذا تم توليده
    if "latest_ops_report" in st.session_state:
        rep_data = st.session_state["latest_ops_report"]
        with st.expander(f"📄 معاينة التقرير الصادر: {rep_data['title']} ({rep_data['report_id']})", expanded=True):
            st.markdown(rep_data["md_content"])
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                st.download_button(
                    label="⬇️ تحميل التقرير بصيغة Markdown (.md)",
                    data=rep_data["md_content"],
                    file_name=os.path.basename(rep_data["md_path"]),
                    mime="text/markdown",
                    use_container_width=True
                )
            with c_d2:
                st.download_button(
                    label="⬇️ تحميل التقرير بصيغة طباعة رسمية HTML (.html)",
                    data=rep_data["html_content"],
                    file_name=os.path.basename(rep_data["html_path"]),
                    mime="text/html",
                    use_container_width=True
                )

    # شريط كود الإنذار ومستوى التهديد التكتيكي
    crit_count = kpis['critical_events']
    if crit_count >= 15:
        st.markdown(f"""
        <div class="threat-banner-red">
            🚨 <b>كود الإنذار: أحمر (مستوى تهديد حرج)</b> — تم رصد {crit_count} حدثاً أمنياً عاجلاً يتطلب تدقيقاً ومطابقة فورية مع إشارات AIS وتحذيرات UKMTO.
        </div>
        """, unsafe_allow_html=True)
    elif crit_count >= 5:
        st.markdown(f"""
        <div class="threat-banner-orange">
            ⚠️ <b>كود الإنذار: برتقالي (مستوى توتر مرتفع)</b> — رصد {crit_count} أحداث ذات أولوية؛ حركة القوافل التجارية مستمرة بمواكبة أمنية دورية.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="threat-banner-green">
            🟢 <b>كود الإنذار: أخضر (مستوى ملاحة طبيعي)</b> — حركة طبيعية في الممرات المائية والموانئ، وتدفق مستمر لسفن الإغاثة والبضائع.
        </div>
        """, unsafe_allow_html=True)

    # بطاقات مؤشرات الأداء الحية (KPI Cards)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">إجمالي الأحداث المفهرسة</div>
            <div class="metric-val">{kpis['total_events']}</div>
            <div style="color: #0284c7; font-size: 0.8rem; font-weight: 600;">رصد مباشر متعدد المصادر</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">الأحداث العاجلة (أولوية قصوى)</div>
            <div class="metric-val" style="color: #ef4444 !important;">{kpis['critical_events']}</div>
            <div style="color: #ef4444; font-size: 0.8rem; font-weight: 600;">تتطلب استجابة وتثليثاً</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">القطع البحرية قيد التتبع</div>
            <div class="metric-val" style="color: #10b981 !important;">{kpis['active_vessels']}</div>
            <div style="color: #10b981; font-size: 0.8rem; font-weight: 600;">تغطية إشارات AIS الحية</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">نسبة التحقق والتوثيق</div>
            <div class="metric-val" style="color: #8b5cf6 !important;">{kpis['verification_rate']}%</div>
            <div style="color: #8b5cf6; font-size: 0.8rem; font-weight: 600;">وفق نموذج التثليث الميداني</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # لوحة حالة المصادر المفتوحة والتحكم المباشر (المرحلة 2)
    with st.expander("📡 حالة المصادر المفتوحة والتحكم المباشر (RSS اليمنية + البحرية + AIS)", expanded=False):
        render_sources_status_panel(key_prefix="live_ops")

    # أداة التحليل الفوري المباشر داخل غرفة العمليات (In-Ops Live Analyst)
    with st.expander("🔬 المحلل الاستخباري المباشر داخل غرفة العمليات (Live Text & Dispatch Analyst)", expanded=False):
        st.write("أدخل أي بيان، برقية واردة، أو منشور وسائط لتحليله فوراً وفهرسته:")
        quick_input = st.text_area("نص البرقية أو البيان الوارد:", height=90, placeholder="مثال: رصدت هيئة التجارة البحرية UKMTO اقتراب قارب مشبوه من ناقلة نفط غرب المخا بمضيق باب المندب...")
        col_an1, col_an2 = st.columns([3, 1])
        with col_an2:
            auto_save = st.checkbox("حفظ تلقائي في قاعدة البيانات", value=True)
            run_an = st.button("🔍 تحليل فوري", use_container_width=True)
        
        if run_an and quick_input.strip():
            nlp = NLPProcessor()
            sentiment = SentimentAnalyzer()
            gis = SpatialGISAnalyzer()
            
            cleaned = nlp.clean_arabic_text(quick_input)
            ents = nlp.extract_entities(quick_input)
            sent = sentiment.analyze_sentiment(quick_input)
            
            loc_found = "البحر الأحمر"
            for e in ents:
                if e["type"] == "LOCATION":
                    loc_found = e["text"]
                    break
            coords = gis.resolve_location(loc_found)
            dist_to_bab = gis.haversine_distance_nautical_miles(coords[0], coords[1], 12.586, 43.342)

            res_c1, res_c2, res_c3, res_c4 = st.columns(4)
            with res_c1:
                st.metric("نبرة المحتوى", sent["label"])
            with res_c2:
                st.metric("مؤشر التهديد", f"{sent['threat_index']} / 100")
            with res_c3:
                st.metric("الموقع المرصود", loc_found)
            with res_c4:
                st.metric("البعد عن باب المندب", f"{dist_to_bab} ميل بحري")

            st.write("**الكيانات المستخرجة:**")
            if ents:
                st.write(" | ".join([f"`{e['type']}: {e['text']}`" for e in ents]))
            else:
                st.info("لا توجد كيانات مسماة مطابقة للمعجم.")

            if auto_save:
                ev_data = {
                    "title": quick_input[:80] + "...",
                    "raw_content": quick_input,
                    "cleaned_content": cleaned,
                    "source_id": 1,
                    "published_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "event_category": "بحري" if any(w in quick_input for w in ["بحر", "سفينة", "مندب"]) else "أمني",
                    "sentiment_score": sent["score"],
                    "sentiment_label": sent["label"],
                    "urgency_level": "قصوى" if sent["threat_index"] >= 65 else "متوسطة",
                    "fact_check_status": "تحليل غرفة العمليات",
                    "latitude": coords[0],
                    "longitude": coords[1],
                    "location_name": loc_found,
                    "raw_data_url": "داخل غرفة العمليات",
                    "raw_hash": ""
                }
                new_id = db.add_event(ev_data)
                st.success(f"تم حفظ الواقعة بنجاح برقم قيد: #{new_id}")

    # شريط البحث والتصفية الذكي
    st.subheader("🔍 استعراض وتصفية تدفقات الرصد المفتوحة")
    f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
    with f_col1:
        search_kw = st.text_input("بحث بالكلمات المفتاحية:", placeholder="مثال: باب المندب، ناقلة، قمح، UKMTO...")
    with f_col2:
        cat_filter = st.selectbox("تصنيف الحدث:", ["الكل", "بحري", "أمني/عسكري", "إغاثي/تجاري", "سياسي/عام"])
    with f_col3:
        urg_filter = st.selectbox("مستوى الأهمية:", ["الكل", "قصوى", "متوسطة", "روتينية"])

    # استرجاع الأحداث المفلترة
    try:
        events = db.get_events(limit=50, category=cat_filter, urgency=urg_filter, search_query=search_kw)
    except TypeError:
        events = db.get_events(limit=100)
        if cat_filter and cat_filter != "الكل":
            events = [e for e in events if e.get("event_category") == cat_filter]
        if urg_filter and urg_filter != "الكل":
            events = [e for e in events if e.get("urgency_level") == urg_filter]
        if search_kw:
            events = [e for e in events if search_kw.lower() in e.get("title", "").lower() or search_kw.lower() in e.get("raw_content", "").lower() or search_kw.lower() in e.get("location_name", "").lower()]

    # الرسوم البيانية التفاعلية لغرفة العمليات
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("📊 توزيع الأحداث حسب التصنيف")
        if events:
            df_ev = pd.DataFrame(events)
            cat_counts = df_ev['event_category'].value_counts().reset_index()
            cat_counts.columns = ['التصنيف', 'العدد']
            fig_pie = px.pie(cat_counts, values='العدد', names='التصنيف', hole=0.45,
                             color_discrete_sequence=px.colors.sequential.Teal)
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=theme_plotly_font), template=theme_plotly_template)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("لا توجد بيانات أحداث لعرضها حالياً.")

    with col_chart2:
        st.subheader("📈 مؤشر التوتر ومستوى الأهمية")
        if events:
            df_ev = pd.DataFrame(events)
            fig_bar = px.histogram(df_ev, x='sentiment_label', color='urgency_level',
                                  color_discrete_map={'قصوى': '#ef4444', 'متوسطة': '#f59e0b', 'روتينية': '#10b981'},
                                  labels={'sentiment_label': 'نبرة المحتوى', 'count': 'عدد المنشورات'})
            fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=theme_plotly_font), template=theme_plotly_template)
            st.plotly_chart(fig_bar, use_container_width=True)

    # جدول وتفاصيل الرصد اللحظي المباشر وقراءة الأحداث
    ev_head_col1, ev_head_col2 = st.columns([3, 1])
    with ev_head_col1:
        st.subheader(f"📡 تدفق الرصد اللحظي المفهرس ({len(events)} واقعة)")
    with ev_head_col2:
        if events:
            csv_events_bytes = pd.DataFrame(events).to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="⬇️ تصدير الأحداث لـ Excel (.CSV)",
                data=csv_events_bytes,
                file_name=f"osint_events_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
    if events:
        nlp_reader = NLPProcessor()
        for ev in events[:15]:
            badge_class = "status-badge-critical" if ev["urgency_level"] == "قصوى" else ("status-badge-verified" if ev["urgency_level"] == "متوسطة" else "status-badge-routine")
            
            with st.container():
                st.markdown(f"""
                <div style="background: {theme_event_card_bg}; border: 1px solid {theme_event_card_border}; border-radius: 10px; padding: 14px; margin-bottom: 8px; box-shadow: {theme_card_shadow};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 1.05rem; font-weight: 700; color: {theme_event_card_title};">#{ev['id']} — {ev['title']}</span>
                        <span class="{badge_class}">{ev['urgency_level']}</span>
                    </div>
                    <div style="display: flex; gap: 15px; font-size: 0.82rem; color: {theme_event_card_meta}; margin-top: 8px;">
                        <span>📍 <b>الموقع:</b> {ev['location_name']}</span>
                        <span>🏷️ <b>التصنيف:</b> {ev['event_category']}</span>
                        <span>✅ <b>التحقق:</b> {ev['fact_check_status']}</span>
                        <span>⏱️ <b>التوقيت:</b> {ev['captured_at']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"📖 قراءة وتحليل الواقعة #{ev['id']}: {ev['title'][:60]}..."):
                    st.write("**النص الكامل المرصود:**")
                    st.info(ev["raw_content"])
                    
                    ev_ents = nlp_reader.extract_entities(ev["raw_content"])
                    c_det1, c_det2 = st.columns(2)
                    with c_det1:
                        st.write("**الكيانات المستخرجة (NER):**")
                        if ev_ents:
                            for ent in ev_ents:
                                st.markdown(f"- 🏷️ `{ent['type']}`: **{ent['text']}** (ثقة: {int(ent['confidence']*100)}%)")
                        else:
                            st.write("لم تُرصد كيانات مخصصة في هذا النص.")
                    with c_det2:
                        st.write("**التقييم الاستخباري والمكاني:**")
                        lat_v = ev.get('latitude', 13.5) or 13.5
                        lon_v = ev.get('longitude', 43.5) or 43.5
                        st.write(f"- نبرة النص: **{ev.get('sentiment_label', 'محايد')}**")
                        st.write(f"- الإحداثيات: `{lat_v:.3f}, {lon_v:.3f}`")
                        st.markdown(f"- 🌍 [فتح موقع الحدث على Google Earth 3D](https://earth.google.com/web/@{lat_v},{lon_v},300a,25000d,35y,0h,40t,0r)")
                        if ev.get("raw_data_url") and ev.get("raw_data_url").startswith("http"):
                            st.markdown(f"- 🌐 [زيارة الرابط الأصلي للخبر في المصدر المفتوح]({ev['raw_data_url']})")
    else:
        st.info("لا توجد أحداث مطابقة لشروط البحث والتصفية.")

# ==============================================================================
# شاشة إدارة وحالة المصادر المفتوحة (Sources Status & Control)
# ==============================================================================
elif menu == "إدارة وحالة المصادر (Sources Status)":
    st.markdown(f"""
    <div class='section-header' style="display: flex; align-items: center; gap: 12px;">
        {f'<img src="data:image/svg+xml;base64,{svg_b64}" width="32" height="32" />' if svg_b64 else ''}
        <h2 style="margin: 0; color: {theme_heading_color};">حالة المصادر المفتوحة والتحكم المباشر (Sources Status & Control)</h2>
    </div>
    """, unsafe_allow_html=True)
    st.write("مراقبة حية لحالة كافة مصادر الرصد المفتوحة (المصادر اليمنية المباشرة بدرجة ثقة 90، المصادر البحرية والأمنية الدولية بدرجة ثقة 70، وخلاصات Google News الوسيطة بدرجة ثقة 60) مع إمكانية اختبار الاتصال أو إيقاف/تشغيل أي مصدر.")

    render_sources_status_panel(key_prefix="sources_page")

    st.markdown("---")
    with st.expander("🛡️ سجل الأخبار المستبعدة بواسطة فلتر الصلة اليمنية (rejected_news)", expanded=False):
        rej_items = db.get_rejected_news(limit=50)
        if rej_items:
            df_rej = pd.DataFrame(rej_items)
            st.dataframe(
                df_rej[["id", "title", "source", "rejection_reason", "matched_exclude", "rejected_at"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("لا توجد أخبار مستبعدة مسجلة حالياً.")

# ==============================================================================
# الشاشة 2: الرادار البحري وتتبع السفن (على خريطة Google Earth الحقيقية)
# ==============================================================================
elif menu == "الرادار البحري وتتبع السفن (AIS)":
    st.markdown(f"""
    <div class='section-header' style="display: flex; align-items: center; gap: 12px;">
        {f'<img src="data:image/svg+xml;base64,{svg_b64}" width="32" height="32" />' if svg_b64 else ''}
        <h2 style="margin: 0; color: {theme_heading_color};">الرادار البحري وتتبع الملاحة على Google Earth (Maritime AIS Radar)</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("مراقبة حية لحركة القطع البحرية وناقلات النفط وسفن البضائع على صور الأقمار الصناعية الحقيقية (Google Earth Satellite Hybrid) في مضيق باب المندب، البحر الأحمر، وخليج عدن.")
    
    if vessels:
        df_v = pd.DataFrame(vessels)
        df_v["mode_badge"] = df_v.apply(
            lambda r: r.get("mode_badge") or ("🟢 حي مباشر" if int(r.get("is_live", 0) or 0) == 1 else "🟡 محاكاة"),
            axis=1
        )
        any_live = any(int(v.get("is_live", 0) or 0) == 1 for v in vessels)
        if any_live:
            st.success("🟢 **وضع الرادار البحري: حي مباشر (AISStream.io WebSocket)** — يتم استقبال إشارات السفن الحقيقية مباشرة من مضيق باب المندب والبحر الأحمر.")
        else:
            st.info("🟡 **وضع الرادار البحري: محاكاة (`🟡 محاكاة`)** — يعمل النظام حالياً ببيانات محاكاة ملاحية. لتفعيل البث الحي المجاني، ضع مفتاح `AISSTREAM_API_KEY` في ملف `.env`.")
        
        ais_col1, ais_col2, ais_col3 = st.columns([2, 1, 1])
        with ais_col1:
            ais_layer_choice = st.selectbox(
                "🌍 نمط خريطة قوقل إيرث للرادار البحري:",
                [
                    "🌍 قوقل إيرث هجين — قمر صناعي مع أسماء الموانئ والممرات (Google Earth Hybrid)",
                    "🛰️ قوقل إيرث صافي — صور أقمار صناعية عالية الدقة (Google Earth Satellite)",
                    "🏔️ قوقل إيرث تضاريس — الأعماق والسواحل (Google Terrain)",
                    "🗺️ خرائط قوقل التفصيلية (Google Maps)"
                ]
            )
        with ais_col2:
            show_ports_ais = st.checkbox("⚓ إظهار الموانئ ونطاقات الرصد", value=True)
        with ais_col3:
            kml_ais = generate_google_earth_kml([], vessels)
            st.download_button(
                label="⬇️ تصدير الأسطول لـ Google Earth (.KML)",
                data=kml_ais,
                file_name=f"maritime_ais_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.kml",
                mime="application/vnd.google-earth.kml+xml",
                use_container_width=True
            )

        layer_code = "hybrid"
        if "صافي" in ais_layer_choice:
            layer_code = "satellite"
        elif "تضاريس" in ais_layer_choice:
            layer_code = "terrain"
        elif "التفصيلية" in ais_layer_choice:
            layer_code = "roadmap"

        # عرض خريطة قوقل إيرث الحقيقية للرادار البحري
        render_google_earth_map(
            events_list=[],
            vessels_list=vessels,
            show_ports=show_ports_ais,
            default_layer=layer_code,
            center_lat=13.5,
            center_lon=43.8,
            zoom=6,
            height=660,
            is_dark=is_dark
        )

        v_head_c1, v_head_c2, v_head_c3 = st.columns([2.4, 1.1, 1.1])
        with v_head_c1:
            st.subheader(f"📋 سجل أسطول السفن المرصود ({len(vessels)} قطعة بحرية نشطة)")
        with v_head_c2:
            if st.button("📡 تحديث إشارات AIS الآن", use_container_width=True):
                from ais.ais_stream_client import AISStreamClient
                with st.spinner("جاري التقاط أحدث إشارات AIS الملاحية..."):
                    AISStreamClient().fetch_vessels(duration_seconds=5)
                st.rerun()
        with v_head_c3:
            csv_vessels_bytes = df_v[['mode_badge', 'mmsi', 'vessel_name', 'vessel_type', 'flag_country', 'destination', 'speed_knots', 'nav_status', 'last_signal_at']].to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="⬇️ تصدير الأسطول لـ Excel (.CSV)",
                data=csv_vessels_bytes,
                file_name=f"ais_vessels_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        df_v_display = df_v[['mode_badge', 'mmsi', 'vessel_name', 'vessel_type', 'flag_country', 'destination', 'speed_knots', 'nav_status', 'last_signal_at']].rename(columns={
            'mode_badge': 'حالة الإشارة',
            'mmsi': 'رقم MMSI',
            'vessel_name': 'اسم السفينة',
            'vessel_type': 'النوع',
            'flag_country': 'دولة العلم',
            'destination': 'الوجهة',
            'speed_knots': 'السرعة (عقدة)',
            'nav_status': 'الحالة الملاحية',
            'last_signal_at': 'آخر إشارة',
        })
        st.dataframe(
            df_v_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "حالة الإشارة": st.column_config.TextColumn("حالة الإشارة", width="small"),
                "رقم MMSI": st.column_config.NumberColumn("رقم MMSI", format="%d", width="small"),
                "اسم السفينة": st.column_config.TextColumn("اسم السفينة", width="medium"),
                "النوع": st.column_config.TextColumn("النوع", width="medium"),
                "دولة العلم": st.column_config.TextColumn("دولة العلم", width="small"),
                "الوجهة": st.column_config.TextColumn("الوجهة", width="small"),
                "السرعة (عقدة)": st.column_config.NumberColumn("السرعة (عقدة)", format="%.1f", width="small"),
                "الحالة الملاحية": st.column_config.TextColumn("الحالة الملاحية", width="medium"),
                "آخر إشارة": st.column_config.TextColumn("آخر إشارة", width="medium"),
            }
        )
    else:
        st.warning("لا توجد بيانات سفن متوفرة حالياً.")

# ==============================================================================
# الشاشة 3: الخريطة الاستخباراتية المكانية على Google Earth الحقيقي
# ==============================================================================
elif menu == "الخريطة الاستخباراتية (Geospatial GIS)":
    st.markdown(f"""
    <div class='section-header' style="display: flex; align-items: center; gap: 12px;">
        {f'<img src="data:image/svg+xml;base64,{svg_b64}" width="32" height="32" />' if svg_b64 else ''}
        <h2 style="margin: 0; color: {theme_heading_color};">الخريطة الاستخباراتية المكانية — قوقل إيرث (Google Earth Geospatial Intelligence)</h2>
    </div>
    """, unsafe_allow_html=True)
    
    events_all = db.get_events(limit=250)
    if events_all:
        # شريط أدوات الخريطة الاستخباراتية (فلاتر + اختيار طبقة قوقل إيرث + تصدير KML)
        g_col1, g_col2, g_col3, g_col4 = st.columns([2.2, 1.1, 1.1, 1.2])
        with g_col1:
            geo_layer_mode = st.selectbox(
                "🌍 نمط العرض على قوقل إيرث (Google Earth Mode):",
                [
                    "🌍 قوقل إيرث هجين — قمر صناعي واقعي + المسميات والحدود (Google Earth Hybrid)",
                    "🛰️ قوقل إيرث صافي — قمر صناعي عالي الوضوح (Google Earth Satellite)",
                    "🏔️ قوقل إيرث تضاريس — الجبال والسواحل الطبيعية (Google Terrain)",
                    "🗺️ خرائط قوقل القياسية — الطرق والمدن (Google Maps)"
                ]
            )
        with g_col2:
            geo_urg_filter = st.selectbox(
                "🎯 تصفية حسب الأولوية:",
                ["الكل", "قصوى", "متوسطة", "روتينية"]
            )
        with g_col3:
            include_vessels_on_gis = st.checkbox("🚢 دمج رادار السفن AIS", value=True)
            include_ports_on_gis = st.checkbox("⚓ إظهار الموانئ والمضايق", value=True)
        with g_col4:
            kml_full = generate_google_earth_kml(events_all, vessels if include_vessels_on_gis else [])
            st.download_button(
                label="⬇️ تحميل لبرنامج Google Earth (.KML)",
                data=kml_full,
                file_name=f"platform_ox_earth_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.kml",
                mime="application/vnd.google-earth.kml+xml",
                use_container_width=True
            )

        filtered_geo_events = events_all
        if geo_urg_filter != "الكل":
            filtered_geo_events = [e for e in events_all if e.get("urgency_level") == geo_urg_filter]

        g_layer = "hybrid"
        if "صافي" in geo_layer_mode:
            g_layer = "satellite"
        elif "تضاريس" in geo_layer_mode:
            g_layer = "terrain"
        elif "القياسية" in geo_layer_mode:
            g_layer = "roadmap"

        # عرض الخريطة الحقيقية والواضحة على Google Earth
        render_google_earth_map(
            events_list=filtered_geo_events,
            vessels_list=vessels if include_vessels_on_gis else [],
            show_ports=include_ports_on_gis,
            default_layer=g_layer,
            center_lat=14.2,
            center_lon=44.2,
            zoom=6,
            height=690,
            is_dark=is_dark
        )

        st.caption("💡 يمكنك النقر على أي حدث أو سفينة أو ميناء فوق خريطة قوقل إيرث لاستعراض بطاقة المعلومات الكاملة، أو فتح الموقع مباشرة في Google Earth 3D، أو التبديل بين طبقات الأقمار الصناعية من أعلى يسار الخريطة.")
    else:
        st.info("لا توجد أحداث بإحداثيات مكانية للعرض.")

# ==============================================================================
# الشاشة 4: محلل المحتوى والتحقق الفوري
# ==============================================================================
elif menu == "محلل المحتوى والتحقق (NLP Analyzer)":
    st.markdown(f"""
    <div class='section-header' style="display: flex; align-items: center; gap: 12px;">
        {f'<img src="data:image/svg+xml;base64,{svg_b64}" width="32" height="32" />' if svg_b64 else ''}
        <h2 style="margin: 0; color: {theme_heading_color};">محلل المحتوى والتحقق الفوري (NLP & Fact-Checking Engine)</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("أداة لتحليل أي نص، منشور، أو تغريدة، واستخراج الكيانات، وقياس مستوى التوتر والتهديد، وإصدار توصية تحقق فورية.")
    
    user_input = st.text_area("أدخل النص أو المنشور المراد تحليله:", height=130, 
                              placeholder="مثال: رصدت هيئة التجارة البحرية البريطانية اقتراب زورق مجهول من سفينة تجارية غرب ميناء الحديدة في البحر الأحمر...")
    
    if st.button("🔍 تحليل النص واستخراج الرؤى الاستخباراتية", use_container_width=True):
        if user_input.strip():
            nlp = NLPProcessor()
            sentiment = SentimentAnalyzer()
            gis = SpatialGISAnalyzer()
            
            cleaned = nlp.clean_arabic_text(user_input)
            entities = nlp.extract_entities(user_input)
            sent = sentiment.analyze_sentiment(user_input)
            
            res_c1, res_c2, res_c3, res_c4 = st.columns(4)
            with res_c1:
                st.metric("نبرة المحتوى", sent["label"])
            with res_c2:
                st.metric("مؤشر التوتر", sent["tension_level"])
            with res_c3:
                st.metric("مؤشر التهديد", f"{sent.get('threat_index', 20)}/100")
            with res_c4:
                st.metric("عدد الكيانات المرصودة", len(entities))
                
            st.subheader("🏷️ الكيانات المسماة المستخرجة (NER)")
            if entities:
                ent_df = pd.DataFrame(entities)
                st.dataframe(ent_df, use_container_width=True)
            else:
                st.info("لم يتم رصد كيانات مطابقة في المعجم الحالي.")

            st.subheader("🛡️ توصية التحقق (Fact-Checking Assessment)")
            if sent["tension_level"] in ["قصوى", "مرتفع"] and len(entities) > 0:
                st.warning("⚠️ **توصية:** يحتوي النص على إشارات أمنية عالية التوتر. يلزم التثليث الميداني ومطابقة إشارات AIS للتحقق من الواقعة قبل الاعتماد والنشر.")
            else:
                st.success("✅ **توصية:** المحتوى روتيني/طبيعي، لا تظهر مؤشرات تحريض أو شائعات عاجلة.")
        else:
            st.error("يرجى إدخال نص أولاً للبدء في التحليل.")

# ==============================================================================
# الشاشة 5: شبكة الكيانات والعلاقات
# ==============================================================================
elif menu == "شبكة الكيانات والعلاقات (Network Graph)":
    st.markdown(f"""
    <div class='section-header' style="display: flex; align-items: center; gap: 12px;">
        {f'<img src="data:image/svg+xml;base64,{svg_b64}" width="32" height="32" />' if svg_b64 else ''}
        <h2 style="margin: 0; color: {theme_heading_color};">شبكة الكيانات والارتباطات (Intelligence Link Analysis)</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("تفكيك وتتبع خيوط العلاقات بين الأحداث والمواقع والجهات الفاعلة.")
    
    events_for_graph = db.get_events(limit=80)
    if events_for_graph:
        graph = EntityNetworkGraph()
        graph.build_from_events(events_for_graph)
        top_nodes = graph.get_top_central_nodes(top_n=8)
        
        st.subheader("🌟 العقد والمواقع الأكثر مركزية وتأثيراً (Top Influential Hubs)")
        c_nodes = st.columns(len(top_nodes)) if len(top_nodes) <= 5 else st.columns(5)
        for i, node in enumerate(top_nodes[:5]):
            with c_nodes[i]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{node['type']}</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: {theme_metric_val};">{node['label']}</div>
                    <div style="color: {theme_muted_color}; font-size: 0.8rem;">تكرار: {node['degree']} روابط</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📁 تصدير شبكة العلاقات لبرنامج Gephi")
        gexf_content = graph.export_gexf()
        st.download_button(
            label="⬇️ تحميل ملف الشبكة بصيغة Gephi (.GEXF)",
            data=gexf_content,
            file_name=f"osint_network_{datetime.datetime.now().strftime('%Y%m%d')}.gexf",
            mime="application/xml",
            use_container_width=True
        )
    else:
        st.info("لا توجد أحداث كافية لبناء شبكة العلاقات.")

# ==============================================================================
# الشاشة 6: محرك إصدار التقارير
# ==============================================================================
elif menu == "محرك إصدار التقارير (Reports Engine)":
    st.markdown(f"""
    <div class='section-header' style="display: flex; align-items: center; gap: 12px;">
        {f'<img src="data:image/svg+xml;base64,{svg_b64}" width="32" height="32" />' if svg_b64 else ''}
        <h2 style="margin: 0; color: {theme_heading_color};">محرك التقارير الاستخباراتية (Intelligence Reports Engine)</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("إصدار وتوثيق تقارير تقدير الموقف والبرقيات العاجلة وفق منهجية مركز معطى.")
    
    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        rep_type_select = st.selectbox(
            "اختر نوع الوثيقة الاستخباراتية المراد إصدارها:",
            [
                "تقرير تقدير موقف استخباراتي شامل (SITREP)",
                "برقية إنذار أمني عاجل (FLASH)",
                "ملف الرصد البحري وحركة الملاحة (MARITIME)"
            ]
        )
    with col_t2:
        st.write("")
        st.write("")
        gen_btn = st.button("⚡ توليد وتوثيق الوثيقة الآن", use_container_width=True, type="primary")

    if gen_btn:
        r_type = "FLASH" if "FLASH" in rep_type_select else ("MARITIME" if "MARITIME" in rep_type_select else "SITREP")
        import reporting.report_generator
        importlib.reload(reporting.report_generator)
        rep = reporting.report_generator.ReportGenerator()
        try:
            rep_dict = rep.generate_situation_report(report_type=r_type)
        except TypeError:
            rep_dict = rep.generate_situation_report()

        if isinstance(rep_dict, str):
            filepath = rep_dict
            with open(filepath, "r", encoding="utf-8") as f:
                txt = f.read()
            rep_dict = {
                "report_id": os.path.basename(filepath),
                "report_type": r_type,
                "title": "تقرير تقدير موقف استخباراتي",
                "md_path": filepath,
                "html_path": filepath,
                "md_content": txt,
                "html_content": f"<pre>{txt}</pre>",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        st.session_state["active_report"] = rep_dict
        st.success(f"تم إصدار وتوثيق التقرير بنجاح: {rep_dict.get('report_id', '')}")

    if "active_report" in st.session_state:
        rep_dict = st.session_state["active_report"]
        
        c_act1, c_act2 = st.columns(2)
        with c_act1:
            st.download_button(
                label="⬇️ تحميل التقرير بصيغة Markdown (.md)",
                data=rep_dict["md_content"],
                file_name=os.path.basename(rep_dict["md_path"]),
                mime="text/markdown",
                use_container_width=True
            )
        with c_act2:
            st.download_button(
                label="⬇️ تحميل التقرير بصيغة طباعة رسمية HTML (.html)",
                data=rep_dict["html_content"],
                file_name=os.path.basename(rep_dict["html_path"]),
                mime="text/html",
                use_container_width=True
            )

        tab_md, tab_html = st.tabs(["معاينة التقرير (Markdown)", "معاينة الطباعة الرسمية (HTML)"])
        with tab_md:
            st.markdown(rep_dict["md_content"])
        with tab_html:
            st.components.v1.html(rep_dict["html_content"], height=700, scrolling=True)

    # أرشيف التقارير السابقة المحفوظة
    st.markdown("---")
    st.subheader("🗄️ أرشيف التقارير والوثائق الصادرة")
    reports_dir = os.path.join(APP_DIR, "..", "reporting", "generated_reports")
    if os.path.exists(reports_dir):
        files = sorted(glob.glob(os.path.join(reports_dir, "*.md")), reverse=True)
        if files:
            for f in files[:8]:
                fname = os.path.basename(f)
                fsize = os.path.getsize(f)
                ftime = datetime.datetime.fromtimestamp(os.path.getmtime(f)).strftime('%Y-%m-%d %H:%M:%S')
                with open(f, "r", encoding="utf-8") as fr:
                    content_read = fr.read()
                col_arch1, col_arch2 = st.columns([3, 1])
                with col_arch1:
                    st.write(f"📄 **{fname}** — `{ftime}` ({fsize} بايت)")
                with col_arch2:
                    st.download_button(
                        label=f"⬇️ تحميل {fname}",
                        data=content_read,
                        file_name=fname,
                        mime="text/markdown",
                        key=f"arch_{fname}"
                    )
        else:
            st.info("لم تصدر أي تقارير مؤرشفة بعد.")

# ==============================================================================
# الشاشة 7: عن المنصة ومنهجية معطى
# ==============================================================================
elif menu == "عن المنصة ومنهجية معطى":
    st.markdown(f"""
    <div class='section-header' style="display: flex; align-items: center; gap: 12px;">
        {f'<img src="data:image/svg+xml;base64,{svg_b64}" width="32" height="32" />' if svg_b64 else ''}
        <h2 style="margin: 0; color: {theme_heading_color};">عن نظام الرصد العلني Platform OX ومنهجية مركز معطى</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    ### 🎯 الرؤية والرسالة
    **Platform OX** هي منصة استخبارات مفتوحة المصدر (OSINT) مبنية وفق المعايير المعمارية العالمية، ومصممة لدعم الرصد اللحظي، التحليل الاستخباراتي، وتتبع التحركات البحرية وحركة الرأي العام.

    ---

    ### 🔄 منهجية مركز "معطى" الخماسية المعتمدة:
    1. **تحديد الموضوع (Topic Identification):** تحديد نطاق الرصد، الأولويات، والمصادر المستهدفة.
    2. **التصميم (Taxonomy & Design):** هندسة المعاجم اللغوية، الفلاتر، وقواعد الاستبعاد.
    3. **الجمع (Data Acquisition):** كشط الويب، واجهات البرمجة، بيانات تتبع السفن AIS، والحساسات.
    4. **التحليل (Analysis & Verification):** معالجة اللغة الطبيعية، تحليل المشاعر، التحديد المكاني، ومكافحة الشائعات.
    5. **التقرير (Reporting & Dissemination):** لوحات تحكم تفاعلية، خرائط، وتقارير تقدير موقف موثقة.

    ---

    ### 🛠️ مصادر الرصد العلني المجانية المدمجة (19 مصدراً + رادار AIS):
    * **المصادر اليمنية المباشرة (8 خلاصات بدرجة ثقة 90):** سبأ نت، عدن الغد، الموقع بوست، المشهد اليمني، يمن مونيتور، يمن شباب نت، يمن برس وعدن حرة.
    * **المصادر البحرية والأمنية والإغاثية الدولية (بدرجة ثقة 70–85):** The Maritime Executive، gCaptain، USNI News، Naval News، Splash247، ومرصد الشؤون الإنسانية في اليمن (ReliefWeb).
    * **خلاصات المراقبة الإقليمية:** Google News (شؤون اليمن، البحر الأحمر، باب المندب، الموانئ، التحالفات البحرية) وBBC Arabic.
    * **فلتر الصلة اليمنية (`Yemen Relevance Filter`):** يُطبَّق حصرياً على قسم `سياسي/عام` لمنع تسرب الأخبار الفنية والتقنية والرياضية غير اليمنية وعزلها في سجل المرفوضات (`rejected_news`).
    * **الرادار البحري المفتوح (`Google Earth & AISStream.io`):** تتبع حركة السفن وناقلات الطاقة وسفن الإغاثة على خريطة قوقل إيرث التفاعلية (بث حي `🟢 حي مباشر` أو محاكاة `🟡 محاكاة`).
    * **الذاكرة السحابية الدائمة (`Turso / SQLite`):** حفظ آمن ومستمر للأحداث والسفن والمرفوضات مع منع التكرار ببصمة `SHA-256`.
    """)
