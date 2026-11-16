# 🧠 التقرير التقني المفصل لآلية تحليل المحتوى | Platform OX Content Analysis Audit (`CONTENT_ANALYSIS_AUDIT.md`)

**تاريخ التدقيق:** 2026-11-16  
**نطاق التدقيق:** الكود الفعلي في `03_processing/nlp_engine/nlp_processor.py`، `03_processing/sentiment/sentiment_analyzer.py`، `03_processing/filters/yemen_relevance_filter.py`، `03_processing/spatial_gis/spatial_analyzer.py`، `04_orchestration/pipeline_runner.py`، `02_storage/database.py`، و`06_presentation/reporting/report_generator.py`.  
**منهجية التوثيق:** استخراج حرفي ودقيق من الشيفرة المصدرية الفعلية دون أي افتراض أو اختراع.

---

## القسم 1: ما هي المعلومات التي يستخرجها المحلل من النص؟

| # | المعلومة المستخرجة | الملف المصدر | الدالة المسؤولة | الطريقة / الآلية الفعلية | مثال تطبيقي |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | **النص المنظف والموحّد (`cleaned_content`)** | `03_processing/nlp_engine/nlp_processor.py` | `NLPProcessor.clean_arabic_text(text)` | تعابير نمطية (`RegEx`): حذف الروابط، حذف التشكيل والتطويل، توحيد الألف (`إأآ ← ا`)، توحيد التاء المربوطة (`ة ← ه`) والألف المقصورة (`ى ← ي`)، وإزالة الرموز غير القياسية. | `"أعلنتْ UKMTO في عدنً..."` ← `"اعلنت UKMTO في عدن..."` |
| **2** | **الكيانات المسماة (`LOCATION, ORGANIZATION, VESSEL, WEAPON_SYSTEM`)** | `03_processing/nlp_engine/nlp_processor.py` | `NLPProcessor.extract_entities(text)` | مطابقة 4 قواميس (`47` موقعاً، `35` منظمة، `18` سفينة، `12` سلاحاً) عبر مطابقة الكلمة الكاملة `match_whole_term` مع إسناد ثقة ثابتة (`0.95` موقع، `0.94` سلاح، `0.92` منظمة، `0.90` سفينة). | `"هيئة UKMTO ترصد ناقلة نفط قبالة الحديدة بصاروخ باليستي"` ← `UKMTO (ORG)`, `ناقلة نفط (VESSEL)`, `الحديدة (LOC)`, `صاروخ باليستي (WEAPON)` |
| **3** | **التصنيف الرباعي (`event_category`)** | `03_processing/sentiment/sentiment_analyzer.py` | `_raw_classify_category(title, summary, text)` و`classify_event(...)` | مطابقة الكلمة الكاملة (`match_whole_term`) وفق أولوية تسلسلية صارمة: `بحري` (`27` مصطلحاً مع استبعاد "القناة الناقلة") ← `إغاثي/تجاري` (`17` مصطلحاً) ← `أمني/عسكري` (`24` مصطلحاً) ← `سياسي/عام` (افتراضي). | `"وصول شحنة قمح إلى ميناء الصليف"` ← `"بحري"` (لأولوية `ميناء` قبل `قمح`)؛ `"توزيع مساعدات غذائية"` ← `"إغاثي/تجاري"` |
| **4** | **درجة الصلة اليمنية (`relevance_score` 0–100)** | `03_processing/filters/yemen_relevance_filter.py` | `is_yemen_relevant(title, summary)` | لقسم `سياسي/عام` فقط: فحص الاستبعاد الصريح والناعم (`is_soft_excluded`)، ثم حساب النقاط: كيان يمني في العنوان (`+50`) + في الملخص (`+30`) + كلمة سياق (`+20`). يُقبل إذا كان `>= 40`. | `"اجتماع في صنعاء لبحث التهدئة"` ← `50 (صنعاء) + 20 (تهدئة/سياق) = 70` (مقبول) |
| **5** | **المشاعر والقطبية (`sentiment_score` & `sentiment_label`)** | `03_processing/sentiment/sentiment_analyzer.py` | `SentimentAnalyzer.analyze_sentiment(text)` | عدّ الكلمات السلبية (`26` كلمة) والإيجابية (`20` كلمة) وحساب المعادلة: `(pos - neg) / (pos + neg)`. إذا كان `< -0.2` فـ `سلبي (توتر مرتفع)`، وإذا `> 0.2` فـ `إيجابي`، وإلا `محايد / متوازن`. | `"وصول آمن وتفريغ قمح وإغاثة"` (`pos=3, neg=0`) ← `score = 1.0`, `إيجابي` |
| **6** | **مؤشر التهديد (`threat_index` 10–95) ومستوى التوتر (`tension_level`)** | `03_processing/sentiment/sentiment_analyzer.py` | `SentimentAnalyzer.analyze_sentiment(text)` | قواعد حسابية: في النبرة السلبية `min(95, 40 + neg_count * 15)` وتوتر `قصوى` إذا `neg_count >= 3`؛ في الإيجابية `max(10, 30 - pos_count * 5)`؛ في المحايدة `35 + neg_count * 8` (أو `20` عند غياب الكلمات). | `"هجوم واستهداف وانفجار صاروخ"` (`neg=4`) ← `threat_index = 95`, `tension_level = قصوى` |
| **7** | **مستوى الأهمية (`urgency_level`: قصوى/متوسطة/روتينية)** | `04_orchestration/pipeline_runner.py` (و`news_api.py`) | `run_full_osint_cycle()` | `قصوى` إذا كان `tension_level == "قصوى"` أو وردت إحدى الكلمات (`صاروخ، استهداف، هجوم، غرق`)؛ `متوسطة` إذا وُجدت كيانات أو `tension_level == "متوسط"`؛ وإلا `روتينية`. | `"استهداف سفينة في البحر الأحمر"` ← `"قصوى"` |
| **8** | **مؤشر احتمالية الشائعات (`rumor_risk`)** | `03_processing/sentiment/sentiment_analyzer.py` | `SentimentAnalyzer.analyze_sentiment(text)` | مطابقة قائمة `rumor_indicators` (`8` عبارات مثل `مصادر غير مؤكدة، أنباء متضاربة، يقال`): `>= 2` ← `مرتفع`، `1` ← `متوسط`، `0` ← `منخفض`. | `"أنباء متضاربة عن مصادر غير مؤكدة"` ← `rumor_risk = مرتفع` |
| **9** | **حالة التحقق والتثليث (`fact_check_status`)** | `04_orchestration/pipeline_runner.py` (و`news_api.py`) | `run_full_osint_cycle()` / `NewsAggregator.save_news()` | في `pipeline_runner`: `مؤكد برقيات رسمية` إذا وردت (`UKMTO، رسمي، أسبيدس`)، `قيد التثليث الميداني` إذا `len(entities) >= 2`، وإلا `رصد أولي مفتوح`. وفي `news_api.save_news`: `مؤكد (مصدر يمني مباشر)` إذا `trust_score >= 90`. | `"إشعار رسمي من UKMTO"` ← `"مؤكد برقيات رسمية"` |
| **10** | **الموقع الجغرافي والإحداثيات (`location_name, lat, lon`)** | `yemen_relevance_filter.py` + `spatial_analyzer.py` | `extract_yemen_location()` ثم `SpatialGISAnalyzer.resolve_location()` | استخراج أول موقع من `ORDERED_YEMEN_LOCATIONS` (`47` موقعاً) مع التحقق من السياق للمواقع المشتركة، ثم تحويله لإحداثيات `Lat/Lon` عبر `geo_gazetteer` (`47` إحداثية؛ الافتراضي صنعاء `15.3694, 44.1910`). | `"انفجار قرب ميناء الحديدة"` ← `ميناء الحديدة` (`14.7978, 42.9496`) |
| **11** | **المسافة عن باب المندب والبؤر الساخنة** | `03_processing/spatial_gis/spatial_analyzer.py` | `haversine_distance_km()`, `haversine_distance_nautical_miles()`, `identify_hotspots()` | معادلة `Haversine` الجيوديسية (`R = 6371 كم` ومعامل `0.539957` للميل البحري)، وتجميع الأحداث ضمن نصف قطر `60 كم`. *(تعمل الدالة في `spatial_analyzer.py` ومختبرة برمجياً، لكنها لا تُحفظ كعمود مستقل في `osint_events`)*. | المسافة من ميناء الحديدة إلى باب المندب = `249.6 كم` (`134.77 ميل بحري`) |
| **12** | **التلخيص النصي الاستخلاصي (`summarize_text`)** | `03_processing/nlp_engine/nlp_processor.py` | `NLPProcessor.summarize_text(text, max_sentences=2)` | تقسيم النص عند علامات الترقيم والأسطر وأخذ أول جملتين أطول من `15` حرفاً. *(دالة متاحة في NLP لكن لا تُستدعى تلقائياً داخل `pipeline_runner`)*. | يأخذ أول جملتين من متن الخبر |
| **13** | **الكلمات المفتاحية المستخرجة / التلخيص الموضوعي** | — | — | **غير موجود** كدالة استخراج كلمات مفتاحية مستقلة (TF-IDF / KeyBERT)؛ ما يُستخرج فعلياً هو الكيانات في القواميس الأربعة أعلاه، بينما يحسب `ReportGenerator.generate_filter_performance_report()` أعلى `10` كلمات تكراراً في العناوين عبر `Counter`. | في تقرير الفلترة فقط: `('الأحمر', 91), ('عدن', 88)...` |

