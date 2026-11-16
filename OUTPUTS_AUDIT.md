# 📦 التقرير التقني الشامل للمخرجات | Platform OX Outputs Audit (`OUTPUTS_AUDIT.md`)

**تاريخ التدقيق:** 2026-11-16  
**نطاق التدقيق:** الكود الفعلي في `06_presentation/reporting/report_generator.py`، `06_presentation/streamlit_app/app.py`، `03_processing/network_analysis/network_graph.py`، `01_acquisition/maritime_ais/ais_tracker.py`، و`build_cloud_index.py`.  
**منهجية التوثيق:** استخراج حرفي ودقيق من الشيفرة المصدرية الفعلية؛ أي صيغة غير موجودة في الكود موثقة صراحةً بـ **"غير موجود"**.

---

## القسم 1: جرد المخرجات (Output Inventory)

| # | المخرج | الصيغة | الملف المصدر | الدالة المسؤولة | مكان الحفظ | طريقة الوصول | ثابت/ديناميكي |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- | :---: |
| **1** | تقرير تقدير الموقف الشامل (`SITREP`) | `HTML` + `MD` | `06_presentation/reporting/report_generator.py` | `ReportGenerator.generate_situation_report("SITREP")` | `06_presentation/reporting/generated_reports/report_sitrep_YYYYMMDD_HHMMSS.{html,md}` | زر في غرفة العمليات / محرك التقارير + `st.download_button` | ديناميكي (يدوي عند الطلب) |
| **2** | برقية الإنذار الأمني العاجل (`FLASH`) | `HTML` + `MD` | `06_presentation/reporting/report_generator.py` | `ReportGenerator.generate_situation_report("FLASH")` | `06_presentation/reporting/generated_reports/report_flash_YYYYMMDD_HHMMSS.{html,md}` | زر توليد في محرك التقارير + `st.download_button` | ديناميكي (يدوي عند الطلب) |
| **3** | ملف الرصد البحري (`MARITIME`) | `HTML` + `MD` | `06_presentation/reporting/report_generator.py` | `ReportGenerator.generate_situation_report("MARITIME")` | `06_presentation/reporting/generated_reports/report_maritime_YYYYMMDD_HHMMSS.{html,md}` | زر توليد في محرك التقارير + `st.download_button` | ديناميكي (يدوي عند الطلب) |
| **4** | ملف خريطة قوقل إيرث الشامل (`Full GIS KML`) | `KML` (XML) | `06_presentation/streamlit_app/app.py` | `generate_google_earth_kml(events_all, vessels)` | يُنشأ في الذاكرة ويُحمّل باسم `osint_google_earth_YYYYMMDD_HHMM.kml` | `st.download_button` في تبويب الخريطة GIS | ديناميكي (عند التحميل) |
| **5** | ملف خريطة الأسطول البحري (`Maritime AIS KML`) | `KML` (XML) | `06_presentation/streamlit_app/app.py` | `generate_google_earth_kml([], vessels)` | يُنشأ في الذاكرة ويُحمّل باسم `maritime_ais_YYYYMMDD_HHMM.kml` | `st.download_button` في تبويب الرادار البحري | ديناميكي (عند التحميل) |
| **6** | ملف شبكة العلاقات (`Gephi Network`) | `GEXF` (XML) | `03_processing/network_analysis/network_graph.py` | `EntityNetworkGraph.export_gexf()` | يُنشأ في الذاكرة ويُحمّل باسم `osint_network_YYYYMMDD.gexf` | `st.download_button` في تبويب شبكة الكيانات | ديناميكي (عند التحميل) |
| **7** | جدول الأحداث المفهرسة (`Events CSV`) | `CSV` (`utf-8-sig`) | `06_presentation/streamlit_app/app.py` | `pd.DataFrame(events).to_csv(index=False)` | يُنشأ في الذاكرة ويُحمّل باسم `osint_events_YYYYMMDD_HHMM.csv` | `st.download_button` في غرفة العمليات | ديناميكي (عند التحميل) |
| **8** | جدول أسطول السفن (`Vessels CSV`) | `CSV` (`utf-8-sig`) | `06_presentation/streamlit_app/app.py` | `df_v[...].to_csv(index=False)` | يُنشأ في الذاكرة ويُحمّل باسم `ais_vessels_YYYYMMDD_HHMM.csv` | `st.download_button` في تبويب الرادار البحري | ديناميكي (عند التحميل) |
| **9** | ملف البذرة السحابية (`Cloud Seed JSON`) | `JSON` | `build_cloud_index.py` | `build_seed_and_index()` | `cloud_seed.json` (جذر المشروع) | يُقرأ تلقائياً عند بدء `OSINTDatabase._seed_if_empty()` | ثابت (يُحدّث عند تشغيل السكربت) |
| **10** | خريطة Google Earth التفاعلية (`Interactive Map`) | `HTML/JS` (Leaflet) | `06_presentation/streamlit_app/app.py` | `render_google_earth_map(...)` | عرض مباشر في المتصفح (`st.components.v1.html`) | تبويب الخريطة GIS وتبويب الرادار البحري | ديناميكي (تلقائي مع إعادة الرسم) |
| **11** | الرسوم البيانية التفاعلية (`Pie & Histogram`) | `Plotly JSON/SVG` | `06_presentation/streamlit_app/app.py` | `px.pie(...)` و `px.histogram(...)` | عرض مباشر في المتصفح (`st.plotly_chart`) | تبويب غرفة العمليات المركزية | ديناميكي (تلقائي) |
| **12** | عناصر الواجهة التحليلية (`KPIs, Banners, Feed, Tables`) | `Streamlit UI` | `06_presentation/streamlit_app/app.py` | منطق التبويبات السبعة | عرض مباشر في المتصفح | كافة التبويبات السبعة | ديناميكي (تلقائي) |
| **13** | تقارير PDF / Excel `.xlsx` / GeoJSON / GraphML / Static Map PNG | — | — | — | **غير موجود** في الكود | غير متاح مباشرة (PDF عبر طباعة المتصفح لـ HTML) | — |

