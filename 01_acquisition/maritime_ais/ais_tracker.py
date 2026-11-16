import os
import sys
import datetime
from typing import List, Dict, Any

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _sub in ["01_acquisition", "02_storage"]:
    _p = os.path.join(_BASE_DIR, _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from database import db
from ais.ais_stream_client import AISStreamClient

# ==============================================================================
# الخطوة 5.2: القائمة الموحدة للموانئ والجزر والممرات الاستراتيجية (25 موقعاً)
# ==============================================================================
STRATEGIC_PORTS: List[Dict[str, Any]] = [
    # المواقع الـ 11 الأساسية
    {"name": "مضيق باب المندب (ممر دولي استراتيجي)", "lat": 12.5860, "lon": 43.3420, "type": "مضيق وممر ملاحي", "radius_km": 35},
    {"name": "ميناء الحديدة التجاري", "lat": 14.7978, "lon": 42.9496, "type": "ميناء استراتيجي رئيسي", "radius_km": 25},
    {"name": "ميناء الصليف للحبوب والبضائع", "lat": 15.3102, "lon": 42.6711, "type": "ميناء بضائع سائبة", "radius_km": 20},
    {"name": "ميناء رأس عيسى النفطي", "lat": 15.1950, "lon": 42.6580, "type": "مرسى وخزان نفطي", "radius_km": 20},
    {"name": "ميناء عدن الدولي للحاويات", "lat": 12.7855, "lon": 44.9782, "type": "ميناء محوري", "radius_km": 25},
    {"name": "جزيرة ميون (بريم) — باب المندب", "lat": 12.6528, "lon": 43.4144, "type": "نقطة رصد ومراقبة بحرية", "radius_km": 15},
    {"name": "أرخبيل جزر حنيش", "lat": 13.7500, "lon": 42.7500, "type": "جزر وممرات بحرية", "radius_km": 28},
    {"name": "ميناء المخا", "lat": 13.3211, "lon": 43.2478, "type": "ميناء ساحلي", "radius_km": 18},
    {"name": "ميناء المكلا — حضرموت", "lat": 14.5425, "lon": 49.1242, "type": "ميناء بحر العرب", "radius_km": 25},
    {"name": "أرخبيل جزيرة سقطرى", "lat": 12.4634, "lon": 53.8237, "type": "موقع استراتيجي — المحيط الهندي", "radius_km": 45},
    {"name": "قاعدة وميناء جيبوتي", "lat": 11.5880, "lon": 43.1450, "type": "مركز لوجستي إقليمي", "radius_km": 22},
    # المواقع البحرية الإضافية (الخطوة 5.2)
    {"name": "ميناء الضبة النفطي — حضرموت", "lat": 14.7000, "lon": 49.4500, "type": "ميناء تصدير نفطي", "radius_km": 22},
    {"name": "ميناء النشيمة النفطي — شبوة", "lat": 13.9917, "lon": 48.3667, "type": "ميناء تصدير نفطي", "radius_km": 20},
    {"name": "ميناء قنا — شبوة", "lat": 14.0150, "lon": 48.3350, "type": "ميناء ساحلي", "radius_km": 18},
    {"name": "ميناء الخوخة — الحديدة", "lat": 13.8050, "lon": 43.2500, "type": "ميناء صيد ومراقبة", "radius_km": 15},
    {"name": "ميناء بلحاف للغاز المسال — شبوة", "lat": 13.9800, "lon": 48.1800, "type": "منشأة غاز وميناء", "radius_km": 22},
    {"name": "جزيرة كمران — البحر الأحمر", "lat": 15.3500, "lon": 42.5833, "type": "جزيرة استراتيجية", "radius_km": 18},
    {"name": "جزيرة زقر — البحر الأحمر", "lat": 14.0167, "lon": 42.7333, "type": "جزيرة وممر ملاحي", "radius_km": 20},
    {"name": "أرخبيل جزيرة الزبير", "lat": 15.0500, "lon": 42.1667, "type": "جزر بركانية وممر ملاحي", "radius_km": 20},
    {"name": "ميناء جازان — السعودية", "lat": 16.8894, "lon": 42.5489, "type": "ميناء إقليمي (البحر الأحمر)", "radius_km": 25},
    {"name": "ميناء ينبع التجاري والنفطي — السعودية", "lat": 24.0895, "lon": 38.0618, "type": "ميناء إقليمي (البحر الأحمر)", "radius_km": 30},
    {"name": "ميناء جدة الإسلامي — السعودية", "lat": 21.4858, "lon": 39.1725, "type": "ميناء محوري (البحر الأحمر)", "radius_km": 35},
    {"name": "ميناء بورتسودان — السودان", "lat": 19.6158, "lon": 37.2164, "type": "ميناء إقليمي (البحر الأحمر)", "radius_km": 28},
    {"name": "ميناء بربرة — صوماليلاند", "lat": 10.4396, "lon": 45.0143, "type": "ميناء إقليمي (خليج عدن)", "radius_km": 25},
    {"name": "ميناء عصب — إريتريا", "lat": 13.0092, "lon": 42.7394, "type": "ميناء إقليمي (باب المندب)", "radius_km": 22},
]


class AISTracker:
    """
    محرك تتبع الملاحة البحرية وإشارات AIS لمنصة OSINT Platform OX (المرحلة 2)
    يتكامل مع AISStream.io (WebSocket مجاني) لالتقاط السفن الحية في البحر الأحمر وباب المندب،
    وعند عدم وجود مفتاح API يستخدم الـ 13 سفينة محاكاة مع إظهار شارة '🟡 محاكاة' بوضوح.
    """
    def __init__(self):
        self.monitored_zones = {
            "باب المندب": {"lat": 12.586, "lon": 43.342, "radius_km": 60},
            "ميناء الحديدة": {"lat": 14.797, "lon": 42.949, "radius_km": 40},
            "ميناء الصليف": {"lat": 15.310, "lon": 42.671, "radius_km": 30},
            "ميناء عدن": {"lat": 12.785, "lon": 44.978, "radius_km": 40},
            "مضيق هرمز": {"lat": 26.566, "lon": 56.252, "radius_km": 80},
            "قناة السويس": {"lat": 29.932, "lon": 32.559, "radius_km": 50},
            "أرخبيل حنيش": {"lat": 13.750, "lon": 42.750, "radius_km": 35}
        }
        self.stream_client = AISStreamClient()

    def decode_nmea_sentence(self, sentence: str) -> Dict[str, Any]:
        """فك تشفير جمل AIVDM/AIVDO المفتوحة"""
        parts = sentence.split(",")
        return {
            "raw_sentence": sentence,
            "message_type": parts[0] if parts else "Unknown",
            "timestamp": datetime.datetime.now().isoformat()
        }

    def fetch_live_vessels(self) -> List[Dict[str, Any]]:
        """
        جلب وتحديث مواقع أسطول السفن:
        - إذا وُجد مفتاح AISSTREAM_API_KEY -> بيانات حقيقية حية (🟢 حي مباشر)
        - إذا لم يوجد المفتاح -> 13 سفينة محاكاة مع شارة واضحة (🟡 محاكاة)
        """
        res = self.stream_client.fetch_vessels()
        vessels = res["vessels"]
        is_live = res["is_live"]
        badge = "🟢 مباشر" if is_live else "🟡 محاكاة"
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            db.upsert_source_status(
                name="AISStream (رادار السفن)",
                url="wss://stream.aisstream.io/v0/stream",
                source_type="AIS حي" if is_live else "AIS محاكاة",
                trust_score=95 if is_live else 75,
                enabled=True,
                last_status=badge,
                last_fetched_at=now_str,
                items_count=len(vessels)
            )
        except Exception:
            pass

        return vessels


if __name__ == "__main__":
    tracker = AISTracker()
    fleet = tracker.fetch_live_vessels()
    print(f"[*] تم تحديث وتتبع أسطول السفن بنجاح: {len(fleet)} سفينة نشطة.")
    for v in fleet[:3]:
        print(f"  - [{v.get('mode_badge', '🟡 محاكاة')}] {v['vessel_name']} | نوع: {v['vessel_type']} | موقع: {v['current_latitude']:.2f}, {v['current_longitude']:.2f}")
