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
        # المواقع الحساسة والمطارات والمنافذ والجزر والمديريات (الخطوة 1.1 أ)
        "مطار صنعاء", "مطار عدن", "مطار الريان", "مطار تعز",
        "منفذ الوديعة", "منفذ شحن", "منفذ البقع", "منفذ الطوال",
        "جزيرة كمران", "جزيرة زقر", "جزيرة الزبير",
        "حريب", "بيحان", "العبر", "الحزم", "الروضة",
        "خمر", "حرض", "ميدي", "الزيدية",
        "التربة", "المخاء", "مقبنة", "موزع",
        "رداع", "مكيراس",
        "عتق", "زنجبار", "جعار", "أحور", "المحفد",
        "تريم", "غيل باوزير", "الديس", "الريان",
        "حديبو", "حديبو سقطرى", "عبد الكوري",
        "قصر معاشيق", "مدينة مأرب", "الساحل الغربي",
        # الصيغ الإنجليزية للمدن والمحافظات (الخطوة 3.2)
        "Sanaa", "Sana'a", "Hodeidah", "Hudaydah", "Socotra", "Marib", "Mukalla",
        "Taiz", "Aden", "Saada", "Mokha", "Shabwa",
        "Bab el-Mandeb", "Bab al-Mandab", "Houthi", "Houthis"
    ],
    "organizations_and_authorities": [
        "حكومة صنعاء", "الحكومة الشرعية", "الحكومة اليمنية", "المجلس الرئاسي",
        "مجلس القيادة الرئاسي", "أنصار الله", "الحوثي", "الحوثيون", "الحوثيين",
        "القوات المسلحة اليمنية", "التحالف العربي", "التحالف السعودي الإماراتي",
        "UKMTO", "أسبيدس", "Aspides", "CENTCOM", "سنتكوم",
        "الأمم المتحدة في اليمن", "المبعوث الأممي إلى اليمن", "المبعوث الأممي لليمن",
        "UNMHA", "OCHA Yemen", "مؤسسة موانئ البحر الأحمر", "خفر السواحل اليمني",
        "المجلس الانتقالي الجنوبي",
        # الجهات والبنوك والوزارات والمنظمات الأممية في اليمن (الخطوة 1.1 ب)
        "البنك المركزي اليمني", "البنك المركزي عدن", "البنك المركزي صنعاء",
        "درع الوطن", "ألوية العمالقة", "المقاومة الوطنية",
        "حلف قبائل حضرموت", "المجلس المحلي", "مجلس النواب",
        "مجلس الشورى", "وزارة الدفاع", "وزارة الداخلية",
        "الأمن العام", "الأمن السياسي", "الأمن القومي",
        "الهيئة الوطنية لإدارة وتنسيق الشؤون الإنسانية", "NCHA",
        "مكتب الأمم المتحدة لتنسيق الشؤون الإنسانية في اليمن",
        "منظمة الصحة العالمية في اليمن", "WHO Yemen",
        "اليونيسف في اليمن", "UNICEF Yemen",
        "المفوضية السامية لشؤون اللاجئين في اليمن", "UNHCR Yemen",
        # المسميات الرسمية للتشكيلات العسكرية والسياسية (الخطوة 2.2)
        "الجيش الوطني اليمني", "قوات الشرعية",
        "المنطقة العسكرية الأولى", "المنطقة العسكرية الثانية",
        "المنطقة العسكرية الثالثة", "المنطقة العسكرية الرابعة",
        "المنطقة العسكرية الخامسة", "المنطقة العسكرية السادسة",
        "المنطقة العسكرية السابعة",
        "محور تعز", "محور البقع", "محور علب", "محور مران",
        "ألوية اليمن السعيد", "قوات درع الوطن",
        "قوات الواجب المشتركة", "ألوية العروبة", "ألوية الفتح",
        "ألوية التوحيد", "حرس الحدود اليمني",
        "القوات المشتركة", "العمالقة الجنوبية",
        "حراس الجمهورية", "المقاومة التهامية",
        "ألوية الزرانيق", "القوات المسلحة الجنوبية",
        "قوات الحزام الأمني", "الحزام الأمني عدن",
        "الحزام الأمني لحج", "الحزام الأمني أبين",
        "الحزام الأمني الضالع", "قوات النخبة الشبوانية",
        "قوات النخبة الحضرمية", "قوات دفاع شبوة",
        "قوات الصاعقة", "قوات الدعم والإسناد",
        "محور يافع", "محور الضالع",
        "الحكومة اليمنية في عدن", "مجلس الوزراء اليمني",
        "المكتب السياسي للمقاومة الوطنية", "التحالف الوطني للأحزاب",
        "البنك المركزي في عدن", "وزارة الدفاع اليمنية"
    ],
    "persons_and_leaders": [
        "أحمد عوض بن مبارك", "عبدالملك الحوثي", "عبد الملك الحوثي",
        "مهدي المشاط", "رشاد العليمي", "عيدروس الزبيدي", "سلطان العرادة",
        "طارق صالح", "يحيى سريع", "محمد عبدالسلام", "محمد علي الحوثي",
        "هانس غروندبرغ", "غروندبرغ", "شائع الزنداني", "معين عبدالملك",
        # القيادات والشخصيات الإضافية (الخطوة 1.1 ج)
        "عبدالعزيز بن حبتور", "عبدالكريم العرشي",
        "حمود الصبري", "صالح الصماد",
        "عبدالله الردمي", "عبدالحكيم الخيواني",
        "حسين العزي", "عبدالسلام صلاح",
        "خالد بحاح", "أحمد عبيد بن دغر",
        "مايكل أرون", "فرج البحسني", "عبدالرحمن المحرمي",
        "عبدالله العليمي", "عثمان مجلي",
        # الصيغ الإنجليزية للقيادات (الخطوة 3.2)
        "Abdul-Malik al-Houthi", "Yahya Saree", "Mahdi al-Mashat",
        "Rashad al-Alimi", "Aidarus al-Zoubaidi", "Tareq Saleh", "Israel Katz"
    ],
    "yemen_ports": [
        "ميناء الحديدة", "ميناء عدن", "ميناء الصليف", "ميناء رأس عيسى",
        "ميناء المخا", "ميناء المكلا", "ميناء نشطون", "ميناء بير علي",
        "ميناء بلحاف", "ميناء قنا", "ميناء الشحر",
        # الموانئ الإضافية (الخطوة 1.1 د)
        "ميناء الضبة", "ميناء النشيمة", "ميناء الخوخة",
        "رصيف بلحاف", "مرسى الفجير", "ميناء المخا القديم"
    ],
    "waterways": [
        "باب المندب", "مضيق باب المندب", "خليج عدن", "البحر الأحمر",
        # الممرات المائية الإضافية (الخطوة 1.1 هـ)
        "مضيق هرمز", "خليج عمان", "بحر العرب", "المحيط الهندي",
        "قناة السويس", "البحر المتوسط"
    ]
}