---

## القسم 2: تحليل المخرجات حسب النوع (Outputs by Type)

### أ) التقارير الاستخباراتية (Intelligence Reports)
تُنتَج جميعها عبر الفئة `ReportGenerator` في [06_presentation/reporting/report_generator.py](06_presentation/reporting/report_generator.py):

1. **تقرير تقدير الموقف الشامل (`SITREP`):**
   * **الأقسام:** ترويسة التصنيف والهوية ← 1) المؤشرات التكتيكية (`Executive KPIs`) ← 2) جدول الرصد الميداني (أحدث **15** حدثاً من `osint_events`) ← 3) وضع الملاحة والقطع البحرية (أحدث **10** سفن من `ais_vessels`) ← 4) الاستنتاجات والتوصيات العملياتية + بصمة التحقق `SHA-256`.
   * **الصيغ:** `.html` و`.md` (صيغة `.pdf` المباشرة **غير موجودة**).
   * **الطباعة والهوية البصرية:** نعم، قابل للطباعة الرسمية عبر `@media print` ويحتوي شعار المنصة (`icon.svg`) وخلفية الهيدر والفوتير (`header_background.png`) مدمجة ذاتياً بصيغة `Base64`.
2. **برقية الإنذار الأمني العاجل (`FLASH`):**
   * **الأقسام:** نفس الهيكل الرباعي، لكن جدول الرصد يركز حصرياً على الأحداث ذات مستوى التوتر **`قصوى`** (بحد أقصى **10** أحداث، أو أحدث 5 أحداث إذا لم توجد أحداث قصوى) مع شارة حمراء (`#ef4444`).
   * **الصيغ والطباعة:** `.html` و`.md`، قابل للطباعة ويحمل نفس الهوية البصرية.
3. **ملف الرصد البحري (`MARITIME`):**
   * **الأقسام:** نفس الهيكل، ويركز جدول الرصد على أحداث تصنيفي **`بحري`** و**`إغاثي/تجاري`** (بحد أقصى **15** حدثاً) مع شارة زرقاء (`#0284c7`) وجدول السفن.
   * **الصيغ والطباعة:** `.html` و`.md`، قابل للطباعة ويحمل الهوية البصرية كاملة.

