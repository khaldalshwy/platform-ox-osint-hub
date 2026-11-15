# -*- coding: utf-8 -*-
"""
اختبار التحقق الإلزامي للمرحلة 2 (test_sources.py)
يختبر:
  [1] كل مصدر RSS في القائمة (HTTP 200 + عناصر XML صالحة + عدد الأخبار المسترجعة)
  [2] تطبيق فلتر الصلة اليمنية على 10 أخبار من كل مصدر، والتأكد أن المرفوض يذهب إلى rejected_news فقط
      بينما الأقسام الثلاثة (بحري، أمني/عسكري، إغاثي/تجاري) تبقى بدون فلترة
  [3] اختبار AIS (الاتصال بـ WebSocket إن وُجد مفتاح، أو عمل المحاكاة مع وسم "🟡 محاكاة")
  [4] اختبار منع التكرار عبر SHA-256 (إرسال نفس الخبر مرتين من مصدرين مختلفين -> يُحفظ مرة واحدة فقط)
"""

import os
import sys
import requests
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

# إعداد المسارات
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
for sub in ["01_acquisition", "02_storage", "03_processing", "04_orchestration"]:
    p = os.path.join(ROOT_DIR, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from apis.rss_sources import RSS_SOURCES
from apis.news_api import NewsAggregator, compute_news_hash
from ais.ais_stream_client import AISStreamClient
from database import OSINTDatabase
from sentiment.sentiment_analyzer import SentimentAnalyzer
from nlp_engine.nlp_processor import NLPProcessor
from spatial_gis.spatial_analyzer import SpatialGISAnalyzer


def run_phase2_tests():
    print("═" * 78)
    print("🧪 بدء اختبارات المرحلة 2: توسيع المصادر الحقيقية المجانية + AIS + منع التكرار")
    print("═" * 78)

    agg = NewsAggregator(timeout=15)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }

    # ─────────────────────────────────────────────────────────────────────────
    # [1] اختبار كل مصدر RSS في القائمة (HTTP 200 + XML صالح + عدد الأخبار)
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[1] فحص خلاصات RSS المباشرة في RSS_SOURCES (timeout=15s):")
    print("-" * 78)
    fetched_by_source = {}
    working_sources = 0

    def _fetch_one(idx_src):
        idx, src = idx_src
        name = src["name"]
        url = src["url"]
        trust = src.get("trust_score", 70)
        last_err = None
        for attempt in range(2):
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                http_code = resp.status_code
                items = agg._parse_xml_items(resp.content, max_items=25)
                if http_code == 200 and len(items) > 0:
                    return (idx, True, name, http_code, len(items), trust, src, items, None)
            except Exception as e:
                last_err = f"{type(e).__name__}: {e}"
        return (idx, False, name, 0, 0, trust, src, [], last_err)

    with ThreadPoolExecutor(max_workers=5) as ex:
        results_1 = list(ex.map(_fetch_one, enumerate(RSS_SOURCES, 1)))

    for idx, ok, name, http_code, item_count, trust, src, items, err in results_1:
        if ok:
            working_sources += 1
            fetched_by_source[name] = (src, items)
            print(
                f"  ✅ [{idx:02d}] {name} | HTTP {http_code} | XML صالح | "
                f"الأخبار المسترجعة: {item_count} | الثقة: {trust}"
            )
        else:
            print(f"  ❌ [{idx:02d}] {name} | خطأ: {err}")

    test1_passed = working_sources == len(RSS_SOURCES)
    print("-" * 78)
    print(f"📊 نتيجة [1]: {working_sources}/{len(RSS_SOURCES)} مصدر يعمل بنجاح (HTTP 200 + XML صالح).")

    # ─────────────────────────────────────────────────────────────────────────
    # [2] تطبيق فلتر الصلة على 10 أخبار من كل مصدر والتحقق من مسار الحفظ
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[2] تطبيق التصنيف وفلتر الصلة اليمنية على 10 أخبار من كل مصدر:")
    print("-" * 78)

    test_db_path = os.path.join(ROOT_DIR, "02_storage", "test_phase2_verify.db")
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except Exception:
            pass

    test_db = OSINTDatabase(db_path=test_db_path)
    sentiment = SentimentAnalyzer()
    nlp = NLPProcessor()
    gis = SpatialGISAnalyzer()

    total_tested = 0
    total_accepted = 0
    total_rejected = 0

    for name, (src, items) in fetched_by_source.items():
        sample_10 = items[:10]
        src_accepted = 0
        src_rejected = 0

        for it in sample_10:
            total_tested += 1
            title = it["title"]
            summary = it.get("summary", "") or title
            full_text = f"{title}. {summary}"

            # التصنيف والفلترة عبر classify_event (يطبق الفلتر على سياسي/عام فقط)
            cat_info = sentiment.classify_event(title, summary, full_text)
            if not cat_info["accepted"]:
                src_rejected += 1
                total_rejected += 1
                test_db.add_rejected_news({
                    "title": title,
                    "summary": summary,
                    "source": name,
                    "rejection_reason": cat_info["rejection_reason"],
                    "matched_exclude": cat_info.get("matched_exclude"),
                })
            else:
                src_accepted += 1
                total_accepted += 1
                loc_name = cat_info.get("location_name") or "اليمن"
                lat, lon = gis.resolve_location(loc_name)
                sent = sentiment.analyze_sentiment(full_text)
                test_db.add_event({
                    "title": title,
                    "raw_content": full_text,
                    "cleaned_content": nlp.clean_arabic_text(full_text),
                    "source_id": 1,
                    "published_at": it.get("pub_date", ""),
                    "event_category": cat_info["category"],
                    "sentiment_score": sent["score"],
                    "sentiment_label": sent["label"],
                    "urgency_level": "متوسطة",
                    "fact_check_status": f"ثقة المصدر ({src.get('trust_score', 70)}%)",
                    "latitude": lat,
                    "longitude": lon,
                    "location_name": loc_name,
                    "raw_data_url": it.get("link", ""),
                    "raw_hash": compute_news_hash(title),
                })

        print(
            f"  📌 {name}: تم فحص {len(sample_10)} أخبار -> "
            f"مقبول: {src_accepted} | مرفوض (إلى rejected_news): {src_rejected}"
        )

    # التأكد أيضاً من عدم تسرب خبر غير يمني من قسم سياسي/عام، وأن المرفوض في rejected_news فقط
    non_yemen_sample = {
        "title": "أحمد السقا يشارك في مهرجان القاهرة السينمائي الدولي بفيلم جديد",
        "summary": "حفل افتتاح مهرجان القاهرة السينمائي بحضور نجوم الفن والسينما في القاهرة",
        "source": "اختبار فلترة",
    }
    cat_non_yemen = sentiment.classify_event(
        non_yemen_sample["title"], non_yemen_sample["summary"], non_yemen_sample["title"]
    )
    if not cat_non_yemen["accepted"]:
        test_db.add_rejected_news({
            "title": non_yemen_sample["title"],
            "summary": non_yemen_sample["summary"],
            "source": non_yemen_sample["source"],
            "rejection_reason": cat_non_yemen["rejection_reason"],
            "matched_exclude": cat_non_yemen.get("matched_exclude"),
        })

    # فحص سجلات قاعدة البيانات الاختبارية
    saved_events = test_db.get_events(limit=500)
    saved_rejected = test_db.get_rejected_news(limit=500)

    leaked_in_events = any("أحمد السقا" in ev["title"] for ev in saved_events)
    present_in_rejected = any("أحمد السقا" in r["title"] for r in saved_rejected)
    test2_passed = (not leaked_in_events) and present_in_rejected and (len(saved_rejected) == total_rejected + 1)

    print("-" * 78)
    print(
        f"📊 نتيجة [2]: إجمالي المفحوص: {total_tested} | المقبول في osint_events: {total_accepted} | "
        f"المرفوض في rejected_news فقط: {len(saved_rejected)} | تسرب أخبار غير يمنية: {'صفر ✅' if not leaked_in_events else 'يوجد تسرب ❌'}"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # [3] اختبار AIS (WebSocket أو بديل المحاكاة مع وسم "🟡 محاكاة")
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[3] اختبار عميل الملاحة البحرية AISStreamClient:")
    print("-" * 78)
    ais_client = AISStreamClient()
    ais_result = ais_client.fetch_vessels(duration_seconds=5)
    ais_vessels = ais_result.get("vessels", [])
    ais_mode = ais_result.get("mode")
    ais_badge = ais_result.get("badge")

    for v in ais_vessels:
        test_db.upsert_vessel(v)
    db_vessels = test_db.get_vessels(limit=50)

    has_badge_on_all = all(
        (v.get("mode_badge") in ("🟢 حي مباشر", "🟡 محاكاة")) or ("محاكاة" in str(v.get("nav_status", "")) or "حي" in str(v.get("nav_status", "")))
        for v in db_vessels
    )
    if ais_client.has_api_key():
        print(f"  🔑 مفتاح AISSTREAM_API_KEY متوفر | الوضع: {ais_mode} | الوسم: {ais_badge}")
    else:
        print(f"  ℹ️ لا يوجد مفتاح AISSTREAM_API_KEY حالياً -> تفعيل وضع المحاكاة التلقائي بنجاح | الوسم: {ais_badge}")
    print(f"  🚢 عدد السفن المسجلة في جدول vessels: {len(db_vessels)} سفينة | جميعها تحمل وسم الحالة: {'نعم ✅' if has_badge_on_all else 'لا ❌'}")
    if db_vessels:
        sample_v = db_vessels[0]
        v_lat = sample_v.get("lat") or sample_v.get("current_latitude")
        v_lon = sample_v.get("lon") or sample_v.get("current_longitude")
        v_badge = sample_v.get("mode_badge") or ("🟢 حي مباشر" if sample_v.get("is_live") else "🟡 محاكاة")
        print(
            f"  ⚓ عينة سفينة: {sample_v['vessel_name']} (MMSI: {sample_v['mmsi']}) | "
            f"الموقع: ({v_lat}, {v_lon}) | الحالة: {v_badge}"
        )

    test3_passed = len(db_vessels) >= 13 and has_badge_on_all and (
        (not ais_client.has_api_key() and ais_badge == "🟡 محاكاة") or (ais_client.has_api_key())
    )

    # ─────────────────────────────────────────────────────────────────────────
    # [4] اختبار منع التكرار (SHA-256) عبر مصدرين مختلفين
    # ─────────────────────────────────────────────────────────────────────────
    print("\n[4] اختبار منع التكرار (SHA-256 Deduplication) لنفس الخبر من مصدرين مختلفين:")
    print("-" * 78)
    dup_title = "اجتماع طارئ في محافظة عدن لمناقشة تحسين الخدمات بالموانئ اليمنية"
    dup_summary = "عقدت السلطات المحلية في عدن اجتماعاً موسعاً لمتابعة حركة الملاحة في ميناء عدن."

    first_save = agg.save_news(
        {
            "title": dup_title,
            "summary": dup_summary,
            "source_name": "عدن الغد",
            "category_hint": "سياسي/عام",
            "trust_score": 90,
            "link": "https://example.com/source1/news-1",
        },
        target_db=test_db,
    )
    second_save = agg.save_news(
        {
            "title": dup_title,
            "summary": dup_summary,
            "source_name": "يمن شباب نت",
            "category_hint": "سياسي/عام",
            "trust_score": 90,
            "link": "https://example.com/source2/news-1",
        },
        target_db=test_db,
    )

    all_after_dup = test_db.get_events(limit=500)
    occurrences = sum(1 for ev in all_after_dup if ev["title"] == dup_title)

    print(f"  1️⃣ الإرسال الأول (المصدر: عدن الغد)     -> الحالة: {first_save['status']} (ID: {first_save['id']})")
    print(f"  2️⃣ الإرسال الثاني (المصدر: يمن شباب نت) -> الحالة: {second_save['status']} (السبب: {second_save['reason']})")
    print(f"  🔍 عدد مرات ظهور الخبر في قاعدة البيانات: {occurrences} مرة فقط (SHA-256: {compute_news_hash(dup_title)[:16]}...)")

    test4_passed = (
        first_save["status"] == "accepted"
        and second_save["status"] == "duplicate"
        and occurrences == 1
    )

    # تنظيف ملف قاعدة البيانات الاختبارية المؤقتة
    try:
        os.remove(test_db_path)
    except Exception:
        pass

    print("\n" + "═" * 78)
    print("📋 ملخص نتائج اختبارات المرحلة 2:")
    print(f"  [1] فحص خلاصات RSS (HTTP 200 + XML):      {'✅ ناجح' if test1_passed else '❌ فاشل'} ({working_sources}/{len(RSS_SOURCES)})")
    print(f"  [2] فلتر الصلة وعزل المرفوض بـ rejected_news: {'✅ ناجح' if test2_passed else '❌ فاشل'}")
    print(f"  [3] عميل AIS ووسم (🟡 محاكاة / 🟢 حي):     {'✅ ناجح' if test3_passed else '❌ فاشل'}")
    print(f"  [4] منع التكرار عبر SHA-256 بين المصادر:    {'✅ ناجح' if test4_passed else '❌ فاشل'}")
    print("═" * 78)

    if not (test1_passed and test2_passed and test3_passed and test4_passed):
        sys.exit(1)


if __name__ == "__main__":
    run_phase2_tests()