---

## القسم 2: كيف تتجمع هذه المعلومات لتشكيل التقرير؟

### 1. مسار النص من لحظة سحبه حتى ظهوره في التقرير (Pipeline Flow)
1. **السحب المتوازي (`01_acquisition/apis/news_api.py`):** يسحب `NewsAggregator.fetch_live_news()` الخلاصات من `19` مصدراً عبر `ThreadPoolExecutor`، ويزيل وسوم HTML والروابط عبر `_clean_html_and_urls`، ويحسب بصمة `SHA-256` للعنوان المطبّع عبر `compute_news_hash` لمنع التكرار.
2. **التصنيف والفلترة (`sentiment_analyzer.py` + `yemen_relevance_filter.py`):**
   * تُصنّف كل مادة إلى أحد الأقسام الأربعة (`بحري`، `إغاثي/تجاري`، `أمني/عسكري`، `سياسي/عام`).
   * إذا صُنّف `سياسي/عام` يمر عبر `is_yemen_relevant()` (المرفوض يُحفظ في `rejected_news` ويتوقف مساره).
   * إذا صُنّف `بحري` أو `أمني/عسكري` من مصدر دولي (`USNI, Naval News, gCaptain, Splash247, Maritime Executive`) يمر عبر `is_maritime_region_relevant()` في `news_api.save_news()`.