---

### ب) ملفات الخرائط والبيانات الجغرافية (Geospatial Outputs)
* **ملفات `KML` (`generate_google_earth_kml` في `app.py`):**
  * **النقاط المضمنة:**
    * في تبويب **الخريطة GIS**: جميع الأحداث المحمّلة (حتى **250** حدثاً) + السفن (اختيارياً، حالياً **13–18** سفينة) + الموانئ الاستراتيجية (**25** موقعاً من `STRATEGIC_PORTS`).
    * في تبويب **الرادار البحري AIS**: السفن + الـ **25** موقعاً استراتيجياً (بدون أحداث إخبارية).
  * **الطبقات (Folders):** 3 مجلدات داخل الـ KML (`الأحداث والوقائع الاستخباراتية` بأيقونات حمراء/صفراء/خضراء، `القطع البحرية والأسطول AIS`، `الموانئ والممرات الاستراتيجية`).
  * **التوافق:** يفتح مباشرة في **Google Earth Pro** و**QGIS**، ويدعم روابط `Google Earth 3D` و`Google Maps`.
  * **الإحداثيات:** إحداثيات الأحداث والموانئ حقيقية (`geo_gazetteer` + `STRATEGIC_PORTS`)، بينما إحداثيات السفن **محاكاة** (ما لم يُفعّل `AISSTREAM_API_KEY`).
* **ملفات `GeoJSON` وصور الخرائط الثابتة (`Static Maps PNG`):** **غير موجودة** في الكود.

---

### ج) ملفات تحليل الشبكات (Network Analysis Outputs)
* **ملفات `GEXF` (`EntityNetworkGraph.export_gexf()` في `03_processing/network_analysis/network_graph.py`):**
  * **العقد والروابط:** تُبنى ديناميكياً من أحدث **80** حدثاً (`db.get_events(limit=80)`). في كل حدث تُنشأ 3 عقد كحد أقصى (`EV_<id>`, `LOC_<location>`, `CAT_<category>`) ورابطان غير موجهين (`وقع في` بوزن `1.5`، و`يصنف كـ` بوزن `1.0`). على البيانات الحالية (80 حدثاً) ينتج نحو **80–120 عقدة** و**160 رابطاً**.
  * **الأنواع المضمنة:** `EVENT`، `LOCATION`، `CATEGORY` (ملاحظة: الكيانات الفردية مثل الأشخاص والأسلحة من `NLPProcessor` غير مدمجة في الرسم الشبكي حالياً).
  * **التوافق:** يفتح مباشرة في **Gephi** بصيغة `GEXF 1.2draft`.
* **ملفات `GraphML` أو `JSON` شبكية:** **غير موجودة**.

---

### د) الجداول والبيانات المنظمة (Structured Data Outputs)
* **ملف `CSV` للأحداث (`osint_events_*.csv`):**
  * **الأعمدة:** جميع أعمدة جدول `osint_events` (`id, title, raw_content, cleaned_content, source_id, published_at, captured_at, event_category, sentiment_score, sentiment_label, urgency_level, fact_check_status, latitude, longitude, location_name, raw_data_url, raw_hash, relevance_score, relevance_reason, trust_score, source_label`).
  * **الترميز:** `utf-8-sig` (يحتوي على `BOM`) — يفتح في **Microsoft Excel** باللغة العربية بدون أي تشويه.
* **ملف `CSV` للأسطول البحري (`ais_vessels_*.csv`):**
  * **الأعمدة (9):** `mode_badge, mmsi, vessel_name, vessel_type, flag_country, destination, speed_knots, nav_status, last_signal_at`.
  * **الترميز:** `utf-8-sig` — متوافق تماماً مع Excel.
* **ملف `Excel (.xlsx)` الأصلي:** **غير موجود** (الاعتماد على `CSV utf-8-sig`).
* **ملف `JSON` برمجي (`cloud_seed.json`):** يضم مفاتيح `events`, `vessels`, `rejected` ويُستخدم للبذر السحابي التلقائي فقط.

---