# ==============================================================================
# الخطوة 2: قاموس المصطلحات العسكرية والتعبوية (MILITARY_TERMS & PROPAGANDA_TERMS)
# ==============================================================================
# ملاحظة: المصطلحات التعبوية في propaganda_sanaa تُستخدم في إعلام صنعاء/أنصار الله
# وهي مخصصة للرصد والتحليل الإعلامي فقط وتُضاف إلى CONTEXT_KEYWORDS كسياق إعلامي.
PROPAGANDA_TERMS: List[str] = [
    "مرتزقة", "مرتزقة العدوان", "مرتزقة السعودية", "مرتزقة الإمارات",
    "أدوات العدوان", "عملاء العدوان", "مليشيات العدوان",
    "الخونة والعملاء", "مجندو التحالف", "الفصائل الموالية للتحالف",
    "التشكيلات المسلحة الموالية للإمارات", "التشكيلات المسلحة الموالية للسعودية",
    "حكومة المرتزقة", "حكومة الفنادق", "سلطة الارتزاق", "مجلس الخيانة",
    "المجلس الرئاسي التابع للتحالف", "حكومة معين", "حكومة بن مبارك",
    "حكومة عدن", "السلطة الموالية للعدوان", "الشرعية المزعومة"
]

MILITARY_TERMS: Dict[str, List[str]] = {
    "propaganda_sanaa": list(PROPAGANDA_TERMS),
    "saudi_backed_official": [
        "الجيش الوطني اليمني", "قوات الشرعية",
        "المنطقة العسكرية الأولى", "المنطقة العسكرية الثانية",
        "المنطقة العسكرية الثالثة", "المنطقة العسكرية الرابعة",
        "المنطقة العسكرية الخامسة", "المنطقة العسكرية السادسة",
        "المنطقة العسكرية السابعة",
        "محور تعز", "محور البقع", "محور علب", "محور مران",
        "ألوية اليمن السعيد", "قوات درع الوطن",
        "قوات الواجب المشتركة", "ألوية العروبة", "ألوية الفتح",
        "ألوية التوحيد", "حرس الحدود اليمني"
    ],
    "uae_backed_official": [
        "القوات المشتركة", "ألوية العمالقة", "العمالقة الجنوبية",
        "المقاومة الوطنية", "حراس الجمهورية", "المقاومة التهامية",
        "ألوية الزرانيق", "القوات المسلحة الجنوبية",
        "قوات الحزام الأمني", "الحزام الأمني عدن",
        "الحزام الأمني لحج", "الحزام الأمني أبين",
        "الحزام الأمني الضالع", "قوات النخبة الشبوانية",
        "قوات النخبة الحضرمية", "قوات دفاع شبوة",
        "قوات الصاعقة", "قوات الدعم والإسناد",
        "محور يافع", "محور الضالع"
    ],
    "political_admin": [
        "مجلس القيادة الرئاسي", "الحكومة اليمنية في عدن",
        "مجلس الوزراء اليمني", "المجلس الانتقالي الجنوبي",
        "المكتب السياسي للمقاومة الوطنية", "التحالف الوطني للأحزاب",
        "البنك المركزي في عدن", "وزارة الدفاع اليمنية"
    ],
}

