from typing import List, Dict, Any

# ==============================================================================
# الخطوة 3.3: صيغ الاستعلام المنطقية الجاهزة (Boolean Queries) لدعم البحث
# ==============================================================================
BOOLEAN_QUERIES: Dict[str, str] = {
    "western_clashes": '(Houthis OR Yemen) AND (offensive OR clashes OR airstrikes OR "territorial gains" OR ceasefire) -sport -football',
    "israeli_coverage": '(Houthis OR Yemen) AND (IDF OR Eilat OR Arrow OR "ballistic missile" OR Hodeidah OR Sanaa)',
    "maritime_red_sea": '("Red Sea" OR "Bab-el-Mandeb" OR "Gulf of Aden") AND (Houthis OR shipping OR vessel OR CENTCOM OR UKMTO)',
}

# ==============================================================================
# الخطوة 2.1 + الخطوة 5.1 + الخطوة 6: قائمة خلاصات RSS اليمنية والبحرية المباشرة
# ==============================================================================
# توثيق فحص الروابط الجديدة (المرحلة 5.1 — اختبار فعلي HTTP 200 + XML صالح):
#
# أ) مصادر جديدة تم التحقق من عملها وإضافتها:
#   - الجزيرة نت - اليمن (https://www.aljazeera.net/aljazeerarss/a7c186be-1baa-4bd4-9d80-a84db769f779/73d0e1b4-532f-45ef-b135-bfdff8b8cab9) -> HTTP 200 + XML صالح (25 خبراً).
#   - BBC Arabic - اليمن عبر Google News (https://news.google.com/rss/search?q=site:bbc.com/arabic+%D8%A7%D9%84%D9%8A%D9%85%D9%86&hl=ar&gl=YE&ceid=YE:ar) -> HTTP 200 + XML صالح (100 خبر).
#
# ب) مصادر مقترحة تم اختبارها وفشلت (موثقة هنا ولم تُضف منعاً لأعطال السحب):
#   - المصدر أونلاين (https://almasdaronline.com/rss) -> فشل: ConnectionError.
#   - مأرب برس (https://marebpress.net/rss) -> فشل: ConnectionError.
#   - اليمن الآن (https://www.alyemen-now.net/feed) -> فشل: ConnectionError.
#   - عدن الغد مباشر (https://adengad.net/rss) -> فشل: ConnectionError.
#   - الموقع بوست مباشر (https://almawqea.net/rss) -> فشل: HTTP 200 لكن المحتوى HTML وليس XML صالحاً (items=0).
#   - المشهد اليمني مباشر (https://almashhad-alyemeni.com/rss) -> فشل: ConnectionError.
#   - UKMTO (https://www.ukmto.org/feed) -> فشل: HTTP 404.
#   - Dryad Global (https://dryadglobal.com/feed) -> فشل: HTTP 404.
#   - BIMCO (https://www.bimco.org/news/rss) -> فشل: ConnectionError.
#   - OCHA Yemen (https://www.unocha.org/yemen/rss.xml) -> فشل: HTTP 406.
#   - UNHCR Yemen (https://www.unhcr.org/rss/yemen.xml) -> فشل: HTTP 403.
#   - WHO Yemen (https://www.emro.who.int/index.php?option=com_obrss&task=feed&id=1&format=feed) -> فشل: HTTP 200 لكن XML غير صالح (items=0).
#   - العربية - اليمن (https://www.alarabiya.net/rss/arab-and-world/yemen.xml) -> فشل: ConnectionError.
#
# ج) أوزان الثقة المعتمدة (الخطوة 6):
#   - المصادر المباشرة (RSS أصلي): trust_score = 95
#   - المصادر عبر Google News: trust_score = 75
#   - المصادر البحرية الدولية: trust_score = 70 (مع تطبيق فلتر MARITIME_REGION)
# ==============================================================================