### هـ) مخرجات الواجهة (UI Outputs)
* **بطاقات `KPIs` الأربع + شريط كود الإنذار التكتيكي:** تفاعلية تلقائياً مع البيانات، غير قابلة للتصدير كصورة منفردة، ولا تُضمّن تلقائياً كـ HTML داخل تقارير `ReportGenerator` (التقرير يعيد حساب الأرقام نصياً).
* **الرسوم البيانية التفاعلية (`Plotly`):**
  * `fig_pie`: توزيع الأحداث حسب التصنيف (`event_category`).
  * `fig_bar`: توزيع مؤشر التوتر والأهمية (`urgency_level`).
  * تفاعلية بالكامل، **ويمكن تصديرها كصورة `PNG`** عبر أيقونة الكاميرا المدمجة في شريط Plotly العلوي، لكنها **غير مضمّنة داخل تقارير SITREP/FLASH/MARITIME**.
* **خريطة Google Earth التفاعلية (`Leaflet`):** تفاعلية (4 طبقات، `Fly-To`، بطاقات منبثقة)، لا يوجد زر تصدير كصورة مباشرة.
* **سجل الأحداث وجدول المصادر والمرفوضات وبطاقات NLP والشبكة:** تفاعلية ومفلترة، غير قابلة للتصدير كصورة.

---

### و) مخرجات أخرى (سجلات / إشعارات / أخطاء)
* **إشعارات الواجهة الحية:** `st.success` / `st.info` / `st.warning` / `st.error` (فورية ومؤقتة في الجلسة).
* **سجلات الطرفية (Console Logs):** مطبوعات `pipeline_runner.py` و`news_api.py` (تظهر في سجل Streamlit Cloud Runtime Logs فقط).
* **ملف سجل أخطاء مستقل (`error.log`) أو نظام إشعارات بريدية/تليجرام:** **غير موجود** في الكود.

---

## القسم 3: أين تذهب المخرجات؟ (Where Do Outputs Go?)

1. **التخزين المحلي (`Local Storage`):**
   * تُحفظ تقارير `SITREP / FLASH / MARITIME` تلقائياً في المجلد: `06_presentation/reporting/generated_reports/`.
   * نمط التسمية يحتوي التاريخ والوقت بدقة الثانية: `report_<type>_YYYYMMDD_HHMMSS.html` و`.md`.
   * **التراكم:** لا يوجد تنظيف تلقائي للملفات القديمة؛ الملفات تتراكم باستمرار (يوجد حالياً 72+ ملفاً متراكماً من التشغيلات السابقة).
   * ملفات `KML` و`GEXF` و`CSV` **لا تُحفظ على القرص**، بل تُولّد في الذاكرة للتنزيل المباشر فقط.
2. **التخزين السحابي (`Cloud Storage`):**
   * المخرجات الملفية (`generated_reports/*.html, *.md`) **لا تُرفع إلى Turso**، بل تُكتب في نظام الملفات المؤقت لحاوية `Streamlit Community Cloud`، وبالتالي **تُفقد عند إعادة تشغيل الحاوية (Container Reboot/Sleep)**، بينما تبقى البيانات الخام (`osint_events`, `rejected_news`, `ais_vessels`) في قاعدة البيانات (Turso إذا فُعّل، أو SQLite المؤقت + `cloud_seed.json`).
   * لا يمكن الوصول إلى ملفات `generated_reports` من خارج التطبيق عبر رابط URL مباشر.
3. **التحميل المباشر (`Direct Download`):**
   * جميع التقارير (`.html`, `.md`) وملفات (`KML`, `GEXF`, `CSV`) تُحمّل مباشرة من المتصفح عبر `st.download_button`.
   * **يعمل على الجوال بالكامل** (تُنزّل الملفات إلى مجلد `Downloads` في iOS/Android).
