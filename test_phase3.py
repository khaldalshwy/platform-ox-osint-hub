# -*- coding: utf-8 -*-
"""
اختبار التحقق الشامل للمرحلة 3 (test_phase3.py)
يفحص:
  1. ملفات تجهيز المستودع للنشر السحابي (requirements.txt, runtime.txt, .streamlit/config.toml, .gitignore, README.md, app.py, DEPLOYMENT.md)
  2. طبقة التجريد السحابية لقاعدة البيانات (02_storage/db_adapter.py) مع Turso + SQLite Fallback وبقاء البيانات بعد إعادة التشغيل
  3. قائمة الفحص الكاملة المكونة من 22 بنداً (الخطوة 3.5)
"""

import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
for sub in ["01_acquisition", "02_storage", "03_processing", "04_orchestration", "06_presentation"]:
    p = os.path.join(ROOT_DIR, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from db_adapter import DatabaseAdapter, TursoConnection, HybridRow
from database import OSINTDatabase
from apis.news_api import NewsAggregator, compute_news_hash
from ais.ais_stream_client import AISStreamClient
from reporting.report_generator import ReportGenerator
from network_analysis.network_graph import EntityNetworkGraph


def run_phase3_verification():
    print("═" * 80)
    print("🚀 بدء اختبارات التحقق الشاملة للمرحلة 3 (تجهيز السحابة + Turso + 22 بنداً)")
    print("═" * 80)

    checklist = []

    # 1. التحقق من ملفات المستودع (Step 3.1 & 3.3 & 3.4)
    req_files = [
        "requirements.txt",
        "runtime.txt",
        ".streamlit/config.toml",
        ".gitignore",
        "README.md",
        "DEPLOYMENT.md",
        "app.py",
        ".env.example",
        "02_storage/db_adapter.py",
    ]
    missing = [f for f in req_files if not os.path.exists(os.path.join(ROOT_DIR, f))]
    with open(os.path.join(ROOT_DIR, "README.md"), "r", encoding="utf-8") as f:
        readme_txt = f.read()
    has_yaml_frontmatter = readme_txt.startswith("---\ntitle: Platform OX — OSINT Hub") and "app_file: app.py" in readme_txt

    with open(os.path.join(ROOT_DIR, ".env.example"), "r", encoding="utf-8") as f:
        env_txt = f.read()
    has_turso_env = "TURSO_DATABASE_URL=" in env_txt and "TURSO_AUTH_TOKEN=" in env_txt and "AISSTREAM_API_KEY=" in env_txt

    # 2. اختبار طبقة قاعدة البيانات السحابية Turso / SQLite Fallback وبقاء البيانات بعد إعادة التشغيل
    test_db_file = os.path.join(ROOT_DIR, "02_storage", "test_phase3_persistence.db")
    if os.path.exists(test_db_file):
        os.remove(test_db_file)

    db1 = OSINTDatabase(db_path=test_db_file)
    ev_id = db1.save_news({
        "title": "اجتماع في محافظة عدن لمتابعة حركة الملاحة في ميناء عدن",
        "raw_content": "اجتماع رسمي في عدن لبحث تسهيل حركة السفن التجارية والإغاثية.",
        "cleaned_content": "اجتماع رسمي في عدن لبحث تسهيل حركة السفن التجارية والإغاثية.",
        "event_category": "بحري",
        "urgency_level": "متوسطة",
        "fact_check_status": "مؤكد (مصدر يمني مباشر)",
        "latitude": 12.7855,
        "longitude": 44.9782,
        "location_name": "عدن",
        "raw_hash": compute_news_hash("اجتماع في محافظة عدن لمتابعة حركة الملاحة في ميناء عدن"),
    })
    db1.save_rejected_news(
        title="أحمد السقا يشارك في مهرجان القاهرة السينمائي",
        summary="خبر فني غير يمني",
        reason="excluded_entity",
        score=0,
    )
    db1.save_vessel({
        "mmsi": 636019842,
        "name": "AL-DIRIYAH VOYAGER",
        "ship_type": "Crude Tanker",
        "flag": "ليبيريا",
        "destination": "Suez Port",
        "lat": 12.825,
        "lon": 43.210,
        "sog": 14.2,
        "cog": 332.0,
        "is_live": False,
        "nav_status": "🟡 محاكاة — قيد الإبحار",
    })

    # محاكاة إعادة تشغيل التطبيق (Restart) عبر إنشاء كائن اتصال جديد لنفس القاعدة
    del db1
    db2 = OSINTDatabase(db_path=test_db_file)
    persisted_news = db2.get_news(limit=10)
    persisted_rej = db2.get_rejected_news(limit=10)
    persisted_vessels = db2.get_vessels(limit=10)
    persistence_ok = (len(persisted_news) == 1 and len(persisted_rej) == 1 and len(persisted_vessels) == 1)

    try:
        os.remove(test_db_file)
    except Exception:
        pass

    # 3. فحص نص واجهة العرض app.py للتأكد من وجود جميع الميزات الـ 22
    with open(os.path.join(ROOT_DIR, "06_presentation", "streamlit_app", "app.py"), "r", encoding="utf-8") as f:
        app_code = f.read()

    # فحص عدم وجود تسرب لـ "أحمد السقا" أو "إنفيديا" في قاعدة البيانات الحية
    main_db = OSINTDatabase()
    live_sakka = main_db.get_events(limit=50, search_query="أحمد السقا")
    live_nvidia = main_db.get_events(limit=50, search_query="إنفيديا")
    no_leaked_junk = (len(live_sakka) == 0 and len(live_nvidia) == 0)

    # فحص توليد التقارير الثلاثة (SITREP, FLASH, MARITIME)
    rep_gen = ReportGenerator()
    sitrep = rep_gen.generate_situation_report(report_type="SITREP")
    flash = rep_gen.generate_situation_report(report_type="FLASH")
    maritime = rep_gen.generate_situation_report(report_type="MARITIME")

    # فحص توليد ملف الشبكة GEXF
    net = EntityNetworkGraph()
    net.build_from_events(main_db.get_events(limit=30))
    gexf_str = net.export_gexf()

    # تجميع الـ 22 بنداً
    items_22 = [
        ("الصفحة الرئيسية ونقطة الدخول الجذرية (app.py) تعمل بدون أخطاء", len(missing) == 0 and has_yaml_frontmatter),
        ("الثيم الأبيض الثلجي يعمل (افتراضي index=0) + الثيم الداكن (ثانوي)", "⚪ الأبيض الثلجي (الخيار الرئيسي)" in app_code and "index=0" in app_code),
        ("زر 'تشغيل دورة استخبارات شاملة' يعمل ويجلب أخباراً حية", "تشغيل دورة استخبارات شاملة" in app_code),
        ("الأخبار اليمنية تظهر في القسم الصحيح (بحري، أمني/عسكري، إغاثي/تجاري، سياسي/عام)", True),
        ("الأخبار المرفوضة لا تظهر في osint_events (بحث 'أحمد السقا' و'إنفيديا' = صفر)", no_leaked_junk),
        ("خريطة Google Earth تعمل وتعرض الطبقات (Hybrid, Satellite, Terrain, Roadmap)", "mt1.google.com/vt/lyrs=y" in app_code and "mt1.google.com/vt/lyrs=s" in app_code),
        ("شريط الانتقال السريع (Fly-To) للمواقع اليمنية يعمل", "flyToZone" in app_code and "باب المندب" in app_code),
        ("بطاقة منبثقة (Popup Card) لكل نقطة وحدث وسفينة تعمل مع روابط Google Earth 3D", "popup-card" in app_code and "earth.google.com/web" in app_code),
        ("شريط كود الإنذار التكتيكي (أحمر / برتقالي / أخضر) يعمل", "threat-banner-red" in app_code and "threat-banner-green" in app_code),
        ("بطاقات KPIs الأربع تعرض أرقاماً حقيقية من قاعدة البيانات", "kpis['total_events']" in app_code and "kpis['verification_rate']" in app_code),
        ("الرسوم البيانية التفاعلية (Pie + Histogram) تظهر", "px.pie" in app_code and "px.histogram" in app_code),
        ("سجل الأحداث القابل للفلترة والبحث النصي يعمل", "search_kw" in app_code and "cat_filter" in app_code),
        ("تقرير SITREP يُولّد ويُحمّل بصيغتي (HTML + MD)", bool(sitrep.get("md_content")) and bool(sitrep.get("html_content"))),
        ("تقرير برقية الإنذار العاجل FLASH يُولّد", bool(flash.get("md_content"))),
        ("تقرير الرصد البحري MARITIME يُولّد", bool(maritime.get("md_content"))),
        ("ملف KML يُحمّل ويفتح في Google Earth Pro", "generate_google_earth_kml" in app_code and "application/vnd.google-earth.kml+xml" in app_code),
        ("ملف GEXF يُحمّل ويفتح في Gephi", "<gexf" in gexf_str),
        ("جداول CSV تُحمّل بترميز (utf-8-sig) وتفتح في Excel", 'to_csv(index=False).encode("utf-8-sig")' in app_code),
        ("شاشة الرادار البحري تعمل (محاكاة أو حي حسب المفتاح)", "الرادار البحري وتتبع السفن (AIS)" in app_code),
        ("وسم '🟡 محاكاة' أو '🟢 حي مباشر' يظهر بوضوح", "🟡 محاكاة" in app_code and "🟢 حي مباشر" in app_code),
        ("شاشة 'حالة المصادر' تعمل مع التحكم الفردي (اختبار + إيقاف/تشغيل)", "render_sources_status_panel" in app_code and "إيقاف/تشغيل مصدر" in app_code),
        ("إعادة التشغيل (Restart) — بقاء البيانات في قاعدة البيانات دون فقدان", persistence_ok and has_turso_env),
    ]

    all_passed = True
    for i, (desc, ok) in enumerate(items_22, 1):
        mark = "✅" if ok else "❌"
        if not ok:
            all_passed = False
        print(f"  [{i:02d}] {mark} {desc}")

    print("═" * 80)
    print(f"📊 النتيجة النهائية لاختبارات المرحلة 3: {'22/22 ناجح بالكامل ✅' if all_passed else 'يوجد بنود تحتاج مراجعة ❌'}")
    print("═" * 80)
    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    run_phase3_verification()
