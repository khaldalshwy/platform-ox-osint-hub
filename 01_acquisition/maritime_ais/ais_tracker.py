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
