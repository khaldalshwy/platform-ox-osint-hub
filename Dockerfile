FROM python:3.11-slim

WORKDIR /app

# إعداد متغيرات البيئة لمنع تخزين ملفات pyc وضمان إخراج السجلات مباشرة
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=7860 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# نسخ وتثبيت الاعتماديات
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# نسخ ملفات المنصة بالكامل وتفويض صلاحيات الكتابة للمستخدم السحابي (UID 1000 على HF Spaces)
COPY . .
RUN chmod -R 777 /app

EXPOSE 7860

CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]

