import sys
import os
import time
import datetime

# ضبط ترميز المخرجات لدعم اللغة العربية في نظام ويندوز
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sub in ["01_acquisition", "02_storage", "03_processing", "04_orchestration", "06_presentation"]:
    p = os.path.join(BASE_DIR, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

from apis.news_api import NewsAggregator
from maritime_ais.ais_tracker import AISTracker
from nlp_engine.nlp_processor import NLPProcessor
from sentiment.sentiment_analyzer import SentimentAnalyzer, classify_event
from filters.yemen_relevance_filter import extract_yemen_location
from spatial_gis.spatial_analyzer import SpatialGISAnalyzer
from database import db
from db_adapter import _read_config_value


def send_alert(
    alert_type: str,
    message: str,
    severity: str = "HIGH",
    bot_token: str = "",
    chat_id: str = "",
    webhook_url: str = "",
) -> dict:
    """
    التحسين 6.2: إرسال إشعار إنذار فوري عبر Telegram Bot API و/أو Generic Webhook (Slack/Discord).
    تُقرأ المفاتيح بأمان من المعاملات أو متغيرات البيئة أو Streamlit Secrets أو .env.
    """
    import requests

    tg_token = (bot_token or _read_config_value("TELEGRAM_BOT_TOKEN")).strip()
    tg_chat = (chat_id or _read_config_value("TELEGRAM_CHAT_ID")).strip()
    wh_url = (webhook_url or _read_config_value("GENERIC_WEBHOOK_URL")).strip()

    placeholders = {"", "your_bot_token_here", "your_chat_id_here", "your_webhook_url_here"}
    results = {"telegram_sent": False, "webhook_sent": False, "errors": []}

    formatted_msg = f"🚨 [{severity}] Platform OX — {alert_type}\n{message}"

    if tg_token not in placeholders and tg_chat not in placeholders:
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                json={"chat_id": tg_chat, "text": formatted_msg},
                timeout=8,
            )
            if resp.status_code == 200:
                results["telegram_sent"] = True
            else:
                results["errors"].append(f"Telegram HTTP {resp.status_code}")
        except Exception as e:
            results["errors"].append(f"Telegram Error: {type(e).__name__}")

    if wh_url not in placeholders:
        try:
            resp = requests.post(
                wh_url,
                json={"text": formatted_msg, "alert_type": alert_type, "severity": severity},
                timeout=8,
            )
            if resp.status_code in (200, 201, 204):
                results["webhook_sent"] = True
            else:
                results["errors"].append(f"Webhook HTTP {resp.status_code}")
        except Exception as e:
            results["errors"].append(f"Webhook Error: {type(e).__name__}")

    return results


