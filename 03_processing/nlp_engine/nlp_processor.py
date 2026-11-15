import os
import sys
import re
from typing import List, Dict, Any

_PROCESSING_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROCESSING_DIR not in sys.path:
    sys.path.insert(0, _PROCESSING_DIR)

from filters.yemen_relevance_filter import match_whole_term


class NLPProcessor:
    """
    محرك معالجة اللغة الطبيعية واستخراج الكيانات (NER) لمنصة OSINT Platform OX
    يدعم تنظيف النصوص العربية، وتحديد الأشخاص والمنظمات والأماكن والسفن والأسلحة
    باستخدام مطابقة الكلمة الكاملة (Word Boundary) لمنع التداخل اللفظي.
    """
    def __init__(self):
        # قواميس الكيانات المرجعية الموسعة مرتبة من الأدق إلى الأعم
        self.locations_lexicon = [
            "ميناء الحديدة", "ميناء عدن", "ميناء الصليف", "ميناء رأس عيسى",
            "ميناء المخا", "ميناء المكلا", "ميناء نشطون", "ميناء بير علي",
            "مضيق باب المندب", "باب المندب", "صنعاء", "عدن", "الحديدة", "المكلا",
            "تعز", "مأرب", "خليج عدن", "سقطرى", "ميون", "حنيش", "الصليف",
            "رأس عيسى", "المخا", "الخوخة", "نشطون", "بير علي", "بلحاف", "الشحر",
            "الغيضة", "لحج", "أبين", "شبوة", "حضرموت", "صعدة", "حجة", "ذمار",
            "إب", "البيضاء", "الجوف", "عمران", "الضالع", "المحويت", "ريمة",
            "سيئون", "المهرة", "البحر الأحمر", "اليمن"
        ]
        self.orgs_lexicon = [
            "حكومة صنعاء", "الحكومة الشرعية", "المجلس الرئاسي", "أنصار الله",
            "الحوثيون", "القوات المسلحة اليمنية", "التحالف العربي",
            "الأمم المتحدة", "مجلس الأمن", "هيئة التجارة البحرية البريطانية", "UKMTO",
            "التحالف الدولي", "سنتكوم", "CENTCOM", "خفر السواحل", "مؤسسة موانئ البحر الأحمر",
            "المنظمة البحرية الدولية", "IMO", "أسبيدس", "Aspides", "برنامج الغذاء العالمي",
            "WFP", "الصليب الأحمر", "الهلال الأحمر", "حارس الازدهار", "Prosperity Guardian",
            "ميرسك", "Maersk", "إم إس سي", "MSC", "سي إم إيه", "CMA CGM", "هاباج لويد",
            "UNMHA", "OCHA Yemen"
        ]
        self.vessels_lexicon = [
            "ناقلة نفط", "سفينة حاويات", "سفينة بضائع", "زورق حربي", "فرقاطة",
            "مدمرة", "قارب صيد", "سفينة تجارية", "جلاكسي ليدر", "روبيمار",
            "سوسن", "ناقلة كيماويات", "ناقلة غاز", "سفينة سائبة", "قاطرة بحرية",
            "حاملة طائرات", "بارجة", "طراد"
        ]
        self.weapons_lexicon = [
            "صاروخ باليستي", "صاروخ كروز", "طائرة مسيرة", "مسيرة بحرية", "لغم بحري",
            "مدفعية", "زورق مفخخ", "مضاد للسفن", "دفاع جوي", "تشويش إلكتروني",
            "مقذوف", "عبوة ناسفة"
        ]

    def clean_arabic_text(self, text: str) -> str:
        """تنظيف النص وإزالة الروابط وعلامات التشكيل وتوحيد الحروف"""
        if not text:
            return ""
        text = re.sub(r'http\S+|www\S+', '', text)
        text = re.sub(r'[\u064B-\u0652\u0640]', '', text)
        text = re.sub(r'[إأآ]', 'ا', text)
        text = re.sub(r'ة\b', 'ه', text)
        text = re.sub(r'ى\b', 'ي', text)
        text = re.sub(r'[^\w\s\.\,\u0600-\u06FF]', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """استخراج الكيانات المسماة وتصنيفها بدقة باستخدام حدود الكلمة الكاملة"""
        entities = []
        if not text:
            return entities
        seen = set()

        # رصد المواقع بحدود الكلمة الكاملة لمنع مطابقة 'عدن' داخل 'معدن' أو 'تعز' داخل 'تعزيز'
        for loc in self.locations_lexicon:
            if loc not in seen and match_whole_term(text, loc):
                seen.add(loc)
                entities.append({"text": loc, "type": "LOCATION", "confidence": 0.95})

        # رصد المنظمات
        for org in self.orgs_lexicon:
            if org not in seen and match_whole_term(text, org):
                seen.add(org)
                entities.append({"text": org, "type": "ORGANIZATION", "confidence": 0.92})

        # رصد السفن والقطع البحرية
        for ves in self.vessels_lexicon:
            if ves not in seen and match_whole_term(text, ves):
                seen.add(ves)
                entities.append({"text": ves, "type": "VESSEL", "confidence": 0.90})

        # رصد الأسلحة والمنظومات
        for wpn in self.weapons_lexicon:
            if wpn not in seen and match_whole_term(text, wpn):
                seen.add(wpn)
                entities.append({"text": wpn, "type": "WEAPON_SYSTEM", "confidence": 0.94})

        return entities

    def summarize_text(self, text: str, max_sentences: int = 2) -> str:
        """تلخيص النص واستخلاص الجمل الجوهرية"""
        if not text:
            return ""
        sentences = [s.strip() for s in re.split(r'[\.\n\r]+', text) if len(s.strip()) > 15]
        return " | ".join(sentences[:max_sentences])


if __name__ == "__main__":
    nlp = NLPProcessor()
    sample = "أعلنت هيئة التجارة البحرية البريطانية UKMTO وشركة ميرسك عن عبور سفينة حاويات بسلام في البحر الأحمر قبالة ميناء الحديدة ومضيق باب المندب."
    ents = nlp.extract_entities(sample)
    print(f"[*] الكيانات المستخرجة ({len(ents)}): {ents}")
