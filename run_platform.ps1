# سكربت تشغيل منصة الرصد العلني Platform OX
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "🛡️ تشغيل غرفة العمليات المركزية - OSINT Platform OX" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Cyan

# التحقق من تثبيت بايثون
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonPath) {
    Write-Host "[!] لم يتم العثور على بايثون في بيئة النظام." -ForegroundColor Red
    Exit 1
}

# تشغيل دورة تحديث أولية
Write-Host "[*] فحص وتحديث بيانات الرصد الميداني..." -ForegroundColor Yellow
$env:PYTHONIOENCODING="utf-8"
python 04_orchestration/pipeline_runner.py

# تشغيل واجهة Streamlit
Write-Host "[*] إطلاق البوابة التفاعلية على المنفذ 8501..." -ForegroundColor Green
python -m streamlit run 06_presentation/streamlit_app/app.py --server.port=8501
