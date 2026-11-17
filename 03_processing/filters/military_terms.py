# -*- coding: utf-8 -*-
"""
قاموس المصطلحات العسكرية والميدانية الموسع (03_processing/filters/military_terms.py)
يضم 6 فئات ثنائية اللغة (عربي + إنجليزي) لرصد التغيرات الميدانية:
  1. ADVANCES (التقدمات)
  2. CLEARING (التطهير والتمشيط)
  3. WITHDRAWALS (الانسحابات)
  4. COLLAPSES (السقوط والانهيار)
  5. FAILURES (الإخفاقات والصد)
  6. FIELD_INDICATORS (المؤشرات الميدانية)
"""

from typing import Dict, List

MILITARY_FIELD_TERMS: Dict[str, Dict[str, List[str]]] = {
    "ADVANCES": {
        "ar": [
            "تقدم ميداني", "سيطرة نارية", "بسط السيطرة", "إحكام السيطرة",
            "استعادة مواقع", "تحرير مناطق", "توغل عسكري", "اختراق خطوط الدفاع",
            "فتح جبهة جديدة", "السيطرة على تبة", "السيطرة على تلال",
            "قطع خطوط الإمداد", "تطويق", "حصار محكم", "زحف عسكري",
            "تقدم متسارع", "تقدمت القوات", "أحكمت السيطرة",
        ],
        "en": [
            "territorial gains", "military advance", "seized control",
            "captured positions", "ground incursion", "breached defenses",
            "cut off supply lines", "encirclement", "strategic hilltop",
        ],
    },
    "CLEARING": {
        "ar": [
            "تطهير مواقع", "تمشيط المنطقة", "تأمين الخطوط الأمامية",
            "نزع الألغام", "ملاحقة الفلول", "تنظيف الجيوب",
            "تثبيت نقاط التمركز", "إغلاق المنافذ",
        ],
        "en": [
            "clearing operations", "mopping-up", "securing areas",
            "demining", "pockets of resistance", "consolidating positions",
        ],
    },
    "WITHDRAWALS": {
        "ar": [
            "انسحاب تكتيكي", "تراجع ميداني", "إعادة تموضع",
            "إخلاء مواقع", "انسحاب مفاجئ", "تراجع تحت الضغط",
            "فقدان السيطرة", "انحسار النفوذ", "ترك المواقع",
            "فك الارتباط",
        ],
        "en": [
            "tactical withdrawal", "retreat", "redeployment",
            "evacuated positions", "pulled back", "lost ground",
            "ceded territory",
        ],
    },
    "COLLAPSES": {
        "ar": [
            "سقوط جبهة", "انهيار دفاعات", "انهيار متسارع",
            "سقوط مدوٍ", "انكسار عسكري", "تهاوي التحصينات",
            "فرار جماعي", "استسلام مواقع", "فقدان خط الدفاع الأول",
            "سقوط مديرية", "سقوط معسكر",
        ],
        "en": [
            "collapse of frontlines", "fall of district",
            "defenses crumbled", "rout", "mass surrender",
            "overran base", "frontline breach",
        ],
    },
    "FAILURES": {
        "ar": [
            "كسر زحف", "صد هجوم", "إفشال محاولة تسلل",
            "إخفاق عسكري", "فشل الهجوم", "كمين محكم",
            "استدراج القوات", "تكبيد خسائر فادحة", "إجهاض عملية",
            "ارتداد عكسي", "هجوم مضاد", "استنزاف",
        ],
        "en": [
            "repelled offensive", "foiled infiltration", "failed assault",
            "ambush", "counter-offensive", "heavy casualties",
            "bogged down", "stalled advance",
        ],
    },
    "FIELD_INDICATORS": {
        "ar": [
            "اغتنام آليات", "السيطرة على مخازن أسلحة", "أسرى",
            "جثث في أرض المعركة", "تغيير خارطة السيطرة",
            "تقدم كيلومترات", "الوصول إلى مشارف", "تحرير أسرى",
        ],
        "en": [
            "seized weapons", "captured armored vehicles",
            "prisoners of war", "POWs", "outskirts of",
            "shifting frontlines", "kilometers advanced",
        ],
    },
}

MILITARY_TERMS = MILITARY_FIELD_TERMS


def get_all_military_field_keywords() -> List[str]:
    """إرجاع قائمة موحدة بدون تكرار لكافة المصطلحات العسكرية الميدانية (عربي + إنجليزي)."""
    seen = set()
    result: List[str] = []
    for cat_data in MILITARY_FIELD_TERMS.values():
        for lang in ("ar", "en"):
            for term in cat_data.get(lang, []):
                if term not in seen:
                    seen.add(term)
                    result.append(term)
    return result
