---
title: Platform OX — OSINT Hub
emoji: 🛡️
colorFrom: blue
colorTo: gray
sdk: streamlit
app_file: app.py
pinned: false
---

# 🛡️ منصة الرصد العلني | Platform OX — OSINT Hub

[![Deployed on Streamlit Cloud](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://khaldalshwy-platform-ox-osint-hub-app-u5lmri.streamlit.app/)

منصة استخبارات المصادر المفتوحة (**OSINT**) المتكاملة للرصد اللحظي، التحليل اللغوي والمكاني (**NLP & GIS**)، تتبع الملاحة البحرية (**AIS**)، وإصدار تقارير تقدير الموقف الاستخباراتية وفق منهجية **مركز معطى**.

---

## 🌐 روابط التطبيق الحي والمستودع الرسمي

- **الرابط الحي للتطبيق (Streamlit Community Cloud — 100% مجاني):** [https://khaldalshwy-platform-ox-osint-hub-app-u5lmri.streamlit.app/](https://khaldalshwy-platform-ox-osint-hub-app-u5lmri.streamlit.app/)
- **رابط المستودع الرسمي على GitHub:** [https://github.com/khaldalshwy/platform-ox-osint-hub](https://github.com/khaldalshwy/platform-ox-osint-hub)
- **بنية الاستضافة:** `Streamlit Community Cloud (Python 3.11)` + قاعدة بيانات سحابية دائمة `Turso (libSQL / SQLite Cloud — 9GB Free)` مع تراجع تلقائي آمن إلى `SQLite` المحلي.

---

## ⚡ تعليمات الاستخدام السريعة (Quick Start)

1. **افتح المنصة الحية مباشرة:** [https://khaldalshwy-platform-ox-osint-hub-app-u5lmri.streamlit.app/](https://khaldalshwy-platform-ox-osint-hub-app-u5lmri.streamlit.app/)
2. **تشغيل الرصد الحي:** اضغط على زر **`🚀 تشغيل دورة استخبارات شاملة`** في الشريط الجانبي أو غرفة العمليات لسحب أحدث الأخبار من **19 مصدراً مفتوحاً**، وتطبيق **فلتر الصلة اليمنية** على قسم `سياسي/عام` فقط.
3. **استعراض الخرائط والرادار:** انتقل إلى تبويب **`الخريطة الاستخباراتية`** أو **`الرادار البحري (AIS)`** لاستعراض صور Google Earth التفاعلية وأزرار الانتقال السريع (`Fly-To`).
4. **تصدير التقارير والملفات:** من تبويب **`محرك إصدار التقارير`** حمّل تقارير `SITREP` أو `FLASH` أو `MARITIME` بصيغة `HTML/MD`، أو حمّل ملفات `KML` (لـ Google Earth Pro) و`GEXF` (لـ Gephi) و`CSV` (لـ Excel).
5. **مراجعة تدقيق الفلترة:** راجع [FILTER_LOG.md](FILTER_LOG.md) للاطلاع على إحصائيات القبول والرفض، و[الجهوزية.md](الجهوزية.md) لتقرير الجهوزية الكامل.

---

## 🖥️ نظرة عامة على واجهات المنصة وميزاتها

تعمل المنصة بالثيم **الأبيض الثلجي (`⚪ الأبيض الثلجي`) كخيار رئيسي افتراضي** مع توفر **النمط الداكن (`🌙 النمط الداكن`) كخيار ثانوي**، وتضم 8 شاشات عملياتية متكاملة:

1. **غرفة العمليات المركزية (`Live Ops`):**
   - شريط كود الإنذار التكتيكي (`🚨 أحمر / ⚠️ برتقالي / 🟢 أخضر`).
   - 4 بطاقات مؤشرات أداء حية (`KPIs`): إجمالي الأحداث، الأحداث العاجلة، القطع البحرية النشطة، ونسبة التحقق.
   - تشغيل دورة استخبارات شاملة بضغطة زر مع شريط تقدم حي.
   - رسوم بيانية تفاعلية (`Pie Chart` لتوزيع التصنيفات + `Histogram` لمؤشر التوتر والأهمية).
   - سجل الأحداث المفهرس القابل للبحث والفلترة مع تصدير مباشر إلى `Excel (.CSV)`.
2. **إدارة وحالة المصادر (`Sources Status`):**
   - مراقبة حية لـ **19 مصدراً مفتوحاً** (8 مصادر يمنية مباشرة بدرجة ثقة `90`، 5 مصادر بحرية/أمنية دولية بدرجة ثقة `70`، و6 خلاصات Google News/BBC) + رادار `AISStream.io`.
   - زر `🔄 اختبار المصادر` لفحص استجابة `HTTP 200 + XML`، وزر `⏸️ إيقاف/تشغيل مصدر` للتحكم الفردي، مع عرض سجل الأخبار المستبعدة (`rejected_news`).
3. **الرادار البحري وتتبع السفن (`Maritime AIS Radar`):**
   - خريطة **Google Earth Satellite Hybrid** حقيقية تعرض السفن والناقلات، متجهات الحركة (`Heading Vectors`)، والموانئ اليمنية ونطاقات الرصد (`25 NM`).
   - دعم البث الحي عبر `AISStream.io WebSocket` (`🟢 حي مباشر`) أو المحاكاة التلقائية (`🟡 محاكاة`)، مع تصدير `.KML` لبرنامج Google Earth Pro وتصدير `.CSV` لبرنامج Excel.
4. **الخريطة الاستخباراتية المكانية (`Geospatial GIS`):**
   - خريطة **Google Earth** التفاعلية بطبقاتها الأربع (`Hybrid`, `Satellite`, `Terrain`, `Roadmap`) مع شريط انتقال جوي فوري (**Fly-To**) لأهم المضايق والموانئ والمدن اليمنية.
5. **محلل المحتوى والتحقق (`NLP Analyzer`):**
   - استخراج الكيانات المسماة (`NER`)، قياس قطبية المشاعر ومؤشر التهديد، وتطبيق **فلتر الصلة اليمنية (`Yemen Relevance Filter`)** على قسم `"سياسي/عام"` لمنع تسرب الأخبار الفنية أو التقنية أو الرياضية غير اليمنية.
6. **شبكة الكيانات والعلاقات (`Network Graph`):**
   - بناء مصفوفة الترابط بين الكيانات والأحداث وتصديرها بصيغة `.GEXF` لبرنامج التحليل الشبكي `Gephi`.
7. **محرك إصدار التقارير (`Reports Engine`):**
   - توليد وتحميل تقارير تقدير الموقف (`SITREP`)، برقيات الإنذار العاجل (`FLASH`)، وملفات الرصد البحري (`MARITIME`) بصيغتي `HTML` (طباعة رسمية) و`Markdown (.md)`.
8. **عن المنصة ومنهجية معطى:**
   - توثيق المنهجية الاستخباراتية ومعايير التثليث والتحقق.

---

## 🚀 كيفية التشغيل محلياً (Local Setup)

1. **تثبيت الاعتماديات:**
   ```bash
   pip install -r requirements.txt
   ```
2. **إعداد متغيرات البيئة (اختياري):**
   انسخ ملف `.env.example` إلى `.env` وأضف مفاتيحك المجانية إن توفرت (يعمل النظام تلقائياً بدونها عبر SQLite المحلي ووضع المحاكاة البحرية):
   ```bash
   cp .env.example .env
   ```
3. **تشغيل المنصة:**
   ```bash
   streamlit run app.py
   ```
   أو عبر ملف التشغيل السريع في ويندوز: `تشغيل.bat`.

---

## ☁️ كيفية النشر المجاني على Hugging Face Spaces + Turso

1. أنشئ قاعدة بيانات مجانية على **[Turso.tech](https://turso.tech)** واحصل على `TURSO_DATABASE_URL` و`TURSO_AUTH_TOKEN`.
2. أنشئ **Space** جديداً على **[Hugging Face Spaces](https://huggingface.co/spaces)** من نوع **Streamlit** باسم `platform-ox-osint-hub`.
3. في إعدادات الـ Space (`Settings -> Variables and secrets -> New secret`)، أضف الأسرار التالية:
   - `TURSO_DATABASE_URL`
   - `TURSO_AUTH_TOKEN`
   - `AISSTREAM_API_KEY` *(اختياري لتفعيل البث الحي للسفن)*
4. ارفع ملفات المستودع عبر `git push`:
   ```bash
   git init
   git remote add space https://huggingface.co/spaces/<YOUR_HF_USERNAME>/platform-ox-osint-hub
   git add .
   git commit -m "Deploy Platform OX OSINT Hub"
   git push --force space main
   ```
   *(راجع ملف [DEPLOYMENT.md](DEPLOYMENT.md) لشرح الخطوات التفصيلية سطراً بسطر).*
