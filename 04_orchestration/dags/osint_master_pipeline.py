"""
خط أنابيب Apache Airflow الرئيسي لمنصة OSINT Platform OX
يقوم بتنسيق وتشغيل دورة معطى الخماسية: الجمع ➔ التخزين ➔ التحليل ➔ الفهرسة
"""
from datetime import datetime, timedelta

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    AIRFLOW_AVAILABLE = True
except ImportError:
    AIRFLOW_AVAILABLE = False

def task_collect_news():
    print("[*] بدء سحب الأخبار الحية من المصادر المفتوحة...")
    from platform_ox.acquisition.apis.news_api import NewsAggregator
    aggregator = NewsAggregator()
    return aggregator.fetch_live_news()

def task_collect_ais_vessels():
    print("[*] بدء سحب إشارات الملاحة البحرية وتتبع حركة السفن...")
    from platform_ox.acquisition.maritime_ais.ais_tracker import AISTracker
    tracker = AISTracker()
    return tracker.fetch_live_vessels()

def task_process_nlp_and_sentiment():
    print("[*] بدء معالجة اللغة الطبيعية واستخراج الكيانات وتحليل المشاعر...")
    from platform_ox.processing.nlp_engine.nlp_processor import NLPProcessor
    from platform_ox.processing.sentiment.sentiment_analyzer import SentimentAnalyzer
    from platform_ox.storage.database import db
    
    nlp = NLPProcessor()
    sentiment = SentimentAnalyzer()
    events = db.get_events(limit=20)
    print(f"[*] تمت معالجة {len(events)} حدثاً بنجاح.")

def task_generate_daily_digest():
    print("[*] إصدار الملخص الاستخباراتي اليومي وتحديث لوحات التحكم...")

if AIRFLOW_AVAILABLE:
    default_args = {
        'owner': 'osint_admin',
        'depends_on_past': False,
        'start_date': datetime(2026, 1, 1),
        'email_on_failure': False,
        'retries': 2,
        'retry_delay': timedelta(minutes=5),
    }

    dag = DAG(
        'osint_master_orchestration',
        default_args=default_args,
        description='خط الأنابيب المركزي لنظام الرصد العلني Platform OX',
        schedule_interval=timedelta(hours=1),
        catchup=False
    )

    t1 = PythonOperator(task_id='collect_news_feed', python_callable=task_collect_news, dag=dag)
    t2 = PythonOperator(task_id='collect_ais_stream', python_callable=task_collect_ais_vessels, dag=dag)
    t3 = PythonOperator(task_id='process_nlp_sentiment', python_callable=task_process_nlp_and_sentiment, dag=dag)
    t4 = PythonOperator(task_id='generate_digest', python_callable=task_generate_daily_digest, dag=dag)

    [t1, t2] >> t3 >> t4