# ==============================================================================
# الخطوة 3: المصطلحات الإنجليزية لوكالات الأنباء الغربية والإعلام الإسرائيلي (WESTERN_TERMS)
# ==============================================================================
WESTERN_TERMS = {
    # توصيفات الأطراف (رويترز/الجارديان/AP/BBC)
    "houthis", "houthi movement", "houthi rebels", "houthi militants",
    "iran-aligned houthis", "iran-backed houthis",
    "yemen's internationally recognized government",
    "saudi-backed government forces",
    "presidential leadership council", "plc",
    "southern transitional council", "stc",
    "saudi-led coalition",

    # العمليات والمعارك
    "yemen civil war", "yemen conflict",
    "territorial gains", "military offensive", "ground offensive",
    "clashes in yemen", "frontline fighting", "besieged yemeni city",
    "air campaign", "airstrikes in yemen", "retaliatory strikes",
    "ceasefire collapse", "fragile truce", "un-led peace process",

    # أزمة البحر الأحمر والملاحة
    "red sea crisis", "bab-el-mandeb strait", "gulf of aden",
    "arabian sea", "red sea chokehold", "freedom of navigation",
    "commercial shipping", "merchant vessel", "bulk carrier",
    "oil tanker", "naval blockade", "maritime security",
    "ship hijacking", "us central command", "centcom",
    "operation prosperity guardian", "operation aspides",
    "ukmto", "multinational maritime defense alliance",

    # الإعلام الإسرائيلي
    "houthi terrorists", "iranian proxy",
    "axis of resistance", "multi-front war", "seventh front",
    "houthi threat", "long-range attacks",
    "ballistic missile from yemen", "surface-to-surface missile",
    "houthi uav", "explosive-laden drone", "suicide drone",
    "arrow air defense system", "david's sling", "thaad",
    "aerial interception", "sirens sound in eilat",
    "central israel sirens", "red sea port of eilat",
    "idf strikes in yemen", "israeli air force", "iaf",
    "hodeidah port strikes", "ras isa", "sanaa airport",
    "power station strikes",

    # الأسلحة والقدرات
    "ballistic missiles", "cruise missiles", "hypersonic missile",
    "one-way attack drones", "unmanned surface vessels", "usvs",
    "unmanned underwater vehicles", "uuvs",
    "air defenses", "mq-9 reaper drone", "f-15 fighter jet",
    "f-35", "aircraft carrier", "guided-missile destroyer",
    "weapons smuggling", "arms embargo",
    "illicit weapons shipments", "dhow interception",
}

# المواقع والجهات المشتركة التي لا تكفي وحدها ويشترط اقترانها بكلمة سياقية أو كيان يمني صريح
SHARED_CONTEXT_DEPENDENT_ENTITIES: List[str] = [
    "البحر الأحمر",
    "تعز",
    "عدن",
    "خليج عدن",
    "CENTCOM",
    "سنتكوم",
    "مضيق هرمز",
    "خليج عمان",
    "بحر العرب",
    "المحيط الهندي",
    "قناة السويس",
    "البحر المتوسط",
]

# قائمة مسطحة للكيانات اليمنية الصريحة غير المشتركة (تُثبت الصلة اليمنية مباشرة وتشمل WESTERN_TERMS)
EXPLICIT_YEMEN_ENTITIES: List[str] = []
for _cat_key, _items in YEMEN_CORE_ENTITIES.items():
    for _itm in _items:
        if _itm not in SHARED_CONTEXT_DEPENDENT_ENTITIES and _itm not in EXPLICIT_YEMEN_ENTITIES:
            EXPLICIT_YEMEN_ENTITIES.append(_itm)
