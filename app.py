# -*- coding: utf-8 -*-
"""
نقطة الدخول الجذرية لمنصة الرصد العلني (Platform OX — OSINT Hub)
مخصصة للتشغيل المباشر على Hugging Face Spaces (app_file: app.py) أو محلياً عبر:
    streamlit run app.py
تقوم بتحميل وتشغيل الواجهة الكاملة في 06_presentation/streamlit_app/app.py
مع الحفاظ الكامل على المسارات والهوية البصرية وكافة الميزات.
"""

import os
import sys
import runpy

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
for sub in ["01_acquisition", "02_storage", "03_processing", "04_orchestration", "06_presentation"]:
    p = os.path.join(ROOT_DIR, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

STREAMLIT_APP_PATH = os.path.join(ROOT_DIR, "06_presentation", "streamlit_app", "app.py")
runpy.run_path(STREAMLIT_APP_PATH, run_name="__main__")

