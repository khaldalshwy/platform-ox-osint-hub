# -*- coding: utf-8 -*-
"""
طبقة التجريد الموحدة لقاعدة البيانات (02_storage/db_adapter.py)
المرحلة 3: دعم قاعدة البيانات السحابية المجانية Turso (libSQL / SQLite Cloud)
مع التراجع التلقائي الآمن (Fallback) إلى قاعدة بيانات SQLite المحلية.

المنطق:
  - إذا وُجد متغيرا البيئة TURSO_DATABASE_URL و TURSO_AUTH_TOKEN (في البيئة، أو .env، أو st.secrets)
    بقيم حقيقية (غير القيم الافتراضية في .env.example) -> يتصل سحابياً بـ Turso.
  - وإلا -> يستخدم قاعدة بيانات SQLite المحلية (02_storage/local_osint.db) تلقائياً.
"""

import os
import sqlite3
import datetime
from typing import List, Dict, Any, Optional, Tuple, Sequence
import requests

_STORAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_STORAGE_DIR)
DEFAULT_SQLITE_PATH = os.path.join(_STORAGE_DIR, "local_osint.db")

_PLACEHOLDER_URLS = {
    "",
    "libsql://your-db.turso.io",
    "https://your-db.turso.io",
    "your_turso_url_here",
}
_PLACEHOLDER_TOKENS = {
    "",
    "your_token_here",
    "your_turso_auth_token_here",
}


def _read_config_value(key: str) -> str:
    """قراءة المتغير من متغيرات النظام، أو Streamlit Secrets، أو ملف .env"""
    # 1. متغيرات البيئة المباشرة
    val = os.environ.get(key, "").strip()
    if val:
        return val

    # 2. Streamlit Secrets (في Hugging Face Spaces)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            s_val = str(st.secrets[key]).strip()
            if s_val:
                return s_val
    except Exception:
        pass

    # 3. ملف .env المحلي إن وُجد
    for env_path in [
        os.path.join(_PROJECT_ROOT, ".env"),
        os.path.join(_PROJECT_ROOT, "05_devops", ".env"),
    ]:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        if k.strip() == key:
                            return v.strip().strip('"').strip("'")
            except Exception:
                pass
    return ""


def get_turso_credentials() -> Tuple[Optional[str], Optional[str]]:
    """استرجاع رابط وتوكن Turso إذا كانا مضبوطين بقيم فعلية صالحة"""
    url = _read_config_value("TURSO_DATABASE_URL")
    token = _read_config_value("TURSO_AUTH_TOKEN")
    if url in _PLACEHOLDER_URLS or token in _PLACEHOLDER_TOKENS:
        return None, None
    return url, token


class HybridRow(dict):
    """
    صف هجين يحاكي sqlite3.Row تماماً:
    يدعم الوصول عبر اسم العمود row['title']، وعبر الفهرس الرقمي row[0]، والتحويل dict(row).
    """
    def __init__(self, columns: Sequence[str], values: Sequence[Any]):
        super().__init__(zip(columns, values))
        self._columns = list(columns)
        self._values = list(values)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return super().__getitem__(key)

    def keys(self):
        return self._columns


class TursoCursor:
    """
    مؤشر تنفيذ استعلامات متوافق مع sqlite3.Cursor يعمل فوق Turso (عبر libsql_client أو Hrana v2 HTTP API).
    """
    def __init__(self, connection: "TursoConnection"):
        self.connection = connection
        self._rows: List[HybridRow] = []
        self.lastrowid: int = 0
        self.rowcount: int = 0

    def execute(self, sql: str, params: Sequence[Any] = ()) -> "TursoCursor":
        rows, last_id, affected = self.connection._execute_sql(sql, params)
        self._rows = rows
        self.lastrowid = last_id
        self.rowcount = affected
        return self

    def fetchone(self) -> Optional[HybridRow]:
        if not self._rows:
            return None
        return self._rows.pop(0)

    def fetchall(self) -> List[HybridRow]:
        rows = list(self._rows)
        self._rows = []
        return rows