4. **الطباعة (`Printing`):**
   * تقارير `.html` فقط مصممة للطباعة الرسمية عبر قواعد `@media print` الموجودة في [report_generator.py](06_presentation/reporting/report_generator.py#L471-L487) (تُحوّل الخلفية للأبيض والخط للأسود مع تثبيت الهيدر).
   * يمكن حفظها كـ **PDF رسمي** عبر فتح ملف `.html` في المتصفح ثم `Ctrl+P -> Save as PDF`.
5. **المشاركة (`Sharing`):**
   * لا يوجد رابط مشاركة دائم لتقرير محدد، ولا يوجد `REST API` خارجي لتحميل المخرجات، ولا يوجد تكامل بريد إلكتروني (`SMTP`) في الكود.

---

## القسم 4: الفائدة الاستخباراتية لكل مخرج (Intelligence Value)

| المخرج | الجمهور المستهدف | القرار المدعوم | القيمة المضافة | القيود الحالية | التوصية |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`SITREP` (`HTML/MD`)** | صانع القرار، مدير العمليات | تقييم الوضع العام وتوجيه الموارد | يجمع مؤشرات الأداء والأحداث والسفن في وثيقة واحدة ممهورة ببصمة `SHA-256` | يتطلب تشغيلاً يدوياً؛ الاستنتاجات نصية ثابتة نسبياً ولا تضم الرسوم البيانية | إضافة توليد دوري تلقائي وتضمين استنتاجات ديناميكية ورسوم SVG |
| **`FLASH` (`HTML/MD`)** | ضباط الإنذار المبكر، فرق الاستجابة | إصدار تحذير فوري أو رفع الجاهزية | يفلتر تلقائياً أحداث الأولوية `قصوى` فقط دون ضجيج روتيني | لا يرسل تنبيهاً خارجياً (Telegram/Email)؛ يدوي فقط | ربطه بتنبيه Webhook/Telegram عند رصد حدث حرج |
| **`MARITIME` (`HTML/MD`)** | شركات الشحن، المحلل البحري | تقييم مخاطر الإبحار في باب المندب | يدمج الحوادث البحرية والإغاثية مع جدول أسطول AIS | جدول السفن يعتمد على المحاكاة ما لم يُضف مفتاح `AISSTREAM_API_KEY` | تفعيل مفتاح `AISStream` وإضافة إحصائية السفن القريبة من مناطق الخطر |
| **`KML` (GIS & AIS)** | محللو GIS، باحثو المصادر المفتوحة | تتبع التمركز الجغرافي ومسار السفن | يعرض الطبقات على Google Earth Pro بـ 25 ميناءً وجزيرة وميزة 3D | غير متوافق تلقائياً مع البث التلقائي (ملف ساكن لحظة التحميل) | إضافة خط زمني (`TimeSpan`) داخل KML لتتبع تطور الأحداث زمنياً |
| **`GEXF` (Network)** | باحثو الشبكات، محللو الترابط | كشف البؤر الجغرافية والتصنيفية المهيمنة | يفتح مباشرة في Gephi لقياس المركزية | يقتصر على 3 أنواع عقد (`EVENT, LOCATION, CATEGORY`) دون الأشخاص والأسلحة | دمج كيانات `NLPProcessor` (الأشخاص، المنظمات، الأسلحة) داخل الشبكة |
| **`CSV` (`Events/Vessels`)** | الباحثون، الصحفيون، المنظمات الإنسانية | تحليل إحصائي مخصص وتدقيق البيانات | ترميز `utf-8-sig` سليم لـ Excel مع كافة حقول الثقة والصلة | لا يصدّر سجل المرفوضات `rejected_news` أو جدول حالة المصادر | إضافة زر تصدير CSV لسجل المرفوضات وتقرير دقة الفلتر |

---

## القسم 5: تقييم الجودة (Quality Assessment — مقياس 1 إلى 5)

| المخرج | الاكتمال | الدقة | الوضوح | الاحترافية | التوافق | ملاحظات التقييم الصريحة |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **تقارير `SITREP / FLASH / MARITIME` (`HTML`)** | 4/5 | 4/5 | 5/5 | 5/5 | 4/5 | تصميم بصري ممتاز متوافق مع `@media print` والهوية المدمجة، لكن الاستنتاجات ثابتة وتنقصه الرسوم البيانية وصيغة PDF المباشرة. |
| **تقارير `Markdown (.md)`** | 4/5 | 4/5 | 4/5 | 4/5 | 5/5 | مهيكلة ونظيفة ومثالية للمشاركة النصية والأرشفة الخفيفة. |
| **ملفات `Google Earth (.KML)`** | 5/5 | 4/5 | 5/5 | 5/5 | 5/5 | متكاملة بـ 3 مجلدات وأيقونات مرمزة لونياً وروابط 3D؛ دقة السفن تعتمد على تفعيل مفتاح AIS الحي. |
| **ملف `Gephi (.GEXF)`** | 3/5 | 4/5 | 4/5 | 4/5 | 5/5 | معيار XML سليم ويفتح في Gephi فوراً، لكنه محدود لعدم تضمين عقد المنظمات والأسلحة والشخصيات. |
| **ملفات `CSV (utf-8-sig)`** | 5/5 | 5/5 | 4/5 | 4/5 | 5/5 | ممتازة لـ Excel والباحثين وتحتوي جميع الحقول الوصفية والزمنية. |
| **خرائط ورسوم الواجهة (`Leaflet + Plotly`)** | 5/5 | 4/5 | 5/5 | 5/5 | 5/5 | متجاوبة بعد التحديث الأخير على الكمبيوتر والتابلت والجوال وتدعم 4 طبقات Google Earth. |

---

## القسم 6: الفجوات والتوصيات (Gaps & Recommendations)

1. **مخرجات مفقودة يُوصى بإضافتها:**
   * **ملف `PDF` جاهز للتنزيل المباشر** (عبر `weasyprint` أو `xhtml2pdf` أو `playwright`) بجانب `HTML` لأن كثيراً من الجهات تفضّل مشاركة PDF واحد مغلق.
   * **خريطة حرارية زمنية / مكانية (Heatmap & Time-Series Chart)** توضح تصاعد الأحداث يومياً/أسبوعياً.
   * **تصدير `GeoJSON` قياسي** لدعم مطوري الويب و`QGIS` بشكل مباشر بجانب `KML`.
   * **تصدير `CSV` لسجل الأخبار المرفوضة (`rejected_news`)** لأغراض التدقيق الدوري.
2. **مخرجات تحتاج تحسيناً:**
   * **شبكة العلاقات (`GEXF`):** توسيع `EntityNetworkGraph.build_from_events` لربط الأحداث بالمنظمات والأشخاص والأسلحة المستخرجة من `NLPProcessor` بدلاً من الاقتصار على الموقع والتصنيف.
   * **تقارير `ReportGenerator`:** جعل قسم **"الاستنتاجات الاستخباراتية"** ديناميكياً محسوباً من أعلى المدن تكراراً وأخطر الكلمات المفتاحية ومعدل التوتر الفعلي بدلاً من الجمل الثابتة.
3. **مخرجات يمكن دمجها:**
   * وجود جدولين منفصلين للموانئ سابقاً تم حله بدمج `STRATEGIC_PORTS` في `ais_tracker.py`. يمكن أيضاً توحيد دالة تصدير `CSV` في دالة مساعدة مشتركة وتجميع أزرار التصدير (`KML`, `CSV`, `GEXF`) في لوحة **"مركز التصدير الموحد"**.
4. **مخرجات يجب أتمتتها:**
   * أتمتة توليد تقرير `SITREP` يومياً أو عند انتهاء كل دورة استخباراتية وحفظ نسخه النصية (`md_content`) داخل جدول جديد في قاعدة بيانات **Turso** (`generated_reports_archive`) حتى لا تُفقد عند إعادة تشغيل حاوية Streamlit Cloud.
5. **توصيات عامة لمنظومة المخرجات:**
   * إضافة سياسة تدوير وتنظيف في `06_presentation/reporting/generated_reports/` (الاحتفاظ بآخر 30 تقريراً محلياً فقط لمنع تضخم الحجم بسبب تضمين `Base64` الذي يرفع حجم كل ملف HTML إلى ~1 ميجابايت).
   * إضافة إشعار تلقائي (Webhook / Telegram Bot اختياري) لبرقية `FLASH` فور رصد أي حدث بتصنيف `قصوى` ومؤشر تهديد `>= 80`.
