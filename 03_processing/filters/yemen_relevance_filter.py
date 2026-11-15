import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class FilterResult:
    """نتيجة فحص الصلة اليمنية للخبر"""
    accepted: bool
    reason: Optional[str]
    score: int
    matched_entities: List[str] = field(default_factory=list)
    matched_location: Optional[str] = None

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accepted": self.accepted,
            "reason": self.reason,
            "score": self.score,
            "matched_entities": self.matched_entities,
            "matched_location": self.matched_location,
        }


# ==============================================================================
# أ) قائمة Yemen Core Entities (كيانات يمنية جوهرية)
# ==============================================================================
YEMEN_CORE_ENTITIES: Dict[str, List[str]] = {
    "national_identifiers": [
        "اليمن", "الجمهورية اليمنية", "يمني", "يمنية", "اليمني", "اليمنية",
        "يمنيين", "يمنيون", "اليمنيين", "اليمنيات", "Yemen", "Yemeni"
    ],
    "cities_and_governorates": [
        "صنعاء", "عدن", "تعز", "الحديدة", "إب", "حجة", "صعدة", "المكلا",
        "سيئون", "مأرب", "الجوف", "الضالع", "لحج", "أبين", "شبوة", "حضرموت",
        "المحويت", "ريمة", "عمران", "ذمار", "البيضاء", "سقطرى", "المخا",
        "باب المندب", "ميون", "حنيش", "الصليف", "رأس عيسى", "الخوخة",
        "نشطون", "بير علي", "بلحاف", "الشحر", "الغيضة", "المهرة",
        "Sanaa", "Sana'a", "Hodeidah", "Hudaydah", "Socotra", "Marib", "Mukalla",
        "Bab el-Mandeb", "Bab al-Mandab", "Houthi", "Houthis"
    ],
    "organizations_and_authorities": [
        "حكومة صنعاء", "الحكومة الشرعية", "الحكومة اليمنية", "المجلس الرئاسي",
        "مجلس القيادة الرئاسي", "أنصار الله", "الحوثي", "الحوثيون", "الحوثيين",
        "القوات المسلحة اليمنية", "التحالف العربي", "التحالف السعودي الإماراتي",
        "UKMTO", "أسبيدس", "Aspides", "CENTCOM", "سنتكوم",
        "الأمم المتحدة في اليمن", "المبعوث الأممي إلى اليمن", "المبعوث الأممي لليمن",
        "UNMHA", "OCHA Yemen", "مؤسسة موانئ البحر الأحمر", "خفر السواحل اليمني",
        "المجلس الانتقالي الجنوبي"
    ],
    "persons_and_leaders": [
        "أحمد عوض بن مبارك", "عبدالملك الحوثي", "عبد الملك الحوثي",
        "مهدي المشاط", "رشاد العليمي", "عيدروس الزبيدي", "سلطان العرادة",
        "طارق صالح", "يحيى سريع", "محمد عبدالسلام", "محمد علي الحوثي",
        "هانس غروندبرغ", "غروندبرغ", "شائع الزنداني", "معين عبدالملك"
    ],
    "yemen_ports": [
        "ميناء الحديدة", "ميناء عدن", "ميناء الصليف", "ميناء رأس عيسى",
        "ميناء المخا", "ميناء المكلا", "ميناء نشطون", "ميناء بير علي",
        "ميناء بلحاف", "ميناء قنا", "ميناء الشحر"
    ],
    "waterways": [
        "باب المندب", "مضيق باب المندب", "خليج عدن", "البحر الأحمر"
    ]
}

# المواقع والجهات المشتركة التي لا تكفي وحدها ويشترط اقترانها بكلمة سياقية أو كيان يمني صريح
SHARED_CONTEXT_DEPENDENT_ENTITIES: List[str] = [
    "البحر الأحمر",
    "تعز",
    "عدن",
    "خليج عدن",
    "CENTCOM",
    "سنتكوم",
]

# قائمة مسطحة للكيانات اليمنية الصريحة غير المشتركة (تُثبت الصلة اليمنية مباشرة)
EXPLICIT_YEMEN_ENTITIES: List[str] = []
for _cat_key, _items in YEMEN_CORE_ENTITIES.items():
    for _itm in _items:
        if _itm not in SHARED_CONTEXT_DEPENDENT_ENTITIES and _itm not in EXPLICIT_YEMEN_ENTITIES:
            EXPLICIT_YEMEN_ENTITIES.append(_itm)


