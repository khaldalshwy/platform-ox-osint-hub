import os
import sys
import time
import socket
import threading
import webbrowser
import requests
import streamlit.web.cli as stcli

# ضبط ترميز المخرجات لدعم اللغة العربية في نظام ويندوز
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def is_port_in_use(port: int) -> bool:
    """فحص ما إذا كان المنفذ قيد الاستخدام حالياً"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def find_free_port(start_port: int = 8501) -> int:
    """البحث التلقائي عن منفذ شاغر لتفادي أي تعارض"""
    port = start_port
    while is_port_in_use(port):
        port += 1
    return port

def open_browser_when_ready(port: int):
    """فتح المتصفح تلقائياً بمجرد تشغيل خادم المنصة"""
    url = f"http://localhost:{port}"
    for _ in range(60):
        try:
            r = requests.get(url, timeout=1)
            if r.status_code == 200:
                webbrowser.open(url)
                return
        except Exception:
            pass
        time.sleep(0.4)
    # فتح احتياطي في حال تأخر الاستجابة
    webbrowser.open(url)

def main():
    print("=" * 70)
    print("🛡️ منصة الرصد العلني الاستخباراتية — Platform OX")
    print("🚀 جاري بدء تشغيل المنظومة وغرفة العمليات المركزية...")
    print("=" * 70)

    # تحديد المسار الأساسي سواء في وضع التطوير أو كملف تنفيذي مجمع
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # إضافة كافة الطبقات لمسار بايثون
    for sub in ["00_governance", "01_acquisition", "02_storage", "03_processing", "04_orchestration", "06_presentation"]:
        p = os.path.join(base_dir, sub)
        if p not in sys.path:
            sys.path.insert(0, p)

    app_path = os.path.join(base_dir, "06_presentation", "streamlit_app", "app.py")

    target_port = 8501
    if is_port_in_use(target_port):
        try:
            r = requests.get(f"http://localhost:{target_port}", timeout=1)
            if r.status_code == 200 and ("Platform OX" in r.text or "منصة الرصد العلني" in r.text):
                print(f"[*] التطبيق يعمل بالفعل على المنفذ {target_port}، جاري توجيهك إلى المتصفح...")
                webbrowser.open(f"http://localhost:{target_port}")
                return
        except Exception:
            pass
        target_port = find_free_port(8502)

    print(f"[*] تشغيل غرفة العمليات على الرابط: http://localhost:{target_port}")

    # فتح المتصفح بالتوازي
    threading.Thread(target=open_browser_when_ready, args=(target_port,), daemon=True).start()

    # تشغيل محرك Streamlit برمجياً
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        f"--server.port={target_port}",
        "--server.headless=true",
        "--server.fileWatcherType=none",
        "--browser.serverAddress=localhost",
        "--theme.base=light"
    ]

    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
