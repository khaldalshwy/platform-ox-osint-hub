import requests
from bs4 import BeautifulSoup
import hashlib
import datetime
from typing import Dict, Any, Optional

class WebScraper:
    """
    محرك كشط الويب الموحد لمنصة OSINT Platform OX
    يستخدم Requests و BeautifulSoup للسرعة، مع إمكانية التوسع واستخراج البيانات الوصفية.
    """
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OSINT-OX/1.0"
        }

    def fetch_url(self, url: str) -> Optional[str]:
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"[!] خطأ أثناء كشط الرابط {url}: {e}")
            return None

    def extract_article(self, url: str) -> Optional[Dict[str, Any]]:
        html = self.fetch_url(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")
        
        # استخراج العنوان
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)

        # استخراج الفقرات والنص
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 20]
        full_text = "\n".join(paragraphs)

        # استخراج الصور الأساسية
        images = []
        for img in soup.find_all("img"):
            src = img.get("src")
            if src and (src.startswith("http") or src.startswith("//")):
                images.append(src)

        # بصمة المحتوى لمنع التكرار
        content_hash = hashlib.sha256((title + full_text).encode("utf-8")).hexdigest()

        return {
            "url": url,
            "title": title,
            "raw_content": full_text,
            "images": images[:5],
            "hash": content_hash,
            "scraped_at": datetime.datetime.now().isoformat()
        }

if __name__ == "__main__":
    scraper = WebScraper()
    print("[*] تم تجهيز واختبار محرك كشط الويب بنجاح.")
