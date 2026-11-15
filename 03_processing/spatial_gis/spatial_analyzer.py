import math
from typing import List, Dict, Any, Tuple


class SpatialGISAnalyzer:
    """
    محرك التحليل الجغرافي والمكاني (GIS) لمنصة OSINT Platform OX
    يحسب المسافات البحرية (بالميل البحري والكيلومتر)، إسقاط الإحداثيات،
    وتحديد دوائر الخطر والنقاط الساخنة (Hotspots) للمواقع اليمنية الحقيقية.
    """
    def __init__(self):
        # قاموس الإحداثيات المرجعية للمدن والمحافظات والموانئ اليمنية والممرات المائية
        self.geo_gazetteer = {
            "ميناء الحديدة": (14.7978, 42.9496),
            "ميناء عدن": (12.7855, 44.9782),
            "ميناء الصليف": (15.3102, 42.6711),
            "ميناء رأس عيسى": (15.1950, 42.6580),
            "ميناء المخا": (13.3211, 43.2478),
            "ميناء المكلا": (14.5425, 49.1242),
            "ميناء نشطون": (15.8200, 52.2300),
            "ميناء بير علي": (14.0150, 48.3350),
            "مضيق باب المندب": (12.5860, 43.3420),
            "باب المندب": (12.5860, 43.3420),
            "صنعاء": (15.3694, 44.1910),
            "عدن": (12.7855, 44.9782),
            "الحديدة": (14.7978, 42.9496),
            "تعز": (13.5795, 44.0209),
            "المكلا": (14.5425, 49.1242),
            "حضرموت": (15.4000, 48.8000),
            "سيئون": (15.9430, 48.7870),
            "مأرب": (15.4628, 45.3258),
            "شبوة": (14.5300, 46.8300),
            "سقطرى": (12.4634, 53.8237),
            "الصليف": (15.3102, 42.6711),
            "رأس عيسى": (15.1950, 42.6580),
            "المخا": (13.3211, 43.2478),
            "ميون": (12.6528, 43.4144),
            "حنيش": (13.7500, 42.7500),
            "الخوخة": (13.8050, 43.2500),
            "صعدة": (16.9402, 43.7639),
            "حجة": (15.6942, 43.6058),
            "إب": (13.9667, 44.1833),
            "ذمار": (14.5426, 44.4051),
            "البيضاء": (13.9852, 45.5727),
            "الجوف": (16.6000, 45.2000),
            "عمران": (15.6594, 43.9439),
            "الضالع": (13.6957, 44.7314),
            "لحج": (13.0578, 44.8831),
            "أبين": (13.1287, 45.3806),
            "المحويت": (15.4701, 43.5448),
            "ريمة": (14.6290, 43.7150),
            "بلحاف": (13.9800, 48.1800),
            "بير علي": (14.0150, 48.3350),
            "نشطون": (15.8200, 52.2300),
            "الشحر": (14.7600, 49.6100),
            "الغيضة": (16.2079, 52.1760),
            "المهرة": (16.5000, 51.8000),
            "خليج عدن": (12.2000, 46.5000),
            "البحر الأحمر": (13.8000, 43.1000),
            "اليمن": (15.3694, 44.1910),
        }

    def resolve_location(self, location_name: str) -> Tuple[float, float]:
        """استرجاع خط العرض وخط الطول لاسم الموقع اليمني الحقيقي"""
        if not location_name or location_name == "غير محدد":
            return (15.3694, 44.1910)
        loc_clean = location_name.strip()
        if loc_clean in self.geo_gazetteer:
            return self.geo_gazetteer[loc_clean]
        for key, coords in self.geo_gazetteer.items():
            if key == loc_clean or (len(key) >= 4 and key in loc_clean):
                return coords
        return (15.3694, 44.1910)

    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """حساب المسافة الجيوديسية بين نقطتين على سطح الأرض بالكيلومتر"""
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 2)

    def haversine_distance_nautical_miles(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """حساب المسافة بالميل البحري (Nautical Miles)"""
        km = self.haversine_distance_km(lat1, lon1, lat2, lon2)
        return round(km * 0.539957, 2)

    def identify_hotspots(self, events: List[Dict[str, Any]], radius_km: float = 60.0) -> List[Dict[str, Any]]:
        """تحديد مراكز التجمع والنقاط الساخنة للأحداث"""
        clusters = []
        for loc_name, (center_lat, center_lon) in self.geo_gazetteer.items():
            matching_events = []
            for ev in events:
                lat = ev.get("latitude")
                lon = ev.get("longitude")
                if lat and lon:
                    dist = self.haversine_distance_km(center_lat, center_lon, lat, lon)
                    if dist <= radius_km:
                        matching_events.append(ev)
            if matching_events:
                clusters.append({
                    "zone_name": loc_name,
                    "center": {"lat": center_lat, "lon": center_lon},
                    "events_count": len(matching_events),
                    "density": "مرتفعة" if len(matching_events) >= 5 else "متوسطة"
                })
        return clusters


if __name__ == "__main__":
    gis = SpatialGISAnalyzer()
    d_km = gis.haversine_distance_km(14.7978, 42.9496, 12.5860, 43.3420)
    d_nm = gis.haversine_distance_nautical_miles(14.7978, 42.9496, 12.5860, 43.3420)
    print(f"[*] المسافة بين ميناء الحديدة ومضيق باب المندب: {d_km} كم ({d_nm} ميل بحري).")