3. **التنظيف واستخراج الكيانات (`nlp_processor.py`):** تنظيف النص (`clean_arabic_text`) واستخراج الكيانات (`extract_entities`).
4. **تحليل المشاعر والتهديد والشائعات (`sentiment_analyzer.py`):** حساب `score, label, tension_level, threat_index, rumor_risk`.
5. **التحديد الجغرافي (`spatial_analyzer.py`):** تحديد اسم الموقع (`extract_yemen_location`) وتحويله إلى `(latitude, longitude)` عبر `resolve_location`.
6. **تحديد الأهمية وحالة التحقق والإنذار (`pipeline_runner.py`):** إسناد `urgency_level` و`fact_check_status`، وإطلاق `send_alert()` تلقائياً لـ Telegram/Webhook إذا كان `urgency == "قصوى"` و`threat_index >= 80`.
7. **الحفظ في قاعدة البيانات (`02_storage/database.py`):** إدراج السجل في جدول `osint_events` داخل Turso السحابي أو SQLite المحلي.
8. **توليد التقرير والأرشفة (`06_presentation/reporting/report_generator.py`):** عند طلب `SITREP` أو `FLASH` أو `MARITIME`، يسترجع `ReportGenerator` المؤشرات والأحداث والسفن ويعيد استخراج الكيانات لحظياً عبر `_build_full_snapshots` ثم يصدر الملفات (`HTML, MD, PDF, DOCX`) ويحفظها بكامل النصوص والكيانات في `generated_reports_archive`.