# ==============================================================================
# ب) قائمة Exclude Entities (كيانات للاستبعاد الفوري عند غياب سياق يمني صريح)
# ==============================================================================
EXCLUDE_ENTITIES: Dict[str, List[str]] = {
    "artists_and_celebrities": [
        "أحمد السقا", "رحمة حسن", "فؤادة", "هشام سليمان", "محمد رمضان",
        "تامر حسني", "عمرو دياب", "عادل إمام", "أحمد عز", "كريم عبدالعزيز",
        "أمير كرارة", "ياسمين صبري", "منى زكي", "شيرين عبدالوهاب", "رامز جلال",
        "غادة عبدالرازق", "إلهام شاهين", "يسرا", "ليلى علوي", "هيفاء وهبي",
        "نانسي عجرم", "إليسا", "أصالة", "أنغام", "محمد هنيدي", "أحمد حلمي",
        "بيومي فؤاد", "أكرم حسني", "ويجز"
    ],
    "global_tech": [
        "إنفيديا", "نفيديا", "Nvidia", "جنسن هوانغ", "أبل", "آبل", "Apple",
        "آيفون", "iPhone", "مايكروسوفت", "Microsoft", "جوجل", "ميتا", "Meta",
        "تويتر", "تسلا", "Tesla", "إيلون ماسك", "سامسونغ", "Samsung", "Galaxy",
        "Honor", "Oppo", "Snapdragon", "Geekbench", "جيمس ويب", "بلايستيشن"
    ],
    "sports": [
        "الأهلي", "الزمالك", "مباريات", "مباراة", "دوري", "الدوري المصري",
        "الدوري السعودي", "الدوري الإنجليزي", "دوري أبطال", "كأس العالم",
        "فيفا", "ريال مدريد", "برشلونة", "ليفربول", "مانشستر", "محمد صلاح",
        "كريستيانو رونالدو", "ميسي", "مونديال"
    ],
    "entertainment": [
        "مهرجان", "مهرجان القاهرة", "مهرجان البحر الأحمر السينمائي",
        "مهرجان الجونة", "سينما", "السينمائي", "السينمائى", "فيلم", "أفلام",
        "مسلسل", "مسلسلات", "حفل", "أغنية", "أوسكار", "الفن", "دراما",
        "شباك التذاكر"
    ],
    "egypt_internal": [
        "القاهرة", "الإسكندرية", "الجيزة", "مدبولي", "سكك حديد مصر",
        "المصري اليوم", "اليوم السابع", "بوابة الشروق", "Masrawy", "جنيه",
        "الصعيد", "المنصورة", "طنطا", "أسوان", "الأقصر", "المنوفية",
        "الأزهر", "السد العالي", "سد النهضة", "الأرصاد", "الشعبة"
    ],
    "gulf_and_foreign_internal": [
        "جدة", "موسم الرياض", "موسم جدة", "مهرجان جدة", "غولدمان ساكس",
        "الفيدرالي", "وول ستريت"
    ]
}

ALL_EXCLUDE_ENTITIES: List[str] = []
for _exc_list in EXCLUDE_ENTITIES.values():
    for _e in _exc_list:
        if _e not in ALL_EXCLUDE_ENTITIES:
            ALL_EXCLUDE_ENTITIES.append(_e)


# ==============================================================================
# ج) كلمات السياق الأمني/البحري/الحكومي/اليمني
# ==============================================================================
CONTEXT_KEYWORDS: List[str] = [
    "سفينة", "سفن", "ناقلة", "ناقلات", "ملاحة", "الملاحة", "بحري", "بحرية",
    "هجوم", "استهداف", "صاروخ", "صواريخ", "مسيرة", "مسيرات", "ميناء", "موانئ",
    "قوات", "عسكري", "عسكرية", "أمن", "أمني", "أمنية", "حكومة", "يمني", "يمنية",
    "اليمن", "صنعاء", "اشتباك", "اشتباكات", "إغاثة", "مساعدات", "توتر", "النفط",
    "نفط", "شحنة", "شحن", "تهديد", "قصف", "غارة", "اعتراض", "حصار", "مقتل",
    "مصرع", "مدنيين", "حادث", "المبعوث", "الأممي", "هدنة", "مفاوضات", "تحالف",
    "مضيق", "زورق", "فرقاطة", "بضائع", "طوارئ", "انفجار", "غرق",
    "ship", "vessel", "tanker", "maritime", "shipping", "port", "missile",
    "drone", "attack", "humanitarian", "relief", "aid", "Yemen", "Sanaa"
]