def run_full_osint_cycle(query: str = "") -> dict:
    """
    تشغيل دورة رصد وتحليل استخباراتي كاملة بأقصى طاقة وفق منهجية مركز معطى:
    1. الجمع متعدد المصادر (Multi-Source Live Acquisition + AIS)
    2. الفلترة والتحليل المتزامن (Yemen Relevance Filter for سياسي/عام + NLP NER + Sentiment + Spatial GIS)
    3. التخزين والتحديث في قاعدة البيانات المركزية
    4. استخراج مقاييس الأداء التكتيكية والتشغيلية
    """
    start_time = time.time()
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("=" * 70)
    print(f"[*] بدء دورة الرصد والتحليل الاستخباراتي الشاملة: {now_str}")
    print("=" * 70)

    # 1. جمع الأخبار والبرقيات الحية من كافة المصادر المفتوحة
    print("[1/4] مسح وتدفق المصادر المفتوحة المتعددة بالتوازي...")
    news_agg = NewsAggregator()
    news_items = news_agg.fetch_live_news(query=query)
    print(f"   -> تم التقاط وقبول {len(news_items)} خبراً وبرقية استخباراتية بنجاح.")

    # 2. معالجة النصوص والمشاعر والإسقاط المكاني
    print("[2/4] تشغيل محركات التحليل (NLP, Threat Analysis, Yemen Filter, Geocoding)...")
    nlp = NLPProcessor()
    sentiment = SentimentAnalyzer()
    gis = SpatialGISAnalyzer()

    inserted_count = 0
    high_urgency_count = 0

    for item in news_items:
        title = item.get("title", "")
        summary = item.get("summary", "")
        full_text = f"{title} {summary}".strip()

        # فحص التصنيف وفلتر الصلة اليمنية (لقسم سياسي/عام فقط)
        classification = classify_event(title, summary, full_text)
        if not classification["accepted"]:
            db.save_rejected_news(
                title=title,
                summary=summary,
                url=item.get("url", ""),
                reason=classification["rejection_reason"],
                score=classification["relevance_score"],
                rejected_at=now_str,
            )
            continue

        category = classification["category"]
        relevance_score = classification.get("relevance_score", 100)
        relevance_reason = classification.get("relevance_reason")

        # تنظيف النص
        cleaned = nlp.clean_arabic_text(full_text)

        # استخراج الكيانات وتصنيفها بحدود الكلمة الكاملة
        entities = nlp.extract_entities(full_text)

        # تحليل المشاعر ومؤشر التهديد
        sent_res = sentiment.analyze_sentiment(full_text)

        # التحديد المكاني الحقيقي (دون إسناد "البحر الأحمر" تلقائياً بدون تحقق)
        loc_name = extract_yemen_location(title, summary)
        if not loc_name:
            for ent in entities:
                if ent["type"] == "LOCATION":
                    loc_name = ent["text"]
                    break
        if not loc_name:
            loc_name = classification.get("location_name") or "اليمن"

        coords = gis.resolve_location(loc_name)

        # تحديد درجة الأهمية الاستخباراتية
        if sent_res["tension_level"] == "قصوى" or any(w in full_text for w in ["صاروخ", "استهداف", "هجوم", "غرق"]):
            urgency = "قصوى"
            high_urgency_count += 1
        elif entities or sent_res["tension_level"] == "متوسط":
            urgency = "متوسطة"
        else:
            urgency = "روتينية"

        # تحديد حالة التحقق والتثليث
        if "UKMTO" in full_text or "رسمي" in full_text or "أسبيدس" in full_text:
            fact_status = "مؤكد برقيات رسمية"
        elif len(entities) >= 2:
            fact_status = "قيد التثليث الميداني"
        else:
            fact_status = "رصد أولي مفتوح"

        event_data = {
            "title": title,
            "raw_content": full_text,
            "cleaned_content": cleaned,
            "source_id": 1,
            "published_at": item.get("published_at"),
            "event_category": category,
            "sentiment_score": sent_res["score"],
            "sentiment_label": sent_res["label"],
            "urgency_level": urgency,
            "fact_check_status": fact_status,
            "latitude": coords[0],
            "longitude": coords[1],
            "location_name": loc_name,
            "raw_data_url": item.get("url"),
            "raw_hash": item.get("hash", ""),
            "relevance_score": relevance_score,
            "relevance_reason": relevance_reason,
            "trust_score": item.get("trust_score", 70),
            "source_label": item.get("source", "رصد علني مباشر"),
        }
        new_id = db.add_event(event_data)
        if new_id > 0:
            inserted_count += 1
            if urgency == "قصوى" and sent_res.get("threat_index", 0) >= 80:
                send_alert(
                    alert_type="حدث أمني حرج (قصوى)",
                    message=f"{item.get('title', '')}\nالموقع: {loc_name} | مؤشر التهديد: {sent_res.get('threat_index', 0)}",
                    severity="CRITICAL",
                )

    print(f"   -> تم فهرسة وتحليل {inserted_count} حدثاً بنجاح في قاعدة البيانات.")

    # 3. تحديث أسطول الملاحة البحرية وإشارات AIS
    print("[3/4] مسح إشارات AIS وتحديث أسطول السفن والملاحة البحرية...")
    ais_tracker = AISTracker()
    vessels = ais_tracker.fetch_live_vessels()
    print(f"   -> تم تحديث مسارات وإحداثيات {len(vessels)} سفينة بحرية حية.")

    # 4. استخراج مقاييس الأداء الميداني
    print("[4/4] استخراج مؤشرات الأداء الحية (KPIs)...")
    kpis = db.get_kpis()
    elapsed = round(time.time() - start_time, 2)
    print(f"   -> إجمالي الأحداث المفهرسة: {kpis['total_events']} | الأحداث العاجلة: {kpis['critical_events']} | السفن النشطة: {kpis['active_vessels']}")
    print(f"   -> زمن التنفيذ الإجمالي: {elapsed} ثانية.")
    print("=" * 70)
    print("[✓] اكتملت دورة الرصد والتحليل الاستخباراتي الشاملة بنجاح تام.")
    print("=" * 70)

    return {
        "status": "success",
        "inserted_events": inserted_count,
        "high_urgency_count": high_urgency_count,
        "active_vessels": len(vessels),
        "total_events_in_db": kpis["total_events"],
        "elapsed_seconds": elapsed,
        "timestamp": now_str
    }


if __name__ == "__main__":
    run_full_osint_cycle()
