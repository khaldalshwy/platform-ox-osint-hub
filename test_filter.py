import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for sub in ["01_acquisition", "02_storage", "03_processing", "04_orchestration", "06_presentation"]:
    p = os.path.join(BASE_DIR, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

from filters.yemen_relevance_filter import is_yemen_relevant, extract_yemen_location, match_whole_term
from sentiment.sentiment_analyzer import classify_event
from database import db


def run_all_tests():
    print("=" * 75)
    print("🧪 بدء الاختبار الإلزامي لفلتر الصلة اليمنية (المرحلة 1 — الخطوة 1.4)")
    print("=" * 75)

    # 1. حالات الرفض الإلزامي (يجب أن تكون False)
    mandatory_reject_cases = [
        ("أحمد السقا يرفض اعتذار هشام سليمان", "فن"),
        ("رحمة حسن تترك الفن للعمل بفندق بالقاهرة", "فن+مصر"),
        ("فؤادة وإثيوبيا بمهرجان القاهرة السينمائي", "فن"),
        ("جنسن هوانغ ضلل قادة إنفيديا", "تقنية"),
        ("مهرجان البحر الأحمر السينمائي بجدة", "فن+غير يمني"),
        ("الأهلي يفوز على الزمالك", "رياضة"),
    ]

    print("\n[1] اختبار حالات الرفض الإلزامي (Mandatory Reject Cases):")
    for title, desc in mandatory_reject_cases:
        res_filter = is_yemen_relevant(title, "")
        res_class = classify_event(title, "", title)
        assert res_filter.accepted is False, f"فشل في رفض: {title} -> {res_filter}"
        assert res_class["accepted"] is False, f"فشل في رفض التصنيف: {title} -> {res_class}"
        print(f"  ❌ REJECT بنجاح [{desc}]: '{title}' | السبب: {res_filter.reason} | الدرجة: {res_filter.score}")

    # 2. حالات القبول الإلزامي (يجب أن تكون True)
    mandatory_accept_cases = [
        ("هجوم على سفينة قرب باب المندب", "يمني+بحري"),
        ("حكومة صنعاء تعلن...", "يمني صريح"),
        ("أسعار النفط ترتفع بعد توتر البحر الأحمر", "سياق يمني"),
        ("مصرع 3 يمنيين في حادث", "يمني"),
        ("أنصار الله تعلن استهداف سفينة", "يمني صريح"),
        ("المبعوث الأممي إلى اليمن يصل صنعاء", "يمني"),
        ("ميناء الحديدة يستقبل شحنة مساعدات", "يمني+بحري"),
        ("تعز: مقتل مدنيين في اشتباكات", "يمني+أمني"),
    ]

    print("\n[2] اختبار حالات القبول الإلزامي (Mandatory Accept Cases):")
    for title, desc in mandatory_accept_cases:
        res_filter = is_yemen_relevant(title, "")
        res_class = classify_event(title, "", title)
        assert res_filter.accepted is True, f"فشل في قبول: {title} -> {res_filter}"
        assert res_class["accepted"] is True, f"فشل في قبول التصنيف: {title} -> {res_class}"
        print(f"  ✅ ACCEPT بنجاح [{desc}]: '{title}' | التصنيف: {res_class['category']} | الدرجة: {res_filter.score} | الموقع: {res_class['location_name']}")

    # 3. اختبار عدم تأثر الأقسام الثلاثة الأخرى إطلاقاً (بحري، أمني/عسكري، إغاثي/تجاري)
    other_categories_cases = [
        ("عبور ناقلة تجارية في الممر الملاحي الدولي", "بحري"),
        ("منظومة دفاع جوي تعترض طائرة مسيرة", "أمني/عسكري"),
        ("تفريغ شحنة قمح ومساعدات إغاثية عاجلة", "إغاثي/تجاري"),
    ]

    print("\n[3] اختبار مرور الأقسام الثلاثة الأخرى بدون أي فلترة:")
    for title, expected_cat in other_categories_cases:
        res_class = classify_event(title, "", title)
        assert res_class["category"] == expected_cat, f"تغير التصنيف خطأً: {res_class}"
        assert res_class["accepted"] is True, f"تمت فلترة قسم غير سياسي/عام خطأً: {res_class}"
        assert res_class["relevance_score"] == 100
        print(f"  ⚪ PASS بدون فلترة [{res_class['category']}]: '{title}' -> accepted={res_class['accepted']}")

    # 4. اختبار دقة حدود الكلمة الكاملة (Word Boundary) وعدم مطابقة 'عدن' داخل 'معدن' أو 'تعز' داخل 'تعزيز'
    print("\n[4] اختبار حدود الكلمة الكاملة (Word Boundary) واستخراج الموقع الحقيقي:")
    assert match_whole_term("ارتفاع أسعار معدن الذهب عالمياً", "عدن") is False, "خطأ: طابق عدن داخل معدن!"
    assert match_whole_term("خطة لتعزيز التعاون الاقتصادي", "تعز") is False, "خطأ: طابق تعز داخل تعزيز!"
    assert is_yemen_relevant("ارتفاع أسعار معدن الذهب عالمياً", "").accepted is False
    assert is_yemen_relevant("خطة لتعزيز التعاون الاقتصادي", "").accepted is False
    assert extract_yemen_location("مهرجان البحر الأحمر السينمائي بجدة", "") is None
    assert extract_yemen_location("ميناء الحديدة يستقبل شحنة مساعدات", "") == "ميناء الحديدة"
    assert extract_yemen_location("هجوم على سفينة قرب باب المندب", "") == "باب المندب"
    print("  ✓ نجح اختبار عدم مطابقة 'عدن' داخل 'معدن' و'تعز' داخل 'تعزيز'!")
    print("  ✓ نجح اختبار عدم إسناد 'البحر الأحمر' تلقائياً إلا في سياق يمني/بحري حقيقي!")

    # 5. اختبار جدول rejected_news في SQLite
    print("\n[5] اختبار الحفظ في جدول rejected_news في قاعدة البيانات:")
    rej_id = db.save_rejected_news(
        title="أحمد السقا يرفض اعتذار هشام سليمان",
        summary="خبر فني ترفيهي لا علاقة له باليمن",
        url="https://example.com/art-news",
        reason="excluded_entity",
        score=0,
    )
    rejected_rows = db.get_rejected_news(limit=5)
    assert rej_id > 0 and len(rejected_rows) > 0, "فشل الحفظ في جدول rejected_news!"
    print(f"  ✓ تم حفظ الخبر المرفوض في جدول rejected_news بنجاح (ID: #{rej_id}).")

    print("\n" + "=" * 75)
    print("🎉 نجحت جميع الاختبارات الإلزامية (100%) بدون أي أخطاء!")
    print("=" * 75)


if __name__ == "__main__":
    run_all_tests()