# قائمة المواقع اليمنية الحقيقية مرتبة من الأكثر تحديداً (الموانئ والمدن) إلى الأعم
ORDERED_YEMEN_LOCATIONS: List[str] = [
    "ميناء الحديدة", "ميناء عدن", "ميناء الصليف", "ميناء رأس عيسى",
    "ميناء المخا", "ميناء المكلا", "ميناء نشطون", "ميناء بير علي",
    "مضيق باب المندب", "باب المندب", "جزيرة ميون", "ميون", "حنيش",
    "صنعاء", "الحديدة", "الصليف", "رأس عيسى", "عدن", "تعز", "مأرب",
    "المكلا", "حضرموت", "سقطرى", "المخا", "الخوخة", "صعدة", "حجة",
    "إب", "شبوة", "بلحاف", "أبين", "لحج", "الضالع", "الجوف", "البيضاء",
    "ذمار", "عمران", "المحويت", "ريمة", "سيئون", "نشطون", "بير علي",
    "الشحر", "الغيضة", "المهرة", "خليج عدن", "البحر الأحمر"
]


# ==============================================================================
# دوال المطابقة اللغوية الدقيقة بحدود الكلمة الكاملة (Word Boundary Matching)
# ==============================================================================
def _clean_html_and_urls(text: str) -> str:
    """إزالة وسوم HTML والروابط المشفرة (مثل روابط Google News Base64) قبل الفحص النصي"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'https?://\S+', ' ', text)
    text = re.sub(r'&[a-zA-Z0-9#]+;', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def _normalize_arabic(text: str) -> str:
    """تطبيع النص العربي مع الحفاظ على بنية الكلمات لتطبيق حدود الكلمة بدقة"""
    if not text:
        return ""
    # إزالة التشكيل والتطويل
    text = re.sub(r'[\u064B-\u0652\u0640]', '', text)
    # توحيد الألف والهمزات الأولية
    text = re.sub(r'[أإآ]', 'ا', text)
    # توحيد الياء والألف المقصورة في نهاية الكلمة
    text = re.sub(r'ى(?=$|[^\u0621-\u064A])', 'ي', text)
    # توحيد التاء المربوطة في نهاية الكلمة
    text = re.sub(r'ة(?=$|[^\u0621-\u064A])', 'ه', text)
    return text


def match_whole_term(text: str, term: str) -> bool:
    """
    مطابقة الكلمة أو العبارة الكاملة (Word Boundary) مع مراعاة حروف الجر والعطف العربية
    ومنع الأخطاء الشائعة مثل:
    - مطابقة 'عدن' داخل 'معدن'
    - مطابقة 'تعز' داخل 'تعزيز' أو 'تعتزم'
    - مطابقة 'إب' داخل 'إبراهيم' أو 'آب'
    - مطابقة 'حجة' داخل 'بحجة'
    - مطابقة 'جدة' داخل 'وجده'
    """
    if not text or not term:
        return False

    # 1. حالات خاصة تتطلب حساسية عالية لمنع التداخل اللفظي في العربية
    if term == "إب":
        # محافظة إب: تشترط وجود همزة القطع المكسورة (إب) أو سبقها بكلمة محافظة/مدينة
        pattern_ibb = r'(?:^|[^\u0621-\u064A0-9a-zA-Z])(?:محافظ[ةه]\s+اب|مدين[ةه]\s+اب|(?:في\s+|من\s+|الي\s+)?إب)(?=$|[^\u0621-\u064A0-9a-zA-Z])'
        return bool(re.search(pattern_ibb, text))

    if term == "حجة":
        # محافظة حجة: لا يجوز أن تسبق بحرف الباء المتصل (بحجة) لأنها تعني الذريعة
        pattern_hajjah = r'(?:^|[^\u0621-\u064A0-9a-zA-Z])(?:محافظ[ةه]\s+حج[ةه]|مدين[ةه]\s+حج[ةه]|[وفل]?حجة)(?=$|[^\u0621-\u064A0-9a-zA-Z])'
        return bool(re.search(pattern_hajjah, text))

    if term == "جدة":
        # مدينة جدة: تشترط التاء المربوطة حتى لا تطابق 'وجده' أو 'جده'
        pattern_jeddah = r'(?:^|[^\u0621-\u064A0-9a-zA-Z])(?:[وف]?[بلك]?)?جدة(?=$|[^\u0621-\u064A0-9a-zA-Z])'
        return bool(re.search(pattern_jeddah, text))

    # 2. للمصطلحات الإنجليزية واللاتينية
    if re.match(r'^[A-Za-z0-9\s\-_]+$', term):
        pattern_en = r'(?:^|[^A-Za-z0-9])' + re.escape(term) + r'(?=$|[^A-Za-z0-9])'
        return bool(re.search(pattern_en, text, flags=re.IGNORECASE))

    # 3. للمصطلحات العربية المفردة والمركبة
    norm_text = _normalize_arabic(text)
    norm_term = _normalize_arabic(term).strip()

    words = norm_term.split()
    if len(words) == 1:
        w = words[0]
        # إذا كانت الكلمة تبدأ بـ "ال" التعريف، نسمح أيضاً بصيغة "بالـ" و"للـ" و"والـ"
        if w.startswith("ال") and len(w) > 3:
            stem = re.escape(w[2:])
            prefix_pat = r'(?:[وف]?[بلك]?ال|[وف]?لل)'
            pattern = r'(?:^|[^\u0621-\u064A0-9a-zA-Z])' + prefix_pat + stem + r'(?=$|[^\u0621-\u064A0-9a-zA-Z])'
        else:
            # للكلمات بدون "ال" (مثل عدن، تعز، صنعاء، مهرجان):
            # نسمح فقط بحروف العطف والجر القياسية ([وف]?[بلك]?(?:ال)?) ولا نسمح أبداً بحرف الميم أو التاء أو الياء!
            stem = re.escape(w)
            prefix_pat = r'(?:[وف]?[بلك]?(?:ال)?|[وف]?لل)?'
            pattern = r'(?:^|[^\u0621-\u064A0-9a-zA-Z])' + prefix_pat + stem + r'(?=$|[^\u0621-\u064A0-9a-zA-Z])'
        return bool(re.search(pattern, norm_text))
    else:
        # عبارة مركبة من عدة كلمات (مثل "باب المندب"، "أحمد السقا"، "البحر الأحمر")
        first = words[0]
        rest = r'\s+'.join(re.escape(x) for x in words[1:])
        if first.startswith("ال") and len(first) > 3:
            first_pat = r'(?:[وف]?[بلك]?ال|[وف]?لل)' + re.escape(first[2:])
        else:
            first_pat = r'(?:[وف]?[بلك]?(?:ال)?|[وف]?لل)?' + re.escape(first)
        pattern = r'(?:^|[^\u0621-\u064A0-9a-zA-Z])' + first_pat + r'\s+' + rest + r'(?=$|[^\u0621-\u064A0-9a-zA-Z])'
        return bool(re.search(pattern, norm_text))


def extract_yemen_location(title: str, summary: str = "") -> Optional[str]:
    """
    استخراج موقع يمني حقيقي من النص باستخدام مطابقة الكلمة الكاملة (Word Boundary).
    لا يعطي 'البحر الأحمر' تلقائياً إلا إذا ورد فعلياً في سياق يمني/بحري/أمني معتبر.
    """
    title_clean = _clean_html_and_urls(title or "")
    summary_clean = _clean_html_and_urls(summary or "")
    full_text = f"{title_clean} {summary_clean}".strip()
    if not full_text:
        return None

    has_context = any(match_whole_term(full_text, kw) for kw in CONTEXT_KEYWORDS)
    has_explicit_yemen = any(match_whole_term(full_text, ent) for ent in EXPLICIT_YEMEN_ENTITIES)

    # البحث أولاً في العنوان ثم في الملخص لضمان أولوية الموقع الرئيسي للخبر
    for segment in (title_clean, summary_clean):
        for loc in ORDERED_YEMEN_LOCATIONS:
            if match_whole_term(segment, loc):
                if loc in SHARED_CONTEXT_DEPENDENT_ENTITIES:
                    if has_context or has_explicit_yemen:
                        return loc
                else:
                    return loc
    return None


def is_yemen_relevant(title: str, summary: str = "") -> FilterResult:
    """
    فحص مدى ارتباط الخبر بالشأن اليمني والأمن الإقليمي المرتبط باليمن
    وفق الترتيب الصارم:
      أ) فحص الاستبعاد الصريح (Exclude Entities)
      ب) فحص الكيانات اليمنية الجوهرية الصريحة (Explicit Yemen Core Entities)
      ج) فحص السياق للمواقع المشتركة (البحر الأحمر، تعز، عدن...)
      د) الرفض عند عدم تحقق أي رابط يمني (no_yemen_link)
      هـ) حساب درجة الصلة relevance_score (0-100) واشتراط >= 40
    """
    title_str = _clean_html_and_urls(title or "")
    summary_str = _clean_html_and_urls(summary or "")
    full_text = f"{title_str} {summary_str}".strip()

    if not full_text:
        return FilterResult(accepted=False, reason="no_yemen_link", score=0)

    # فحص الكيانات الصريحة والكيانات المستبعدة وكلمات السياق
    explicit_in_title = [e for e in EXPLICIT_YEMEN_ENTITIES if match_whole_term(title_str, e)]
    explicit_in_summary = [e for e in EXPLICIT_YEMEN_ENTITIES if match_whole_term(summary_str, e)]
    has_explicit_yemen = bool(explicit_in_title or explicit_in_summary)

    excluded_hits = [ex for ex in ALL_EXCLUDE_ENTITIES if match_whole_term(full_text, ex)]

    # ------------------------------------------------------------------
    # الخطوة أ: فحص الاستبعاد الصريح
    # إذا وُجد كيان في قائمة Exclude + لا يوجد كيان يمني صريح في نفس النص → REJECT فوري
    # ------------------------------------------------------------------
    if excluded_hits and not has_explicit_yemen:
        return FilterResult(
            accepted=False,
            reason="excluded_entity",
            score=0,
            matched_entities=excluded_hits,
            matched_location=None
        )

    # ------------------------------------------------------------------
    # الخطوة ب & ج: فحص الكيانات اليمنية الجوهرية وفحص السياق للمواقع المشتركة
    # ------------------------------------------------------------------
    context_hits = [kw for kw in CONTEXT_KEYWORDS if match_whole_term(full_text, kw)]
    has_context = bool(context_hits)

    shared_in_title = [s for s in SHARED_CONTEXT_DEPENDENT_ENTITIES if match_whole_term(title_str, s)]
    shared_in_summary = [s for s in SHARED_CONTEXT_DEPENDENT_ENTITIES if match_whole_term(summary_str, s)]

    # المواقع المشتركة ("البحر الأحمر"، "تعز"، "عدن") لا تُقبل وحدها إلا مع كلمة سياقية أو كيان يمني صريح
    valid_shared_in_title = shared_in_title if (has_context or has_explicit_yemen) else []
    valid_shared_in_summary = shared_in_summary if (has_context or has_explicit_yemen) else []

    yemen_in_title = explicit_in_title + valid_shared_in_title
    yemen_in_summary = explicit_in_summary + valid_shared_in_summary

    # ------------------------------------------------------------------
    # الخطوة د: إذا لم يتحقق أي شرط → REJECT بسبب "no_yemen_link"
    # ------------------------------------------------------------------
    if not yemen_in_title and not yemen_in_summary:
        return FilterResult(
            accepted=False,
            reason="no_yemen_link",
            score=0,
            matched_entities=[],
            matched_location=None
        )

    # ------------------------------------------------------------------
    # الخطوة هـ: حساب relevance_score (0-100):
    #   - كيان يمني في العنوان = +50
    #   - كيان يمني في الملخص = +30
    #   - كلمة سياق أمني/بحري/حكومي = +20
    #   - إذا < 40 → REJECT تلقائياً
    # ------------------------------------------------------------------
    score = 0
    if yemen_in_title:
        score += 50
    if yemen_in_summary:
        score += 30
    if has_context:
        score += 20

    score = min(100, score)

    if score < 40:
        return FilterResult(
            accepted=False,
            reason="low_relevance_score",
            score=score,
            matched_entities=list(dict.fromkeys(yemen_in_title + yemen_in_summary)),
            matched_location=extract_yemen_location(title_str, summary_str)
        )

    return FilterResult(
        accepted=True,
        reason=None,
        score=score,
        matched_entities=list(dict.fromkeys(yemen_in_title + yemen_in_summary)),
        matched_location=extract_yemen_location(title_str, summary_str)
    )


class YemenRelevanceFilter:
    """واجهة كائنية لفلتر الصلة اليمنية"""
    @staticmethod
    def check(title: str, summary: str = "") -> FilterResult:
        return is_yemen_relevant(title, summary)

    @staticmethod
    def extract_location(title: str, summary: str = "") -> Optional[str]:
        return extract_yemen_location(title, summary)

