import os
import sys
from typing import Dict, Any, Optional

# ضمان إمكانية استيراد فلتر الصلة اليمنية من داخل طبقة المعالجة
_PROCESSING_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROCESSING_DIR not in sys.path:
    sys.path.insert(0, _PROCESSING_DIR)

from filters.yemen_relevance_filter import is_yemen_relevant, extract_yemen_location, match_whole_term, _clean_html_and_urls


def _raw_classify_category(title: str, summary: str = "", text: str = "") -> str:
    """
    دالة التصنيف الأساسي للأخبار إلى الأقسام الأربعة المعتمدة:
    (بحري، إغاثي/تجاري، أمني/عسكري، سياسي/عام)
    مع استخدام مطابقة الكلمة الكاملة لمنع التداخل اللفظي (مثل 'البحرين' مع 'بحري' أو 'القناة الناقلة' مع 'ناقلة').
    """
    full_text = _clean_html_and_urls(f"{title or ''} {summary or ''} {text or ''}")
    # استبعاد عبارة البث التلفزيوني الرياضي (القناة الناقلة / القنوات الناقلة) من مطابقة سفن الناقلات
    text_for_maritime = full_text.replace("القناة الناقلة", " ").replace("القنوات الناقلة", " ")

    maritime_terms = [
        "بحري", "بحرية", "سفينة", "سفن", "ناقلة", "ناقلات", "ميناء", "موانئ",
        "باب المندب", "مندب", "قارب", "زورق", "ملاحة", "الملاحة", "فرقاطة", "باخرة",
        "ship", "vessel", "tanker", "maritime", "shipping", "port", "seafarer",
        "cargo ship", "bab el-mandeb", "ukmto", "aspides"
    ]
    relief_terms = [
        "قمح", "إغاثة", "إغاثية", "مساعدات", "شحنة غذاء", "برنامج الأغذية",
        "تفريغ", "بضائع", "شحنة مساعدات", "حاويات", "تموينية",
        "humanitarian", "relief", "food aid", "wfp", "unicef", "ocha"
    ]
    security_terms = [
        "صاروخ", "صواريخ", "مسيرة", "مسيرات", "غارة", "غارات", "استهداف",
        "وزارة الدفاع", "دفاع جوي", "الدفاعات الجوية",
        "الجيش اليمني", "الجيش الوطني", "قوات الجيش",
        "قصف", "اشتباك", "اشتباكات", "عسكري", "عسكرية",
        "missile", "drone", "naval", "navy", "frigate", "destroyer",
        "airstrike", "military", "defense", "usni"
    ]

    if any(match_whole_term(text_for_maritime, w) for w in maritime_terms):
        return "بحري"
    elif any(match_whole_term(full_text, w) for w in relief_terms):
        return "إغاثي/تجاري"
    elif any(match_whole_term(full_text, w) for w in security_terms):
        return "أمني/عسكري"
    else:
        return "سياسي/عام"


def classify_event(
    title: str,
    summary: str = "",
    text: str = "",
    forced_category: Optional[str] = None
) -> Dict[str, Any]:
    """
    تصنيف الخبر وتطبيق فلتر الصلة اليمنية على قسم 'سياسي/عام' فقط،
    بينما تمر الأقسام الثلاثة الأخرى (بحري، أمني/عسكري، إغاثي/تجاري) كما هي بدون أي فلترة.
    """
    classification = forced_category if forced_category else _raw_classify_category(title, summary, text)
    combined_summary = f"{summary or ''} {text or ''}".strip()
    real_location = extract_yemen_location(title, combined_summary)

    # تطبيق الفلتر فقط على قسم "سياسي/عام"
    if classification == "سياسي/عام":
        relevance = is_yemen_relevant(title, combined_summary)

        if not relevance.accepted:
            # خبر سياسي عام لكنه لا يخص اليمن -> رفض
            return {
                "category": "سياسي/عام",
                "accepted": False,
                "rejection_reason": relevance.reason,
                "matched_exclude": ", ".join(relevance.matched_entities) if relevance.matched_entities else None,
                "relevance_score": relevance.score,
                "location_name": None,
            }

        # مقبول — أضف درجة الصلة والموقع اليمني الحقيقي المستخرج
        return {
            "category": "سياسي/عام",
            "accepted": True,
            "relevance_score": relevance.score,
            "rejection_reason": None,
            "matched_exclude": None,
            "location_name": real_location or "اليمن",
        }

    # الأقسام الثلاثة الأخرى (بحري، أمني/عسكري، إغاثي/تجاري) تمر كما هي بدون أي فلترة
    return {
        "category": classification,
        "accepted": True,
        "relevance_score": 100,
        "rejection_reason": None,
        "location_name": real_location or "غير محدد",
    }


