# 🚀 دليل النشر السحابي المجاني الشامل | Platform OX — Deployment Guide

يوثق هذا الدليل خطوات نشر **منصة الرصد العلني (Platform OX — OSINT Hub)** على الإنترنت مجاناً **100%** باستخدام:
1. **Hugging Face Spaces (Streamlit SDK):** لاستضافة وتشغيل التطبيق سحابياً.
2. **Turso (libSQL / SQLite Cloud — 9GB Free):** لضمان بقاء قاعدة البيانات (`osint_events`, `rejected_news`, `vessels`, `source_registry_status`) وعدم فقدانها عند إعادة تشغيل الحاوية أو تحديث الكود.
3. **AISStream.io (Free WebSocket API):** لتتبع السفن الحية في البحر الأحمر ومضيق باب المندب (مع تراجع تلقائي لوضع المحاكاة `🟡 محاكاة` عند عدم إدخال المفتاح).

---

## 🌐 رابط التطبيق المنشور

- **رابط العرض الحي (Hugging Face Space):**
  [https://huggingface.co/spaces/khaldalshwy/platform-ox-osint-hub](https://huggingface.co/spaces/khaldalshwy/platform-ox-osint-hub)
- **رابط العرض المباشر بملء الشاشة (Direct Embed URL):**
  [https://khaldalshwy-platform-ox-osint-hub.static.hf.space/index.html](https://khaldalshwy-platform-ox-osint-hub.static.hf.space/index.html)

---

## 🛠️ توثيق المشكلات التي واجهتنا أثناء النشر وكيف تم حلها (Troubleshooting Log)

1. **مشكلة إلغاء `sdk: streamlit` ومطالبة Hugging Face باشتراك مدفوع (`402 Payment Required`) لـ Docker/Gradio:**
   - **المشكلة:** عند محاولة إنشاء الـ Space عبر واجهة برمجة تطبيقات Hugging Face (`api/repos/create`)، أرجع الخادم أولاً خطأ `Invalid option: expected one of "gradio"|"docker"|"static" at sdk` بعد إيقاف خيار `streamlit` القديم، وعند تجربة `docker` أرجع `402 Client Error: Payment Required — Static Spaces are free for everyone, but hosting Gradio and Docker Spaces on free cpu-basic requires a PRO subscription`.
   - **الحل الهندسي المجاني 100%:** تم اعتماد بنية مزدوجة تحافظ على مجانية المنصة بالكامل (`$0`):
     1. الإبقاء على كامل ملفات تطبيق Streamlit والباك-إند (`app.py`, `01_acquisition`, `02_storage/db_adapter.py`, `03_processing`, `06_presentation`, `Dockerfile`, `requirements.txt`, `runtime.txt`) لتعمل محلياً أو على أي خادم بايثون.
     2. توليد واجهة الويب السحابية التفاعلية الكاملة [index.html](index.html) عبر [build_cloud_index.py](build_cloud_index.py) ونشرها على `khaldalshwy/platform-ox-osint-hub` بنمط `sdk: static` المجاني 100%، مدمجة بالبيانات الحية المفلترة من قاعدة البيانات وخرائط Google Earth الحقيقية ومخططات Plotly وتوليد التقارير (`SITREP/FLASH/MARITIME`) وتصدير `KML/GEXF/CSV` مع حفظ الحالة الدائم عبر `Turso / Cloud Storage`.
2. **مشكلة توافق `server.enableCORS = false` في `.streamlit/config.toml`:**
   - **المشكلة:** أظهر Streamlit تحذيراً بأن `enableCORS = false` يتعارض مع `enableXsrfProtection = true`.
   - **الحل:** تمت إضافة `enableXsrfProtection = false` في `.streamlit/config.toml` لضمان التوافق التام بدون تحذيرات.

---

## 🗄️ أولاً: إنشاء قاعدة البيانات السحابية المجانية على Turso (سطراً بسطر)

1. افتح الموقع الرسمي **[https://turso.tech](https://turso.tech)** وسجّل حساباً مجانياً (عبر GitHub أو البريد الإلكتروني — يعطيك **9GB** مجاناً مدى الحياة بدون بطاقة ائتمان).
2. من لوحة التحكم (أو عبر أداة سطر الأوامر `turso`)، أنشئ قاعدة بيانات جديدة باسم `platform-ox-db`:
   ```bash
   # إذا كنت تستخدم Turso CLI:
   turso auth login
   turso db create platform-ox-db
   ```
   أو من الواجهة الرسومية في الموقع: اضغط **Create Database** ← سمّها `platform-ox-db` ← اختر أقرب منطقة ← اضغط **Create**.
3. استخرج رابط القاعدة (`TURSO_DATABASE_URL`):
   ```bash
   turso db show platform-ox-db --url
   # مثال النتيجة:
   # libsql://platform-ox-db-username.turso.io
   ```
4. أنشئ مفتاح المصادقة (`TURSO_AUTH_TOKEN`):
   ```bash
   turso db tokens create platform-ox-db
   # انسخ التوكن الطويل الذي يبدأ بـ eyJ...
   ```
   *(أو من لوحة تحكم Turso في المتصفح: اضغط على `platform-ox-db` ← اضغط **Generate Token** ← انسخ الرابط والتوكن).*

> **ملاحظة تقنية:** يقوم الملف [02_storage/db_adapter.py](02_storage/db_adapter.py) تلقائياً بإنشاء كافة الجداول (`osint_events`, `rejected_news`, `vessels`, `ais_vessels`, `sources`, `source_registry_status`, `extracted_entities`, `entity_relationships`) فور أول اتصال بـ Turso دون الحاجة لأي ترحيل يدوي!

---

## ☁️ ثانياً: إنشاء وإعداد Hugging Face Space (سطراً بسطر)

1. سجّل الدخول إلى حسابك على **[https://huggingface.co](https://huggingface.co)**.
2. من القائمة العلوية، اضغط على **+ New** ← اختر **Space** (أو انتقل إلى `https://huggingface.co/new-space`).
3. املأ بيانات الـ Space كالتالي:
   - **Space name:** `platform-ox-osint-hub`
   - **Select the Space SDK:** اختر **Streamlit**
   - **Space hardware:** اختر `CPU basic · 2 vCPU · 16 GB · FREE`
   - **Visibility:** اختر **Public**
4. اضغط **Create Space**.

---

## 🔐 ثالثاً: إضافة الأسرار (Secrets) في Hugging Face Spaces

> ⚠️ **تنبيه أمني صارم:** لا تضع أي توكن أو مفتاح داخل ملفات الكود أو ترفع ملف `.env` إلى Git. تُدار جميع الأسرار حصرياً عبر قسم **Variables and secrets**.

1. داخل صفحة الـ Space الخاص بك، اضغط على تبويب **Settings** في الأعلى.
2. انزل إلى قسم **Variables and secrets** واضغط على زر **New secret**.
3. أضف الأسرار الثلاثة التالية واحداً تلو الآخر:

| Name (اسم السر) | Value (القيمة) | الوظيفة |
| :--- | :--- | :--- |
| `TURSO_DATABASE_URL` | `libsql://platform-ox-db-xxxx.turso.io` | رابط قاعدة بيانات Turso السحابية الدائمة |
| `TURSO_AUTH_TOKEN` | `eyJhbGciOiJFZERTQ...` | توكن الوصول لقاعدة بيانات Turso |
| `AISSTREAM_API_KEY` | `your_aisstream_key` *(اختياري)* | مفتاح البث الحي للسفن من [aisstream.io](https://aisstream.io) |

---

## 📤 رابعاً: رفع ملفات المشروع (Deployment) وتحديثه

يمكنك رفع المشروع وتحديثه بإحدى الطريقتين التاليتين:

### الطريقة أ: النشر الآلي السريع بأمر واحد عبر سكربت `deploy_to_hf.py`
يوفر المشروع أداة نشر جاهزة ترفع كافة الملفات وتضبط الـ Space مباشرة عبر `huggingface_hub`:
```bash
pip install huggingface_hub
python deploy_to_hf.py --token hf_YOUR_WRITE_TOKEN --repo-id YOUR_USERNAME/platform-ox-osint-hub
```

### الطريقة ب: النشر والتحديث القياسي عبر `git push`
1. افتح موجه الأوامر (`PowerShell` أو `CMD`) داخل مجلد المشروع `A:\platform_ox`:
   ```bash
   git init
   git branch -M main
   git remote add space https://huggingface.co/spaces/<YOUR_USERNAME>/platform-ox-osint-hub
   ```
2. أضف الملفات وارفعها (ملف `.gitignore` يمنع رفع `.env` أو قواعد البيانات المحلية تلقائياً):
   ```bash
   git add .
   git commit -m "Release Platform OX v3.0 — Cloud OSINT Hub"
   git push --force space main
   ```
   *(عند طلب كلمة المرور أثناء `git push`، استخدم **Hugging Face Access Token** بصلاحية `Write` من إعدادات حسابك `Settings -> Access Tokens`).*

### 🔄 كيفية تحديث التطبيق لاحقاً
عند إجراء أي تعديل برمجي مستقبلي، يكفي تشغيل:
```bash
git add .
git commit -m "Update intelligence filters and sources"
git push space main
```
سيقوم Hugging Face Spaces بإعادة بناء وتشغيل النسخة الجديدة تلقائياً خلال أقل من دقيقة مع بقاء جميع بياناتك محفوظة في **Turso**.

---

## 🛠️ خامساً: استكشاف الأخطاء ومراقبة السجلات (Build & Runtime Logs)

في أعلى صفحة الـ Space على Hugging Face، اضغط على زر **Logs** بجوار حالة التشغيل (`Building` / `Running`):

1. **تبويب `Build` (سجل البناء):**
   - يعرض عملية قراءة `runtime.txt` (`python-3.11`) وتثبيت المكتبات من `requirements.txt`.
   - **إذا ظهر خطأ في إصدار مكتبة:** تأكد من عدم وجود مسافات زائدة في `requirements.txt` وأن جميع الحزم متوافقة مع Python 3.11.
2. **تبويب `Container` / `App` (سجل التشغيل الحي Runtime Logs):**
   - يعرض رسائل بدء تشغيل `streamlit run app.py` وحالة الاتصال بـ Turso ومصادر RSS.
   - **كيفية التحقق من اتصال Turso:** انظر في أسفل الشريط الجانبي للواجهة؛ إذا ظهرت شارة `☁️ Turso Cloud (SQLite السحابي)` فالاتصال السحابي نشط 100%. إذا ظهرت `💾 SQLite محلي (Fallback)` فتأكد من صحة اسم وقيمة `TURSO_DATABASE_URL` و`TURSO_AUTH_TOKEN` في قسم **Secrets** ثم اضغط **Factory reboot** من إعدادات الـ Space.

---

## 💾 سادساً: كيفية سحب نسخة احتياطية (Backup) من قاعدة بيانات Turso

يمكنك سحب نسخة احتياطية كاملة من قاعدة بيانات Turso السحابية في أي وقت إلى جهازك المحلي بطريقتين:

### 1. عبر أداة سطر الأوامر `turso`:
```bash
turso db shell platform-ox-db .dump > turso_backup_$(date +%Y%m%d).sql
```

### 2. عبر بايثون محلياً (تصدير مباشر إلى ملف SQLite محلي أو JSON):
```bash
python -c "
import sys, json
sys.path.insert(0, '02_storage')
from database import db
backup = {
    'events': db.get_events(limit=5000),
    'rejected_news': db.get_rejected_news(limit=5000),
    'vessels': db.get_vessels(limit=500),
    'sources': db.get_sources_status()
}
with open('turso_full_backup.json', 'w', encoding='utf-8') as f:
    json.dump(backup, f, ensure_ascii=False, indent=2)
print('Backup saved to turso_full_backup.json')
"
```

---

## 🔒 سابعاً: تنبيهات الأمان وحماية المفاتيح

1. **لا تشارك التوكنات أبداً:** لا ترسل `TURSO_AUTH_TOKEN` أو `AISSTREAM_API_KEY` أو `HF_TOKEN` في محادثات عامة أو داخل ملفات الكود.
2. **فحص `.gitignore` قبل الرفع:** تأكد دائماً أن ملف `.env` وملف `.streamlit/secrets.toml` مدرجان في `.gitignore` (مُعدّ مسبقاً في المستودع).
3. **تدوير المفاتيح (Token Rotation):** إذا اشتبهت بتسرب مفتاح Turso، يمكنك إبطاله فوراً عبر الأمر `turso db tokens invalidate platform-ox-db` وتوليد مفتاح جديد وتحديثه في **Secrets** على Hugging Face Spaces.

