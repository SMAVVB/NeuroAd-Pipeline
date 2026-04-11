import os
import sys
import time
import re
from curl_cffi import requests as curl_requests
from lxml import html as lxml_html

def extract_clean_text(html_bytes: bytes) -> str:
    if html_bytes.startswith(b'%PDF'): return ""
    try:
        tree = lxml_html.fromstring(html_bytes)
        for bad in tree.xpath('//script | //style | //noscript | //header | //footer | //nav'):
            bad.getparent().remove(bad)
        clean_text = tree.text_content()
        return re.sub(r'\s+', ' ', clean_text).strip()
    except:
        return ""

def run_mass_scraper(urls: list, save_dir: str):
    """Sammelt Webseiten extrem schnell, OHNE LLM Flaschenhals."""
    print(f"\n🕷️ [PHASE 3] Starte Mass-Scraping (Data Lake Building)...")
    
    urls_to_crawl = list(set(urls))
    
    for idx, url in enumerate(urls_to_crawl):
        print(f"   ⬇️ [{idx+1}/{len(urls_to_crawl)}] Lade Text von: {url}")
        try:
            response = curl_requests.get(url, impersonate="chrome110", timeout=10)
            text_content = extract_clean_text(response.content)[:60000] 
            
            if len(text_content) < 200:
                continue
            
            safe_name = re.sub(r'[^a-zA-Z0-9]', '_', url)[-30:]
            with open(os.path.join(save_dir, f"url_{idx+1}_{safe_name}.txt"), "w", encoding="utf-8") as f:
                f.write(f"URL: {url}\n\n{text_content}")
                
        except Exception:
            pass
        time.sleep(1) # Kurze Anti-Ban Pause