class SentimentAnalyzer:
    """
    محرك تحليل المشاعر والنبرة ومؤشر التهديد الاستخباراتي لمنصة OSINT Platform OX
    يقيس القطبية (Polarity) ومستوى التوتر والحدة اللفظية واحتمالية الشائعات في المنشورات والأخبار،
    ويدمج التصنيف الرباعي مع فلتر الصلة اليمنية لقسم 'سياسي/عام' ومعالجة عبارات النفي.
    """
    NEGATION_PHRASES = {
        "لا صحة", "نفي", "نفى", "فشل", "إحباط", "أحبط", "دون إصابات",
        "بدون خسائر", "لم يقع", "لم يسفر", "لم يتسبب", "لم ينجح",
        "لم يتمكن", "لم يستهدف", "لم يسقط", "لم يصب", "لم يقتل",
        "لم يضر", "لم يؤثر", "لم يحدث", "لم يشهد", "لم يسجل",
        "لم يعلن", "لم يتبن", "لم يعترف", "لم يؤكد", "لم ينف",
        "لم يشر", "لم يذكر", "لم يوضح", "لم يبين", "لم يحدد",
        "لم يكشف", "لم يصرح"
    }

    def __init__(self):
        # معجم الكلمات السلبية وعالية التوتر + المصطلحات الاقتصادية السلبية
        self.negative_keywords = [
            "استهداف", "هجوم", "انفجار", "غرق", "أزمة", "خطر", "توتر", "حرب",
            "كارثة", "اعتداء", "تدمير", "مقتل", "إصابة", "خسائر", "تهديد", "حصار",
            "صاروخ", "مسيرة", "قصف", "اشتباك", "اعتراض", "تعطيل", "إصابة مباشرة",
            "طوارئ", "تأهب", "اشتباه",
            # مصطلحات اقتصادية ومعيشية حرجة (التحسين 1.2)
            "تضخم", "انهيار العملة", "انهيار الريال", "توقف الصادرات", "نقص الوقود",
            "أزمة وقود", "نقص الغذاء", "مجاعة", "غلاء", "ارتفاع الأسعار", "تدهور",
            "انقطاع الكهرباء", "توقف الرواتب", "أزمة سيولة", "إغلاق الميناء"
        ]
        # معجم الكلمات الإيجابية والمطمئنة + الاقتصادية الإيجابية
        self.positive_keywords = [
            "سلام", "أمان", "استقرار", "افتتاح", "تفريغ", "إغاثة", "إنقاذ", "نجاح",
            "تنسيق", "وصول آمن", "تسهيل", "ازدهار", "تنمية", "اتفاق", "هدوء",
            "تعافي", "سلاسة", "استئناف", "حماية", "مرافقة آمنة",
            # مصطلحات اقتصادية وملاحية إيجابية (التحسين 1.3)
            "تعزيز الاحتياطي", "تدفق البضائع", "افتتاح ميناء", "استئناف الصادرات",
            "استقرار العملة", "تحسن اقتصادي", "وصول شحنة", "تفريغ حمولة", "تشغيل رحلة"
        ]
        # مؤشرات الشائعات والتحريض
        self.rumor_indicators = [
            "مصادر غير مؤكدة", "أنباء متضاربة", "تسريبات سرية", "عاجل وهام جدا",
            "لم يتسن التأكد", "مصدر مجهول", "شائعات", "يقال"
        ]

    @staticmethod
    def classify_event(title: str, summary: str = "", text: str = "", forced_category: Optional[str] = None) -> Dict[str, Any]:
        return classify_event(title=title, summary=summary, text=text, forced_category=forced_category)

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """احتساب درجة القطبية ومؤشر التوتر والتهديد بحدود الكلمة الكاملة ومعالجة النفي"""
        if not text:
            return {
                "score": 0.0,
                "label": "محايد",
                "tension_level": "منخفض",
                "threat_index": 10,
                "rumor_risk": "منخفض",
                "neg_hits": 0,
                "pos_hits": 0,
                "negated": False,
            }

        neg_count = sum(1 for word in self.negative_keywords if match_whole_term(text, word))
        pos_count = sum(1 for word in self.positive_keywords if match_whole_term(text, word))
        rumor_count = sum(1 for word in self.rumor_indicators if match_whole_term(text, word))

        has_negation = any(match_whole_term(text, phr) for phr in self.NEGATION_PHRASES)
        if has_negation and neg_count > 0:
            # عند وجود نفي أو إحباط ("لا صحة لاستهداف سفينة")، نخفّض الكلمات السلبية بمقدار 50% (أو نتجاهل كلمة واحدة)
            neg_count = max(0, (neg_count - 1) if neg_count <= 2 else (neg_count // 2))

        total = neg_count + pos_count

        if total == 0:
            score = 0.0
            label = "محايد"
            tension = "منخفض"
            threat_index = 20
        else:
            score = (pos_count - neg_count) / total
            if score < -0.2:
                label = "سلبي (توتر مرتفع)"
                tension = "قصوى" if neg_count >= 3 else "متوسط"
                threat_index = min(95, 40 + (neg_count * 15))
            elif score > 0.2:
                label = "إيجابي"
                tension = "منخفض"
                threat_index = max(10, 30 - (pos_count * 5))
            else:
                label = "محايد / متوازن"
                tension = "متوسط" if neg_count > 0 else "منخفض"
                threat_index = 35 + (neg_count * 8)

        rumor_risk = "مرتفع" if rumor_count >= 2 else ("متوسط" if rumor_count == 1 else "منخفض")

        return {
            "score": round(score, 2),
            "label": label,
            "tension_level": tension,
            "threat_index": int(threat_index),
            "rumor_risk": rumor_risk,
            "neg_hits": neg_count,
            "pos_hits": pos_count,
            "negated": has_negation,
        }


if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    res1 = analyzer.analyze_sentiment("استهداف وتصاعد التوتر وهجوم بطائرة مسيرة يهدد حركة الملاحة.")
    res2 = analyzer.analyze_sentiment("وصول سفينة تجارية بسلام وتفريغ حمولات القمح والإغاثة في الميناء.")
    print("[*] فحص المشاعر والتهديد 1:", res1)
    print("[*] فحص المشاعر والتهديد 2:", res2)
