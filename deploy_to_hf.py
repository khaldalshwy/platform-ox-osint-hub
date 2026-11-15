# -*- coding: utf-8 -*-
"""
أداة النشر السريع إلى Hugging Face Spaces (deploy_to_hf.py)
ترفع كافة ملفات المنصة (مع استثناء الملفات الحساسة وقواعد البيانات المحلية)
إلى مساحة Hugging Face Space المحددة وتضبط الأسرار (Secrets) اختيارياً.

الاستخدام:
    python deploy_to_hf.py --token hf_xxx --repo-id username/platform-ox-osint-hub
"""

import os
import sys
import time
import argparse


def main():
    parser = argparse.ArgumentParser(description="Deploy Platform OX to Hugging Face Spaces")
    parser.add_argument("--token", required=True, help="Hugging Face Write Access Token (hf_...)")
    parser.add_argument("--repo-id", required=True, help="Space Repo ID, e.g. username/platform-ox-osint-hub")
    parser.add_argument("--turso-url", default="", help="Optional TURSO_DATABASE_URL secret")
    parser.add_argument("--turso-token", default="", help="Optional TURSO_AUTH_TOKEN secret")
    parser.add_argument("--ais-key", default="", help="Optional AISSTREAM_API_KEY secret")
    args = parser.parse_args()

    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("[!] يرجى تثبيت مكتبة huggingface_hub أولاً: pip install huggingface_hub")
        sys.exit(1)

    api = HfApi(token=args.token)
    root_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"[*] جاري إنشاء/التحقق من مساحة Hugging Face Space: {args.repo_id} ...")
    for attempt in range(5):
        try:
            api.create_repo(
                repo_id=args.repo_id,
                repo_type="space",
                space_sdk="static",
                private=False,
                exist_ok=True,
            )
            break
        except Exception as e:
            if attempt == 4:
                raise
            print(f"  [!] إعادة محاولة الاتصال بـ Hugging Face ({attempt + 1}/5): {type(e).__name__}")
            time.sleep(2)

    # إضافة الأسرار في حال تمريرها
    if args.turso_url:
        api.add_space_secret(repo_id=args.repo_id, key="TURSO_DATABASE_URL", value=args.turso_url)
    if args.turso_token:
        api.add_space_secret(repo_id=args.repo_id, key="TURSO_AUTH_TOKEN", value=args.turso_token)
    if args.ais_key:
        api.add_space_secret(repo_id=args.repo_id, key="AISSTREAM_API_KEY", value=args.ais_key)

    print("[*] جاري رفع ملفات المنصة إلى السحابة...")
    for attempt in range(5):
        try:
            api.upload_folder(
                folder_path=root_dir,
                repo_id=args.repo_id,
                repo_type="space",
                ignore_patterns=[
                    ".env",
                    "*.db",
                    "*.sqlite",
                    "*.sqlite3",
                    "__pycache__/**",
                    "*.pyc",
                    ".git/**",
                    "build/**",
                    "dist/**",
                    "*.spec",
                    "06_presentation/reporting/generated_reports/*.html",
                    "06_presentation/reporting/generated_reports/*.md",
                ],
            )
            break
        except Exception as e:
            if attempt == 4:
                raise
            print(f"  [!] إعادة محاولة رفع الملفات ({attempt + 1}/5): {type(e).__name__}")
            time.sleep(2)
    print(f"✅ تم النشر بنجاح! رابط المنصة الحي:\nhttps://huggingface.co/spaces/{args.repo_id}")


if __name__ == "__main__":
    main()

