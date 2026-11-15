import os
import sys
import json
import time
import random
import datetime
from typing import List, Dict, Any, Optional

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _sub in ["01_acquisition", "02_storage"]:
    _p = os.path.join(_BASE_DIR, _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from database import db


def _load_env_key(key_name: str = "AISSTREAM_API_KEY") -> Optional[str]:
    """قراءة مفتاح AISSTREAM_API_KEY من متغيرات البيئة أو من ملف .env"""
    val = os.environ.get(key_name, "").strip()
    if val and val != "your_free_key_here":
        return val

    for env_path in [
        os.path.join(_BASE_DIR, ".env"),
        os.path.join(_BASE_DIR, "05_devops", ".env"),
    ]:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        if k.strip() == key_name:
                            v = v.strip().strip('"').strip("'")
                            if v and v != "your_free_key_here":
                                return v
            except Exception:
                pass
    return None


class AISStreamClient:
    """
    عميل الرصد الملاحي المباشر عبر AISStream.io (WebSocket) لمنطقة البحر الأحمر وباب المندب
    - خط العرض (Latitude): 11.0 إلى 16.0
    - خط الطول (Longitude): 41.0 إلى 45.0
    في حال عدم وجود مفتاح API مجاني، ينتقل تلقائياً إلى الـ 13 سفينة محاكاة مع إظهار شارة '🟡 محاكاة'.
    """
    WS_URL = "wss://stream.aisstream.io/v0/stream"
    BOUNDING_BOX = [[[11.0, 41.0], [16.0, 45.0]]]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or _load_env_key("AISSTREAM_API_KEY")

    def has_valid_key(self) -> bool:
        return bool(self.api_key and self.api_key.strip() and self.api_key != "your_free_key_here")

    def has_api_key(self) -> bool:
        return self.has_valid_key()

    def fetch_live_websocket_vessels(self, listen_seconds: float = 6.0, max_vessels: int = 40) -> List[Dict[str, Any]]:
        """
        الاتصال بخدمة AISStream.io عبر WebSocket بنمط النبضة المحدودة (On-Demand Bounded Burst):
        - لا يعمل كاتصال متزامن دائم في الخلفية لعدم استهلاك المعالج أو الشبكة.
        - يفتح الاتصال لمدة محددة فقط (listen_seconds=6 ثوانٍ كحد أقصى أو حتى جمع max_vessels سفينة)،
          ثم يغلق المقبس (Socket) فوراً وبشكل مضمون عبر finally: ws.close().
        """
        if not self.has_valid_key():
            return []

        vessels_by_mmsi: Dict[int, Dict[str, Any]] = {}
        sub_msg = json.dumps({
            "APIKey": self.api_key,
            "BoundingBoxes": self.BOUNDING_BOX,
            "FilterMessageTypes": ["PositionReport", "StandardClassBPositionReport", "ShipStaticData"]
        })

        ws = None
        try:
            import websocket  # websocket-client
            ws = websocket.create_connection(self.WS_URL, timeout=8)
            ws.settimeout(listen_seconds)
            ws.send(sub_msg)
            start_t = time.time()
            while (time.time() - start_t) < listen_seconds and len(vessels_by_mmsi) < max_vessels:
                raw = ws.recv()
                if not raw:
                    break
                msg = json.loads(raw)
                self._parse_aisstream_message(msg, vessels_by_mmsi)
        except ImportError:
            try:
                import asyncio
                import websockets

                async def _listen():
                    async with websockets.connect(self.WS_URL, open_timeout=8, close_timeout=2) as async_ws:
                        await async_ws.send(sub_msg)
                        start_t = time.time()
                        while (time.time() - start_t) < listen_seconds and len(vessels_by_mmsi) < max_vessels:
                            raw = await asyncio.wait_for(async_ws.recv(), timeout=listen_seconds)
                            msg = json.loads(raw)
                            self._parse_aisstream_message(msg, vessels_by_mmsi)

                asyncio.run(_listen())
            except Exception as e:
                print(f"[!] تنبيه اتصال AISStream WebSocket: {e}")
        except Exception as e:
            print(f"[!] خطأ أثناء الاتصال بـ AISStream.io: {e}")
        finally:
            if ws is not None:
                try:
                    ws.close()
                except Exception:
                    pass

        results = list(vessels_by_mmsi.values())
        for v in results:
            db.upsert_vessel(v)
        return results

    def _parse_aisstream_message(self, msg: Dict[str, Any], store: Dict[int, Dict[str, Any]]):
        meta = msg.get("MetaData", {})
        mmsi = meta.get("MMSI")
        if not mmsi:
            return
        mmsi = int(mmsi)
        name = (meta.get("ShipName") or f"VESSEL-{mmsi}").strip()
        lat = float(meta.get("latitude", 13.0))
        lon = float(meta.get("longitude", 43.2))
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        pos = msg.get("Message", {}).get("PositionReport", {})
        sog = float(pos.get("Sog", 12.0))
        cog = float(pos.get("Cog", 330.0))

        store[mmsi] = {
            "mmsi": mmsi,
            "name": name,
            "vessel_name": name,
            "imo_number": 0,
            "ship_type": "سفينة تجارية (AIS Live)",
            "vessel_type": "سفينة تجارية (AIS Live)",
            "flag": "دولي (AIS)",
            "flag_country": "دولي (AIS)",
            "destination": "البحر الأحمر / باب المندب",
            "eta": now_str,
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "current_latitude": round(lat, 4),
            "current_longitude": round(lon, 4),
            "sog": round(sog, 1),
            "cog": round(cog, 1),
            "speed_knots": round(sog, 1),
            "course_degrees": round(cog, 1),
            "nav_status": "🟢 حي مباشر (AISStream)",
            "last_seen": now_str,
            "last_signal_at": now_str,
            "is_live": True,
            "mode_badge": "🟢 حي مباشر"
        }

    def get_simulated_vessels(self) -> List[Dict[str, Any]]:
        """إرجاع الـ 13 سفينة محاكاة الحالية مع وسم كل سفينة بشارة '🟡 محاكاة' بوضوح"""
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        base_13_vessels = [
            {
                "mmsi": 636019842,
                "vessel_name": "AL-DIRIYAH VOYAGER",
                "imo_number": 9812450,
                "vessel_type": "ناقلة نفط خام (Crude Tanker)",
                "flag_country": "ليبيريا",
                "destination": "Suez Port",
                "current_latitude": 12.825,
                "current_longitude": 43.210,
                "speed_knots": 14.2,
                "course_degrees": 332.0,
                "nav_status": "قيد الإبحار بالمحرك",
            },
            {
                "mmsi": 477123980,
                "vessel_name": "PACIFIC GLORY",
                "imo_number": 9745120,
                "vessel_type": "سفينة حاويات (Container Ship)",
                "flag_country": "هونغ كونغ",
                "destination": "Jeddah Port",
                "current_latitude": 13.410,
                "current_longitude": 42.890,
                "speed_knots": 18.5,
                "course_degrees": 345.0,
                "nav_status": "قيد الإبحار بالمحرك",
            },
            {
                "mmsi": 215689000,
                "vessel_name": "MEDITERRANEAN STAR",
                "imo_number": 9456781,
                "vessel_type": "بضائع عامة (General Cargo)",
                "flag_country": "مالطا",
                "destination": "Aden Port",
                "current_latitude": 12.650,
                "current_longitude": 44.820,
                "speed_knots": 11.4,
                "course_degrees": 88.0,
                "nav_status": "قيد الإبحار بالمحرك",
            },
            {
                "mmsi": 538006543,
                "vessel_name": "RED SEA MARINER",
                "imo_number": 9321456,
                "vessel_type": "ناقلة كيماويات (Chemical Tanker)",
                "flag_country": "جزر مارشال",
                "destination": "Hodeidah Anchorage",
                "current_latitude": 14.680,
                "current_longitude": 42.850,
                "speed_knots": 9.8,
                "course_degrees": 45.0,
                "nav_status": "اقتراب من الميناء",
            },
            {
                "mmsi": 351789120,
                "vessel_name": "UN WFP HUMANITARIAN 1",
                "imo_number": 9654321,
                "vessel_type": "سفينة إغاثة وحبوب (Bulk Carrier)",
                "flag_country": "بنما",
                "destination": "Salif Port",
                "current_latitude": 15.220,
                "current_longitude": 42.630,
                "speed_knots": 8.0,
                "course_degrees": 15.0,
                "nav_status": "تفريغ شحنات إغاثية",
            },
            {
                "mmsi": 371892000,
                "vessel_name": "BAB AL-MANDAB GUARD",
                "imo_number": 9582310,
                "vessel_type": "سفينة قطر وإنقاذ (Tug / Salvage)",
                "flag_country": "بنما",
                "destination": "Perim Island Zone",
                "current_latitude": 12.590,
                "current_longitude": 43.380,
                "speed_knots": 6.5,
                "course_degrees": 190.0,
                "nav_status": "مراقبة ملاحية",
            },
            {
                "mmsi": 563112400,
                "vessel_name": "STRAIT NAVIGATOR",
                "imo_number": 9801122,
                "vessel_type": "ناقلة غاز مسال (LNG Tanker)",
                "flag_country": "سنغافورة",
                "destination": "Yanbu Port",
                "current_latitude": 13.950,
                "current_longitude": 42.550,
                "speed_knots": 16.0,
                "course_degrees": 330.0,
                "nav_status": "قيد الإبحار بالمحرك",
            },
            {
                "mmsi": 249001234,
                "vessel_name": "AEGEAN SPIRIT",
                "imo_number": 9411200,
                "vessel_type": "سفينة بضائع سائبة (Bulk Carrier)",
                "flag_country": "مالطا",
                "destination": "Mukalla Port",
                "current_latitude": 14.320,
                "current_longitude": 49.050,
                "speed_knots": 12.2,
                "course_degrees": 65.0,
                "nav_status": "قيد الإبحار بالمحرك",
            },
            {
                "mmsi": 412889000,
                "vessel_name": "SILK ROAD EXPRESS",
                "imo_number": 9799110,
                "vessel_type": "سفينة حاويات عملاقة (ULCV)",
                "flag_country": "الصين",
                "destination": "Suez Canal",
                "current_latitude": 12.450,
                "current_longitude": 43.450,
                "speed_knots": 13.8,
                "course_degrees": 325.0,
                "nav_status": "قيد الإبحار بالمحرك",
            },
            {
                "mmsi": 228394000,
                "vessel_name": "FS LANGUEDOC ESCORT",
                "imo_number": 0,
                "vessel_type": "فرقاطة حماية عسكرية (Naval Frigate)",
                "flag_country": "فرنسا (أسبيدس)",
                "destination": "Red Sea Patrol Sector 4",
                "current_latitude": 13.150,
                "current_longitude": 43.050,
                "speed_knots": 22.0,
                "course_degrees": 340.0,
                "nav_status": "دورية أمنية نشطة",
            },
            {
                "mmsi": 403219000,
                "vessel_name": "YEMEN COASTAL PATROL 03",
                "imo_number": 0,
                "vessel_type": "زورق خفر سواحل (Coast Guard)",
                "flag_country": "اليمن",
                "destination": "Hodeidah Sector",
                "current_latitude": 14.850,
                "current_longitude": 42.910,
                "speed_knots": 24.5,
                "course_degrees": 180.0,
                "nav_status": "دورية تفتيش ومراقبة",
            },
            {
                "mmsi": 620891000,
                "vessel_name": "OCEAN BLUE 1",
                "imo_number": 9187654,
                "vessel_type": "سفينة بضائع وسيارات (Ro-Ro Cargo)",
                "flag_country": "جزر القمر",
                "destination": "Djibouti Port",
                "current_latitude": 11.950,
                "current_longitude": 43.150,
                "speed_knots": 15.0,
                "course_degrees": 210.0,
                "nav_status": "قيد الإبحار بالمحرك",
            },
            {
                "mmsi": 518100234,
                "vessel_name": "SOCOTRA EXPRESS",
                "imo_number": 9511223,
                "vessel_type": "سفينة شحن ومسافرين (Passenger/Cargo)",
                "flag_country": "اليمن",
                "destination": "Socotra Port (Hawlaf)",
                "current_latitude": 13.200,
                "current_longitude": 51.500,
                "speed_knots": 12.0,
                "course_degrees": 105.0,
                "nav_status": "قيد الإبحار بالمحرك",
            },
        ]

        simulated_fleet = []
        for v in base_13_vessels:
            lat = round(v["current_latitude"] + random.uniform(-0.012, 0.012), 4)
            lon = round(v["current_longitude"] + random.uniform(-0.012, 0.012), 4)
            v_item = {
                "mmsi": v["mmsi"],
                "name": v["vessel_name"],
                "vessel_name": v["vessel_name"],
                "imo_number": v["imo_number"],
                "ship_type": v["vessel_type"],
                "vessel_type": v["vessel_type"],
                "flag": v["flag_country"],
                "flag_country": v["flag_country"],
                "destination": v["destination"],
                "eta": now_str,
                "lat": lat,
                "lon": lon,
                "current_latitude": lat,
                "current_longitude": lon,
                "sog": v["speed_knots"],
                "cog": v["course_degrees"],
                "speed_knots": v["speed_knots"],
                "course_degrees": v["course_degrees"],
                "nav_status": f"🟡 محاكاة — {v['nav_status']}",
                "last_seen": now_str,
                "last_signal_at": now_str,
                "is_live": False,
                "mode_badge": "🟡 محاكاة"
            }
            try:
                db.upsert_vessel(v_item)
            except Exception:
                pass
            simulated_fleet.append(v_item)
        return simulated_fleet

    def fetch_vessels(self, duration_seconds: float = 6.0) -> Dict[str, Any]:
        """
        جلب بيانات السفن:
        - إذا وُجد مفتاح AISSTREAM_API_KEY صالح -> يتصل بالـ WebSocket ويعرض شارة '🟢 حي مباشر'
        - إذا لم يوجد المفتاح أو تعذر الاتصال -> يستخدم الـ 13 سفينة محاكاة مع شارة '🟡 محاكاة'
        """
        if self.has_valid_key():
            live_vessels = self.fetch_live_websocket_vessels(listen_seconds=duration_seconds)
            if live_vessels:
                return {
                    "is_live": True,
                    "mode": "live",
                    "badge": "🟢 حي مباشر",
                    "mode_badge": "🟢 حي مباشر",
                    "source": "AISStream.io WebSocket",
                    "vessels": live_vessels
                }

        sim_vessels = self.get_simulated_vessels()
        return {
            "is_live": False,
            "mode": "simulation",
            "badge": "🟡 محاكاة",
            "mode_badge": "🟡 محاكاة",
            "source": "Simulation Fallback (No API Key)",
            "vessels": sim_vessels
        }


def fetch_ais_vessels() -> Dict[str, Any]:
    client = AISStreamClient()
    return client.fetch_vessels()


if __name__ == "__main__":
    res = fetch_ais_vessels()
    print(f"[*] حالة رادار السفن: {res['mode_badge']} | المصدر: {res['source']} | عدد السفن: {len(res['vessels'])}")