### 2. كيف يتم تجميع الأحداث في التقرير؟
في `ReportGenerator.generate_situation_report(report_type)` ([report_generator.py](06_presentation/reporting/report_generator.py#L77-L111)):
* يجلب أحدث **25** حدثاً من قاعدة البيانات مرتبة تنازلياً حسب `id` (`SELECT * FROM osint_events ORDER BY id DESC LIMIT 25`).
* ثم يطبق التصفية والحد الأقصى حسب نوع التقرير:
  * **`SITREP`:** يأخذ أحدث **15** حدثاً كما هي (`events[:15]`).
  * **`FLASH`:** يفلتر الأحداث التي `urgency_level == "قصوى"` وبحد أقصى **10** أحداث (وإذا لم توجد أحداث قصوى، يتراجع تلقائياً لأحدث **5** أحداث).
  * **`MARITIME`:** يفلتر الأحداث التي `event_category in ["بحري", "إغاثي/تجاري"]` وبحد أقصى **15** حدثاً (وإذا لم توجد، يتراجع لأحدث **10** أحداث).

### 3. كيف يتم حساب المؤشرات التكتيكية (`KPIs`)؟
تُحسب مباشرة باستعلامات SQL في `OSINTDatabase.get_kpis()` ([database.py](02_storage/database.py#L499-L525)):
* **`total_events`:** `SELECT COUNT(*) FROM osint_events`.
* **`critical_events`:** `SELECT COUNT(*) FROM osint_events WHERE urgency_level = 'قصوى'`.
* **`verified_events`:** `SELECT COUNT(*) FROM osint_events WHERE fact_check_status LIKE 'مؤكد%'`.
* **`active_vessels`:** `SELECT COUNT(*) FROM ais_vessels`.
* **`verification_rate`:** `round((verified_events / total_events * 100), 1)` (أو `0` إذا كانت القاعدة فارغة).

### 4. كيف يتم توليد "الاستنتاجات والتوصيات" في التقرير؟
* **الإجابة الصريحة:** في الكود الحالي (`report_generator.py` الأسطر `165–171` و`598–608`)، **الاستنتاجات والتوصيات هي نصوص قالبية ثابتة (Static Template Text)** وليست مولدة ديناميكياً من نتائج التحليل اللحظي!
* فهي تعرض 3 نقاط ثابتة حول استمرار مواكبة القوافل في باب المندب، والتثليث مع UKMTO، والتوصية بالمسح كل 15 دقيقة ومراقبة ناقلات الطاقة.

---

## القسم 3: مكونات التقرير النهائي (`SITREP` كمثال)

يتكون تقرير `SITREP` في [06_presentation/reporting/report_generator.py](06_presentation/reporting/report_generator.py) من **6 أقسام رئيسية** (في صيغة `HTML` و`MD`، وبنفس البنية في `PDF` و`DOCX`):

| # | القسم | البيانات المعروضة ومصدرها | التنسيق البصري (`HTML/CSS`) |
| :---: | :--- | :--- | :--- |
| **1** | **الترويسة الرسمية (`Header Banner`)** | عنوان التقرير، رقم الوثيقة (`OX-REP-YYYYMMDD-HHMMSS`)، توقيت الإصدار، ودرجة التصنيف (`رصد علني موثق - مركز العمليات`) من متغيرات الدالة. | شريط علوي ثابت (`position: fixed; height: 120px`) بخلفية `header_background.png` وشعار `icon.svg` مدمجين بـ `Base64`، وشارة تصنيف خضراء (`#10b981`)، مع دعم `@media print`. |
| **2** | **المؤشرات التكتيكية (`Executive KPIs`)** | الأرقام الأربعة الحية من `db.get_kpis()` (`total_events`, `critical_events`, `active_vessels`, `verification_rate`). | شبكة متجاوبة (`kpi-grid` بنظام CSS Grid) تضم 4 بطاقات زجاجية داكنة بإطار أزرق سماوي (`#38bdf8`). |
| **3** | **جدول الرصد الميداني (`Events Table`)** | أحدث 15 حدثاً من `osint_events`: المعرف، العنوان (مقصوص عند `75` حرفاً في HTML/MD، وكاملاً مع `raw_content` و`raw_data_url` في `Word` والأرشيف)، التصنيف، مستوى التوتر، الموقع، وحالة التحقق. | جدول HTML متجاوب (`overflow-x: auto`) مع شارات ملونة لمستوى التوتر (`قصوى` أحمر، `متوسطة` برتقالي، `روتينية` أخضر). |
| **4** | **وضع الملاحة والسفن (`AIS Table`)** | أحدث 10 سفن من `ais_vessels` (حتى 15 في Word/الأرشيف): `MMSI`، اسم السفينة، النوع، العلم، الإحداثيات، الوجهة، السرعة، والحالة الملاحية. | جدول HTML منسق بأعمدة واضحة وحقول إحداثيات ثنائية العشرية. |
| **5** | **الاستنتاجات والتوصيات** | 3 بنود نصية ثابتة (أمن الملاحة، التثليث، التوصيات العملياتية). | قائمة مرقمة داخل حاوية زجاجية مظللة (`report-container`). |
| **6** | **التذييل وبصمة التحقق (`Footer`)** | توقيع مركز العمليات + بصمة التجزئة الرقمية `SHA-256` لمحتوى التقرير (أول 24 حرفاً في HTML وأول 32 حرفاً في MD، وكاملة في الأرشيف). | شريط سفلي غير ثابت (`non-fixed-footer-banner`, `120px`) بخلفية الهوية البصرية المدمجة `Base64`. |

---

## القسم 4: تقييم ذاتي صريح (Self-Assessment)

### 1. أقوى 3 معلومات يستخرجها المحلل
1. **الكيانات المسماة بحدود الكلمة الكاملة (`extract_entities`):** استخدام `match_whole_term` يمنع تماماً الأخطاء الشائعة في العربية (مثل مطابقة `عدن` داخل `معدن` أو `تعز` داخل `تعزيز` أو `إب` داخل `إبراهيم`).
2. **التصنيف الرباعي وفلتر الصلة اليمنية (`classify_event` + `is_yemen_relevant`):** يفصل بدقة الأخبار البحرية والأمنية والإغاثية عن السياسية العامة، ويمنع تسرب الأخبار الفنية والرياضية والتقنية العالمية مع دعم الاستبعاد الناعم (`is_soft_excluded`) والنطاق البحري الإقليمي (`is_maritime_region_relevant`).
3. **الإسقاط الجغرافي الحقيقي (`extract_yemen_location` + `resolve_location`):** يربط 47 موقعاً وميناءً يمنياً بإحداثياتها الحقيقية دون إسناد موقع افتراضي خاطئ مثل "البحر الأحمر" إلا بوجود سياق معتبر.

### 2. أضعف 3 معلومات (الأقل دقة أو الأكثر عرضة للخطأ)
1. **تحليل المشاعر ومؤشر التهديد (`analyze_sentiment`):**
   * **الضعف:** يبحث داخل النص بالاحتواء الجزئي المباشر (`if word in text`) بدون `match_whole_term` وبدون تطبيع الهمزات! مثلاً كلمة `"أزمة"` قد تطابق كلمة أطول أو تفشل مع `"ازمة"` (همزة وصل)، وكلمة `"خطر"` قد تطابق `"خاطر"` أو `"أخطر"`، كما لا يفهم النفي (مثل `"لا يوجد أي هجوم"` يُحسب ككلمة سلبية `هجوم`!).
2. **حالة التحقق والتثليث (`fact_check_status`):**
   * **الضعف:** قاعدة بسيطة جداً (`"رسمي" in full_text` أو `len(entities) >= 2` في `pipeline_runner.py`)؛ أي خبر يحتوي كلمة `"رسمي"` (حتى لو كان نفياً أو من مدونة غير موثوقة) يُوسم بـ `"مؤكد برقيات رسمية"`!
3. **"الاستنتاجات والتوصيات" في التقرير (`ReportGenerator`):**
   * **الضعف:** نصوص ثابتة تماماً لا تتغير بتغير البيانات، ما يجعل قراءتها متكررة بين تقرير وآخر.

### 3. معلومات موجودة في النص لا يستخرجها المحلل حالياً (فجوات التحليل)
* **أسماء الأشخاص والقيادات داخل `NLPProcessor`:** `yemen_relevance_filter.py` يحتوي `persons_and_leaders`، لكن `NLPProcessor` لا يملك قاموس `PERSON`، لذا لا تظهر أسماء القيادات ككيانات مستخرجة في `extracted_entities` أو شبكة `Gephi`!
* **توقيت الحدث الفعلي داخل المتن والأرقام الكمية:** مثل عدد القتلى/الجرحى، حمولة السفينة بالطن، اسم السفينة المحدد (إذا لم يكن من الـ 18 في القاموس)، ونوع الشحنة.
* **النفي والسياق اللغوي (Negation & Coreference):** التمييز بين `"إحباط هجوم"` / `"نفي استهداف"` وبين `"وقوع هجوم"`.
* **ملخص الخبر وحساب المسافة عن باب المندب:** الدالتان `summarize_text` و`haversine_distance_km` موجودتان في الكود لكنهما **غير موصولتين** لتخزين ملخص أو مسافة في جدول `osint_events`.

### 4. توصيات محددة لتحسين دقة التحليل
1. **ترقية `SentimentAnalyzer.analyze_sentiment`:** استبدال `if word in text` بـ `match_whole_term(text, word)` مع معالجة عبارات النفي الشائعة (`لا صحة، نفي، فشل، إحباط، دون إصابات`) لتخفيض `threat_index` عند النفي أو الإحباط.
2. **إضافة قاموس `PERSON` في `NLPProcessor`:** استيراد قائمة `persons_and_leaders` من `yemen_relevance_filter.py` إلى `NLPProcessor.extract_entities()` وربطها بشبكة `EntityNetworkGraph`.
3. **جعل الاستنتاجات في `ReportGenerator` ديناميكية:** حساب أعلى 3 مواقع تكراراً، أعلى 3 كيانات/أسلحة مرصودة، ومتوسط مؤشر التهديد، وصياغة فقرة استنتاجات تتغير تلقائياً مع كل تقرير.
4. **ربط `fact_check_status` بدرجة ثقة المصدر (`trust_score`) والتثليث الفعلي:** الاعتماد على `trust_score >= 90` أو تكرار الحدث في مصدرين مختلفين بدلاً من وجود كلمة `"رسمي"` في النص.
5. **تفعيل استخراج الكلمات المفتاحية والمسافة عن باب المندب:** حفظ المسافة بالكيلومتر والميل البحري وأهم الكيانات في حقول وصفية تُعرض مباشرة في بطاقة الحدث والتقرير.
