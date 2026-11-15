import os
import sys
import sqlite3
import datetime
from typing import List, Dict, Any, Optional

_STORAGE_DIR = os.path.dirname(os.path.abspath(__file__))
if _STORAGE_DIR not in sys.path:
    sys.path.insert(0, _STORAGE_DIR)

from db_adapter import DatabaseAdapter

DB_FILE = os.path.join(_STORAGE_DIR, "local_osint.db")


class OSINTDatabase:
    """
    محرك قواعد البيانات المركزي لمنصة OSINT Platform OX (المرحلة 3)
    يدعم قاعدة البيانات السحابية المجانية Turso (libSQL / SQLite Cloud) عبر db_adapter،
    ويتراجع تلقائياً إلى SQLite المحلي (local_osint.db) في حال عدم ضبط متغيرات Turso.
    """
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_FILE
        # إذا تم تمرير مسار مخصص (مثل ملفات الاختبار المؤقتة)، نستخدم SQLite المخصص مباشرة
        self._force_local = db_path is not None and os.path.abspath(db_path) != os.path.abspath(DB_FILE)
        self.adapter = DatabaseAdapter(sqlite_path=self.db_path, force_sqlite=self._force_local)
        self._init_sqlite()
        if not self._force_local:
            self._seed_if_empty()

    def is_turso_active(self) -> bool:
        return self.adapter.is_turso_enabled()

    def get_backend_name(self) -> str:
        return self.adapter.get_backend_name()

    def _get_connection(self):
        return self.adapter.get_connection()

    def _init_sqlite(self):
        """تهيئة الجداول محلياً عند بدء التشغيل مع جداول المرحلة 1 والمرحلة 2"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                source_type TEXT NOT NULL,
                url_or_channel TEXT,
                credibility_score REAL DEFAULT 0.8,
                country TEXT,
                language TEXT DEFAULT 'ar',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS osint_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                raw_content TEXT,
                cleaned_content TEXT,
                source_id INTEGER,
                published_at TIMESTAMP,
                captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_category TEXT,
                sentiment_score REAL,
                sentiment_label TEXT,
                urgency_level TEXT DEFAULT 'روتينية',
                fact_check_status TEXT DEFAULT 'قيد التحقق',
                latitude REAL,
                longitude REAL,
                location_name TEXT,
                raw_data_url TEXT,
                raw_hash TEXT,
                relevance_score INTEGER DEFAULT 100,
                relevance_reason TEXT,
                trust_score INTEGER DEFAULT 70,
                source_label TEXT,
                FOREIGN KEY (source_id) REFERENCES sources (id)
            );
            """)

            # ترقية قواعد البيانات الحالية لإضافة الأعمدة الجديدة دون فقدان أي بيانات
            cursor.execute("PRAGMA table_info(osint_events);")
            existing_cols = {row["name"] for row in cursor.fetchall()}
            if "relevance_score" not in existing_cols:
                cursor.execute("ALTER TABLE osint_events ADD COLUMN relevance_score INTEGER DEFAULT 100;")
            if "relevance_reason" not in existing_cols:
                cursor.execute("ALTER TABLE osint_events ADD COLUMN relevance_reason TEXT;")
            if "trust_score" not in existing_cols:
                cursor.execute("ALTER TABLE osint_events ADD COLUMN trust_score INTEGER DEFAULT 70;")
            if "source_label" not in existing_cols:
                cursor.execute("ALTER TABLE osint_events ADD COLUMN source_label TEXT;")

            # جدول الأخبار المرفوضة بواسطة فلتر الصلة اليمنية
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS rejected_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                summary TEXT,
                url TEXT,
                reason TEXT,
                score INTEGER,
                rejected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # جدول vessels القياسي للمرحلة 2 (مع عمود is_live)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS vessels (
                mmsi INTEGER PRIMARY KEY,
                name TEXT,
                ship_type TEXT,
                flag TEXT,
                lat REAL,
                lon REAL,
                sog REAL,
                cog REAL,
                destination TEXT,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_live INTEGER DEFAULT 0
            );
            """)

            # جدول ais_vessels المتوافق مع الواجهات الحالية
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ais_vessels (
                mmsi INTEGER PRIMARY KEY,
                vessel_name TEXT,
                imo_number INTEGER,
                vessel_type TEXT,
                flag_country TEXT,
                destination TEXT,
                eta TEXT,
                current_latitude REAL,
                current_longitude REAL,
                speed_knots REAL,
                course_degrees REAL,
                nav_status TEXT,
                last_signal_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_live INTEGER DEFAULT 0
            );
            """)

            cursor.execute("PRAGMA table_info(ais_vessels);")
            ais_cols = {row["name"] for row in cursor.fetchall()}
            if "is_live" not in ais_cols:
                cursor.execute("ALTER TABLE ais_vessels ADD COLUMN is_live INTEGER DEFAULT 0;")

            # جدول حالة المصادر والتحكم بتشغيلها/إيقافها (المرحلة 2.5)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_registry_status (
                name TEXT PRIMARY KEY,
                url TEXT,
                source_type TEXT,
                trust_score INTEGER DEFAULT 70,
                enabled INTEGER DEFAULT 1,
                last_status TEXT DEFAULT '🟢 نشط',
                last_fetched_at TEXT DEFAULT 'لم يُسحب بعد',
                items_count INTEGER DEFAULT 0
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS extracted_entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_name TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                confidence_score REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                entity_id INTEGER,
                relation_type TEXT,
                weight REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES osint_events (id),
                FOREIGN KEY (entity_id) REFERENCES extracted_entities (id)
            );
            """)
            conn.commit()

    def _seed_if_empty(self):
        """بذر تلقائي للبيانات الموثقة عند التشغيل لأول مرة في بيئة سحابية فارغة (مثل Streamlit Community Cloud)"""
        seed_path = os.path.join(os.path.dirname(_STORAGE_DIR), "cloud_seed.json")
        if not os.path.exists(seed_path):
            return
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as c FROM osint_events")
                row = cursor.fetchone()
                if row and int(row["c"]) > 0:
                    return
            import json
            with open(seed_path, "r", encoding="utf-8") as f:
                seed = json.load(f)
            for ev in seed.get("events", []):
                self.add_event(ev)
            for v in seed.get("vessels", []):
                self.upsert_vessel(v)
            for rj in seed.get("rejected", []):
                self.add_rejected_news(rj)
        except Exception:
            pass

    def add_source(self, name: str, source_type: str, url: str, credibility: float = 0.8, country: str = "اليمن") -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sources (name, source_type, url_or_channel, credibility_score, country)
                VALUES (?, ?, ?, ?, ?)
            """, (name, source_type, url, credibility, country))
            conn.commit()
            return cursor.lastrowid

    def save_rejected_news(
        self,
        title: str,
        summary: str = "",
        url: str = "",
        reason: Optional[str] = "no_yemen_link",
        score: int = 0,
        rejected_at: Optional[str] = None
    ) -> int:
        """حفظ الأخبار المستبعدة في جدول rejected_news فقط مع سبب الرفض ودرجة الصلة"""
        ts = rejected_at or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rejected_news (title, summary, url, reason, score, rejected_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, summary, url, reason, score, ts))
            conn.commit()
            return cursor.lastrowid

    def add_rejected_news(self, data: Dict[str, Any]) -> int:
        """دالة مساعدة لحفظ قاموس خبر مرفوض في جدول rejected_news"""
        reason = data.get("rejection_reason") or data.get("reason") or "no_yemen_entity"
        if data.get("matched_exclude"):
            reason = f"{reason} ({data['matched_exclude']})"
        return self.save_rejected_news(
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            url=data.get("url") or data.get("source", ""),
            reason=reason,
            score=int(data.get("relevance_score", data.get("score", 0))),
            rejected_at=data.get("rejected_at"),
        )

    def get_rejected_news(self, limit: int = 100) -> List[Dict[str, Any]]:
        """استرجاع سجل الأخبار المرفوضة لأغراض التدقيق والمراجعة"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM rejected_news ORDER BY id DESC LIMIT ?", (limit,))
            rows = []
            for row in cursor.fetchall():
                d = dict(row)
                d.setdefault("source", d.get("url", "RSS"))
                d.setdefault("rejection_reason", d.get("reason", ""))
                d.setdefault("matched_exclude", d.get("reason", ""))
                rows.append(d)
            return rows

    def event_hash_exists(self, raw_hash: str) -> bool:
        """التحقق من وجود بصمة SHA-256 للخبر لمنع التكرار عبر المصادر المختلفة"""
        if not raw_hash:
            return False
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM osint_events WHERE raw_hash = ? LIMIT 1", (raw_hash,))
            return cursor.fetchone() is not None

    def add_event(self, event_data: Dict[str, Any]) -> int:
        raw_hash = event_data.get("raw_hash", "")
        if raw_hash and self.event_hash_exists(raw_hash):
            return 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO osint_events (
                    title, raw_content, cleaned_content, source_id, published_at,
                    event_category, sentiment_score, sentiment_label, urgency_level,
                    fact_check_status, latitude, longitude, location_name, raw_data_url, raw_hash,
                    relevance_score, relevance_reason, trust_score, source_label
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_data.get("title", ""),
                event_data.get("raw_content", ""),
                event_data.get("cleaned_content", ""),
                event_data.get("source_id"),
                event_data.get("published_at", datetime.datetime.now().isoformat()),
                event_data.get("event_category", "عام"),
                event_data.get("sentiment_score", 0.0),
                event_data.get("sentiment_label", "محايد"),
                event_data.get("urgency_level", "روتينية"),
                event_data.get("fact_check_status", "قيد التحقق"),
                event_data.get("latitude"),
                event_data.get("longitude"),
                event_data.get("location_name", ""),
                event_data.get("raw_data_url", ""),
                raw_hash,
                event_data.get("relevance_score", 100),
                event_data.get("relevance_reason"),
                event_data.get("trust_score", 70),
                event_data.get("source_label", "رصد علني مباشر"),
            ))
            conn.commit()
            return cursor.lastrowid

    def get_events(self, limit: int = 100, category: Optional[str] = None, urgency: Optional[str] = None, search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT e.*, COALESCE(e.source_label, s.name, 'رصد علني مباشر') as source_name 
                FROM osint_events e
                LEFT JOIN sources s ON e.source_id = s.id
                WHERE 1=1
            """
            params = []
            if category and category != "الكل":
                query += " AND e.event_category = ?"
                params.append(category)
            if urgency and urgency != "الكل":
                query += " AND e.urgency_level = ?"
                params.append(urgency)
            if search_query:
                query += " AND (e.title LIKE ? OR e.raw_content LIKE ? OR e.location_name LIKE ?)"
                kw = f"%{search_query}%"
                params.extend([kw, kw, kw])

            query += " ORDER BY e.id DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]

    def upsert_vessel(self, vessel_data: Dict[str, Any]):
        mmsi = int(vessel_data["mmsi"])
        vname = vessel_data.get("name") or vessel_data.get("vessel_name", "Unknown")
        vtype = vessel_data.get("ship_type") or vessel_data.get("vessel_type", "Cargo")
        flag = vessel_data.get("flag") or vessel_data.get("flag_country", "Unknown")
        dest = vessel_data.get("destination", "Open Sea")
        lat = float(vessel_data.get("lat") if vessel_data.get("lat") is not None else vessel_data.get("current_latitude", 0.0))
        lon = float(vessel_data.get("lon") if vessel_data.get("lon") is not None else vessel_data.get("current_longitude", 0.0))
        sog = float(vessel_data.get("sog") if vessel_data.get("sog") is not None else vessel_data.get("speed_knots", 0.0))
        cog = float(vessel_data.get("cog") if vessel_data.get("cog") is not None else vessel_data.get("course_degrees", 0.0))
        is_live = 1 if vessel_data.get("is_live") else 0
        nav_status = vessel_data.get("nav_status", "قيد الإبحار")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. تحديث جدول vessels القياسي للمرحلة 2
            cursor.execute("""
                INSERT INTO vessels (
                    mmsi, name, ship_type, flag, lat, lon, sog, cog, destination, last_seen, is_live
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                ON CONFLICT(mmsi) DO UPDATE SET
                    name=excluded.name,
                    ship_type=excluded.ship_type,
                    flag=excluded.flag,
                    lat=excluded.lat,
                    lon=excluded.lon,
                    sog=excluded.sog,
                    cog=excluded.cog,
                    destination=excluded.destination,
                    last_seen=CURRENT_TIMESTAMP,
                    is_live=excluded.is_live
            """, (mmsi, vname, vtype, flag, lat, lon, sog, cog, dest, is_live))

            # 2. تحديث جدول ais_vessels المتوافق مع الواجهات
            cursor.execute("""
                INSERT INTO ais_vessels (
                    mmsi, vessel_name, imo_number, vessel_type, flag_country,
                    destination, eta, current_latitude, current_longitude,
                    speed_knots, course_degrees, nav_status, last_signal_at, is_live
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                ON CONFLICT(mmsi) DO UPDATE SET
                    vessel_name=excluded.vessel_name,
                    vessel_type=excluded.vessel_type,
                    destination=excluded.destination,
                    current_latitude=excluded.current_latitude,
                    current_longitude=excluded.current_longitude,
                    speed_knots=excluded.speed_knots,
                    course_degrees=excluded.course_degrees,
                    nav_status=excluded.nav_status,
                    last_signal_at=CURRENT_TIMESTAMP,
                    is_live=excluded.is_live
            """, (
                mmsi,
                vname,
                vessel_data.get("imo_number", 0),
                vtype,
                flag,
                dest,
                vessel_data.get("eta", ""),
                lat,
                lon,
                sog,
                cog,
                nav_status,
                is_live
            ))
            conn.commit()

    def update_vessel(self, vessel_data: Dict[str, Any]):
        return self.upsert_vessel(vessel_data)

    def get_vessels(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ais_vessels ORDER BY last_signal_at DESC LIMIT ?", (limit,))
            rows = [dict(row) for row in cursor.fetchall()]
            for r in rows:
                is_live_bool = bool(r.get("is_live", 0))
                r["is_live"] = is_live_bool
                r["mode_badge"] = "🟢 حي مباشر" if is_live_bool else "🟡 محاكاة"
            return rows

    # إدارة سجل حالة المصادر (المرحلة 2.5)
    def upsert_source_status(
        self,
        name: str,
        url: str,
        source_type: str,
        trust_score: int = 70,
        enabled: bool = True,
        last_status: str = "🟢 نشط",
        last_fetched_at: Optional[str] = None,
        items_count: int = 0
    ):
        ts = last_fetched_at or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO source_registry_status (
                    name, url, source_type, trust_score, enabled, last_status, last_fetched_at, items_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    url=excluded.url,
                    source_type=excluded.source_type,
                    trust_score=excluded.trust_score,
                    last_status=excluded.last_status,
                    last_fetched_at=excluded.last_fetched_at,
                    items_count=excluded.items_count
            """, (name, url, source_type, trust_score, 1 if enabled else 0, last_status, ts, items_count))
            conn.commit()

    def set_source_enabled(self, name: str, enabled: bool):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE source_registry_status SET enabled = ?, last_status = ? WHERE name = ?",
                (1 if enabled else 0, "🟢 نشط" if enabled else "⏸️ متوقف يدوياً", name)
            )
            conn.commit()

    def is_source_enabled(self, name: str, default: bool = True) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT enabled FROM source_registry_status WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row is None:
                return default
            return bool(row["enabled"])

    def get_sources_status(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM source_registry_status ORDER BY trust_score DESC, name ASC")
            return [dict(row) for row in cursor.fetchall()]

    def get_kpis(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM osint_events")
            total_events = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM osint_events WHERE urgency_level = 'قصوى'")
            critical_events = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM osint_events WHERE fact_check_status LIKE 'مؤكد%'")
            verified_events = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM ais_vessels")
            active_vessels = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM sources WHERE is_active = 1")
            active_sources = cursor.fetchone()["count"]

            return {
                "total_events": total_events,
                "critical_events": critical_events,
                "verified_events": verified_events,
                "active_vessels": active_vessels,
                "active_sources": active_sources,
                "verification_rate": round((verified_events / total_events * 100) if total_events > 0 else 0, 1),
                "storage_backend": self.get_backend_name(),
            }

    # واجهات متوافقة إضافية (Aliases) للمرحلة 3 (Turso / SQLite)
    def save_news(self, event_data: Dict[str, Any]) -> int:
        return self.add_event(event_data)

    def get_news(self, limit: int = 100, category: Optional[str] = None, urgency: Optional[str] = None, search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.get_events(limit=limit, category=category, urgency=urgency, search_query=search_query)

    def save_vessel(self, vessel_data: Dict[str, Any]):
        return self.upsert_vessel(vessel_data)

    def update_vessels(self, vessels_list: List[Dict[str, Any]]):
        for v in vessels_list:
            self.upsert_vessel(v)


DatabaseManager = OSINTDatabase
db = OSINTDatabase()
save_rejected_news = db.save_rejected_news
