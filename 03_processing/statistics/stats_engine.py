from typing import List, Dict, Any
import datetime

class StatsEngine:
    """
    محرك التحليل الإحصائي والسلاسل الزمنية لمنصة OSINT Platform OX
    يحسب المتوسطات، التوزيعات النسبية، والتغيرات المفاجئة في وتيرة النشر (Surge Detection).
    """
    def __init__(self):
        pass

    def calculate_category_distribution(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        dist = {}
        for ev in events:
            cat = ev.get("event_category", "غير محدد")
            dist[cat] = dist.get(cat, 0) + 1
        return dist

    def calculate_urgency_distribution(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        dist = {"قصوى": 0, "متوسطة": 0, "روتينية": 0}
        for ev in events:
            urg = ev.get("urgency_level", "روتينية")
            if urg in dist:
                dist[urg] += 1
            else:
                dist[urg] = 1
        return dist

    def calculate_sentiment_summary(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        scores = [ev.get("sentiment_score", 0.0) for ev in events if ev.get("sentiment_score") is not None]
        if not scores:
            return {"mean": 0.0, "total": 0}
        return {
            "mean": round(sum(scores) / len(scores), 2),
            "min": min(scores),
            "max": max(scores),
            "total_analyzed": len(scores)
        }

if __name__ == "__main__":
    engine = StatsEngine()
    test_events = [
        {"event_category": "أمني", "urgency_level": "قصوى", "sentiment_score": -0.8},
        {"event_category": "بحري", "urgency_level": "متوسطة", "sentiment_score": 0.1},
        {"event_category": "أمني", "urgency_level": "قصوى", "sentiment_score": -0.5}
    ]
    print("[*] توزيع الفئات:", engine.calculate_category_distribution(test_events))
    print("[*] ملخص المشاعر:", engine.calculate_sentiment_summary(test_events))
