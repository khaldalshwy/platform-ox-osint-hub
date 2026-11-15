import re
import datetime
from typing import List, Dict, Any

class SocialListener:
    """
    محرك الاستماع الاجتماعي لمنصة OSINT Platform OX
    يرصد الكلمات المفتاحية، يحسب وتيرة التفاعل، ويكتشف المؤشرات المبكرة للشائعات.
    """
    def __init__(self):
        # الكلمات الدلالية ومؤشرات الإنذار المبكر
        self.watch_keywords = [
            "باب المندب", "البحر الأحمر", "سفينة", "استهداف", "صاروخ",
            "طائرة مسيرة", "ميناء الحديدة", "ميناء عدن", "غرق", "إنقاذ", "شائعة"
        ]

    def scan_social_stream(self, raw_posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """مسح وتصنيف المنشورات وتحديد درجة الأهمية"""
        processed_posts = []
        for post in raw_posts:
            text = post.get("text", "")
            matched_keywords = [kw for kw in self.watch_keywords if kw in text]
            
            # احتساب مؤشر الأهمية بناء على عدد الكلمات الحساسة
            urgency = "روتينية"
            if any(k in text for k in ["استهداف", "غرق", "انفجار", "صاروخ"]):
                urgency = "قصوى"
            elif matched_keywords:
                urgency = "متوسطة"

            processed_posts.append({
                "author": post.get("author", "حساب غير محدد"),
                "text": text,
                "platform": post.get("platform", "وسائل التواصل"),
                "matched_keywords": matched_keywords,
                "urgency": urgency,
                "timestamp": post.get("timestamp", datetime.datetime.now().isoformat())
            })
        return processed_posts

if __name__ == "__main__":
    listener = SocialListener()
    sample = [
        {"author": "@MarineObserver", "text": "أنباء عن اقتراب زورق مجهول من ناقلة بضائع غرب مضيق باب المندب.", "platform": "Twitter/X"},
        {"author": "قناة الميدان", "text": "هدوء ملاحي تام وحركة طبيعية في موانئ البحر الأحمر اليوم.", "platform": "Telegram"}
    ]
    results = listener.scan_social_stream(sample)
    print(f"[*] تم تحليل {len(results)} منشوراً عبر محرك الاستماع الاجتماعي.")