class TursoConnection:
    """
    اتصال سحابي بقاعدة بيانات Turso متوافق مع واجهة sqlite3.Connection:
    يدعم Context Manager (with conn:)، ويستخدم libsql_client إن توفر أو بروتوكول Turso HTTP Pipeline v2 المباشر.
    """
    def __init__(self, db_url: str, auth_token: str, timeout: int = 15):
        self.raw_url = db_url.strip()
        # تحويل libsql:// أو wss:// إلى https:// لبروتوكول HTTP المتزامن المستقر
        if self.raw_url.startswith("libsql://"):
            self.http_url = "https://" + self.raw_url[len("libsql://"):]
        elif self.raw_url.startswith("wss://"):
            self.http_url = "https://" + self.raw_url[len("wss://"):]
        elif self.raw_url.startswith("http://") or self.raw_url.startswith("https://"):
            self.http_url = self.raw_url
        else:
            self.http_url = f"https://{self.raw_url}"

        self.http_url = self.http_url.rstrip("/")
        self.auth_token = auth_token.strip()
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        })

    def __enter__(self) -> "TursoConnection":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def cursor(self) -> TursoCursor:
        return TursoCursor(self)

    def commit(self):
        # في Turso HTTP Pipeline يتم اعتماد المعاملات (Auto-commit) مع كل طلب
        pass

    def close(self):
        try:
            self._session.close()
        except Exception:
            pass

    @staticmethod
    def _encode_arg(val: Any) -> Dict[str, Any]:
        if val is None:
            return {"type": "null"}
        if isinstance(val, bool):
            return {"type": "integer", "value": "1" if val else "0"}
        if isinstance(val, int):
            return {"type": "integer", "value": str(val)}
        if isinstance(val, float):
            return {"type": "float", "value": val}
        if isinstance(val, bytes):
            import base64
            return {"type": "blob", "base64": base64.b64encode(val).decode("ascii")}
        return {"type": "text", "value": str(val)}

    @staticmethod
    def _decode_cell(cell: Dict[str, Any]) -> Any:
        ctype = cell.get("type")
        if ctype == "null" or ctype is None:
            return None
        if ctype == "integer":
            return int(cell.get("value", 0))
        if ctype == "float":
            return float(cell.get("value", 0.0))
        return cell.get("value")

    def _execute_sql(self, sql: str, params: Sequence[Any] = ()) -> Tuple[List[HybridRow], int, int]:
        """تنفيذ استعلام SQL على Turso عبر Hrana v2 Pipeline أو libsql_client"""
        # 1. المحاولة عبر Turso Hrana v2 Pipeline API (الأسرع والأكثر استقراراً داخل Streamlit)
        pipeline_url = f"{self.http_url}/v2/pipeline"
        stmt: Dict[str, Any] = {"sql": sql}
        if params:
            stmt["args"] = [self._encode_arg(p) for p in params]

        payload = {
            "requests": [
                {"type": "execute", "stmt": stmt},
                {"type": "close"},
            ]
        }

        resp = self._session.post(pipeline_url, json=payload, timeout=self.timeout)
        if resp.status_code != 200:
            # محاولة بديلة عبر libsql_client إن كان مثبتاً
            try:
                import libsql_client
                with libsql_client.create_client_sync(url=self.http_url, auth_token=self.auth_token) as client:
                    rs = client.execute(sql, list(params) if params else [])
                    cols = list(rs.columns)
                    hybrid_rows = [HybridRow(cols, list(r)) for r in rs.rows]
                    last_id = int(rs.last_insert_rowid or 0)
                    return hybrid_rows, last_id, int(rs.rows_affected or 0)
            except Exception:
                raise RuntimeError(f"Turso HTTP Error {resp.status_code}: {resp.text[:300]}")

        data = resp.json()
        results = data.get("results", [])
        if not results:
            return [], 0, 0

        first = results[0]
        if first.get("type") == "error":
            err_msg = first.get("error", {}).get("message", "Unknown Turso SQL Error")
            raise RuntimeError(f"Turso SQL Error: {err_msg}")

        exec_res = first.get("response", {}).get("result", {})
        cols_meta = exec_res.get("cols", [])
        col_names = [c.get("name", f"col_{i}") for i, c in enumerate(cols_meta)]
        raw_rows = exec_res.get("rows", [])

        parsed_rows: List[HybridRow] = []
        for r in raw_rows:
            vals = [self._decode_cell(c) for c in r]
            parsed_rows.append(HybridRow(col_names, vals))

        last_insert_rowid = exec_res.get("last_insert_rowid")
        last_id = int(last_insert_rowid) if last_insert_rowid is not None else 0
        affected = int(exec_res.get("affected_row_count", 0) or 0)
        return parsed_rows, last_id, affected


class DatabaseAdapter:
    """
    مدير الاتصال الهجين بقاعدة البيانات (Turso Cloud أو SQLite المحلي):
    يوفر اتصالاً متوافقاً 100% مع الكود الحالي.
    """
    def __init__(self, sqlite_path: Optional[str] = None, force_sqlite: bool = False):
        self.sqlite_path = sqlite_path or DEFAULT_SQLITE_PATH
        self.force_sqlite = force_sqlite
        self.turso_url, self.turso_token = (None, None) if force_sqlite else get_turso_credentials()
        self._turso_verified = False

        if self.turso_url and self.turso_token:
            # فحص سريع لصلاحية الاتصال بـ Turso، والتراجع الآمن لـ SQLite في حال فشل المصادقة
            try:
                with TursoConnection(self.turso_url, self.turso_token, timeout=10) as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT 1")
                self._turso_verified = True
            except Exception as e:
                print(f"[!] تعذر الاتصال بـ Turso ({e}) — تم التراجع التلقائي إلى SQLite المحلي.")
                self._turso_verified = False

    def is_turso_enabled(self) -> bool:
        return bool(self._turso_verified and self.turso_url and self.turso_token)

    def get_backend_name(self) -> str:
        return "Turso Cloud (libSQL)" if self.is_turso_enabled() else "SQLite Local (Fallback)"

    def get_connection(self):
        """إرجاع كائن اتصال (TursoConnection أو sqlite3.Connection)"""
        if self.is_turso_enabled():
            return TursoConnection(self.turso_url, self.turso_token)
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