for _wterm in sorted(WESTERN_TERMS):
    if _wterm not in SHARED_CONTEXT_DEPENDENT_ENTITIES and _wterm not in EXPLICIT_YEMEN_ENTITIES:
        EXPLICIT_YEMEN_ENTITIES.append(_wterm)


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
        "إنفيديا", "نفيديا", "Nvidia", "جنسن هوانغ",
        "آيفون", "iPhone", "مايكروسوفت", "Microsoft", "ميتا", "Meta",
        "تسلا", "Tesla", "إيلون ماسك", "سامسونغ", "Samsung", "Galaxy",
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

# قائمة الاستبعاد الناعم (الخطوة 4.2): تُرفض فقط إذا لم يوجد أي كيان يمني صريح في النص
SOFT_EXCLUDE_ENTITIES: List[str] = [
    "جوجل", "تويتر", "أبل", "آبل", "Apple", "Google", "Twitter"
]

# قائمة النطاق البحري للمصادر الدولية (الخطوة 4.3)
MARITIME_REGION_ENTITIES: List[str] = [
    "البحر الأحمر", "Red Sea",
    "خليج عدن", "Gulf of Aden",
    "باب المندب", "Bab el-Mandeb", "Bab al-Mandab",
    "بحر العرب", "Arabian Sea",
    "مضيق هرمز", "Strait of Hormuz",
    "المحيط الهندي", "Indian Ocean",
    "قناة السويس", "Suez Canal",
    "اليمن", "Yemen", "الحديدة", "Hodeidah", "عدن", "Aden"
]


# ==============================================================================
# ج) كلمات السياق الأمني/البحري/الحكومي/اليمني + السياق الإعلامي + المصطلحات الغربية
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
# دمج المصطلحات التعبوية (سياق إعلامي) والمصطلحات الإنجليزية في CONTEXT_KEYWORDS
for _pt in PROPAGANDA_TERMS:
    if _pt not in CONTEXT_KEYWORDS:
        CONTEXT_KEYWORDS.append(_pt)
for _wt in sorted(WESTERN_TERMS):
    if _wt not in CONTEXT_KEYWORDS:
        CONTEXT_KEYWORDS.append(_wt)
# دمج المصطلحات العسكرية الميدانية الموسعة (عربي + إنجليزي) في CONTEXT_KEYWORDS بدون تكرار (الخطوة 4)
try:
    from filters.military_terms import get_all_military_field_keywords
    for _mkw in get_all_military_field_keywords():
        if _mkw not in CONTEXT_KEYWORDS:
            CONTEXT_KEYWORDS.append(_mkw)
except Exception:
    pass

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
    if re.match(r"^[A-Za-z0-9\s\-_']+$", term):
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


def is_soft_excluded(word: str, text: str) -> bool:
    """
    دالة الاستبعاد الناعم (الخطوة 4.2):
    ترجع True (يُرفض) فقط إذا وُجدت كلمة الاستبعاد الناعم (مثل جوجل/تويتر/أبل)
    ولم يوجد أي كيان يمني صريح في نفس النص.
    """
    clean_txt = _clean_html_and_urls(text or "")
    if not clean_txt or not word:
        return False
    if not match_whole_term(clean_txt, word):
        return False
    has_explicit = any(match_whole_term(clean_txt, ent) for ent in EXPLICIT_YEMEN_ENTITIES)
    return not has_explicit


def is_maritime_region_relevant(title: str, summary: str = "") -> bool:
    """
    دالة فحص النطاق البحري الإقليمي (الخطوة 4.3):
    تُطبق على الأخبار المصنفة 'بحري' أو 'أمني/عسكري' القادمة من المصادر الدولية
    (USNI, Naval News, gCaptain, Splash247, Maritime Executive) لضمان ارتباطها بنطاق البحر الأحمر وباب المندب وخليج عدن وبحر العرب.
    """
    full_text = _clean_html_and_urls(f"{title or ''} {summary or ''}".strip())
    if not full_text:
        return False
    return any(match_whole_term(full_text, ent) for ent in MARITIME_REGION_ENTITIES)


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
    soft_excluded_hits = [sx for sx in SOFT_EXCLUDE_ENTITIES if is_soft_excluded(sx, full_text)]

    # ------------------------------------------------------------------
    # الخطوة أ: فحص الاستبعاد الصريح والاستبعاد الناعم
    # إذا وُجد كيان في قائمة Exclude + لا يوجد كيان يمني صريح في نفس النص → REJECT فوري
    # ------------------------------------------------------------------
    if (excluded_hits or soft_excluded_hits) and not has_explicit_yemen:
        return FilterResult(
            accepted=False,
            reason="excluded_entity" if excluded_hits else "soft_excluded_entity",
            score=0,
            matched_entities=excluded_hits or soft_excluded_hits,
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