RSS_SOURCES: List[Dict[str, Any]] = [
    # --- أولاً: المصادر المباشرة الأصلية (trust_score = 95) ---
    {
        "name": "يمن شباب نت (RSS مباشر)",
        "url": "https://yemenshabab.net/rss",
        "category_hint": "يمني مباشر",
        "source_type": "RSS يمني مباشر",
        "trust_score": 95,
        "language": "ar",
        "enabled": True,
    },
    {
        "name": "مرصد الشؤون الإنسانية في اليمن (ReliefWeb)",
        "url": "https://reliefweb.int/updates/rss.xml?advanced-search=%28PC255%29",
        "category_hint": "إغاثي/تجاري",
        "source_type": "RSS أممي مباشر",
        "trust_score": 95,
        "language": "en",
        "enabled": True,
    },
    {
        "name": "الجزيرة نت - اليمن (RSS مباشر)",
        "url": "https://www.aljazeera.net/aljazeerarss/a7c186be-1baa-4bd4-9d80-a84db769f779/73d0e1b4-532f-45ef-b135-bfdff8b8cab9",
        "category_hint": "إقليمي مباشر",
        "source_type": "RSS إقليمي مباشر",
        "trust_score": 90,
        "language": "ar",
        "enabled": True,
    },

    # --- ثانياً: المصادر اليمنية والإقليمية عبر Google News (trust_score = 75) ---
    {
        "name": "سبأ نت (وكالة الأنباء اليمنية)",
        "url": "https://news.google.com/rss/search?q=%D9%88%D9%83%D8%A7%D9%84%D8%A9+%D8%B3%D8%A8%D8%A3+%D8%B5%D9%86%D8%B9%D8%A7%D8%A1+%D8%B9%D8%AF%D9%86&hl=ar&gl=YE&ceid=YE:ar",
        "category_hint": "يمني رسمي",
        "source_type": "RSS (Google News)",
        "trust_score": 75,
        "language": "ar",
        "enabled": True,
    },
    {
        "name": "عدن الغد",
        "url": "https://news.google.com/rss/search?q=%D8%B9%D8%AF%D9%86+%D8%A7%D9%84%D8%BA%D8%AF+%D8%A7%D9%84%D9%8A%D9%85%D9%86&hl=ar&gl=YE&ceid=YE:ar",
        "category_hint": "يمني محلي",
        "source_type": "RSS (Google News)",
        "trust_score": 75,
        "language": "ar",
        "enabled": True,
    },
    {
        "name": "الموقع بوست",
        "url": "https://news.google.com/rss/search?q=%D8%A7%D9%84%D9%85%D9%88%D9%82%D8%B9+%D8%A8%D9%88%D8%B3%D8%AA+%D8%A7%D9%84%D9%8A%D9%85%D9%86&hl=ar&gl=YE&ceid=YE:ar",
        "category_hint": "يمني محلي",
        "source_type": "RSS (Google News)",
        "trust_score": 75,
        "language": "ar",
        "enabled": True,
    },
    {
        "name": "المشهد اليمني",
        "url": "https://news.google.com/rss/search?q=%D8%A7%D9%84%D9%85%D8%B4%D9%87%D8%AF+%D8%A7%D9%84%D9%8A%D9%85%D9%86%D9%8A&hl=ar&gl=YE&ceid=YE:ar",
        "category_hint": "يمني محلي",
        "source_type": "RSS (Google News)",
        "trust_score": 75,
        "language": "ar",
        "enabled": True,
    },
    {
        "name": "يمن مونيتور",
        "url": "https://news.google.com/rss/search?q=%D9%8A%D9%85%D9%86+%D9%85%D9%88%D9%86%D9%8A%D8%AA%D9%88%D8%B1+%D8%A7%D9%84%D9%8A%D9%85%D9%86&hl=ar&gl=YE&ceid=YE:ar",
        "category_hint": "يمني محلي",
        "source_type": "RSS (Google News)",
        "trust_score": 75,
        "language": "ar",
        "enabled": True,
    },
    {
        "name": "يمن برس وعدن حرة (تغطية المحافظات)",
        "url": "https://news.google.com/rss/search?q=%D8%B5%D9%86%D8%B9%D8%A7%D8%A1+%D8%B9%D8%AF%D9%86+%D8%A7%D9%84%D8%AD%D8%AF%D9%8A%D8%AF%D8%A9+%D9%85%D8%A3%D8%B1%D8%A8+%D8%AA%D8%B9%D8%B2+%D8%AD%D8%B6%D8%B1%D9%85%D9%88%D8%AA&hl=ar&gl=YE&ceid=YE:ar",
        "category_hint": "يمني محلي",
        "source_type": "RSS (Google News)",
        "trust_score": 75,
        "language": "ar",
        "enabled": True,
    },
    {
        "name": "BBC Arabic - اليمن",
        "url": "https://news.google.com/rss/search?q=site:bbc.com/arabic+%D8%A7%D9%84%D9%8A%D9%85%D9%86&hl=ar&gl=YE&ceid=YE:ar",
        "category_hint": "دولي/يمني",
        "source_type": "RSS (Google News)",
        "trust_score": 75,
        "language": "ar",
        "enabled": True,
    },

    # --- ثالثاً: المصادر البحرية والأمنية الدولية (trust_score = 70 + فلتر MARITIME_REGION) ---
    {
        "name": "gCaptain Maritime",
        "url": "https://gcaptain.com/feed/",
        "category_hint": "بحري",
        "source_type": "RSS بحري دولي",
        "trust_score": 70,
        "language": "en",
        "enabled": True,
    },
    {
        "name": "Splash247 Maritime",
        "url": "https://splash247.com/feed/",
        "category_hint": "بحري",
        "source_type": "RSS بحري دولي",
        "trust_score": 70,
        "language": "en",
        "enabled": True,
    },
    {
        "name": "The Maritime Executive (Red Sea & Global)",
        "url": "https://news.google.com/rss/search?q=site:maritime-executive.com+OR+UKMTO+Red+Sea&hl=en-US&gl=US&ceid=US:en",
        "category_hint": "بحري",
        "source_type": "RSS بحري دولي",
        "trust_score": 70,
        "language": "en",
        "enabled": True,
    },
    {
        "name": "USNI News",
        "url": "https://news.usni.org/feed",
        "category_hint": "أمني/بحري",
        "source_type": "RSS بحري دولي",
        "trust_score": 70,
        "language": "en",
        "enabled": True,
    },
    {
        "name": "Naval News",
        "url": "https://www.navalnews.com/feed/",
        "category_hint": "أمني/بحري",
        "source_type": "RSS بحري دولي",
        "trust_score": 70,
        "language": "en",
        "enabled": True,
    },
]
