import asyncio
import requests
import time
import re
from curl_cffi.requests import AsyncSession


async def get_archive_url(session, url: str, semaphore: asyncio.Semaphore) -> str:
    """
    Prüft ob URL via Archive.ph verfügbar ist (Paywall-Bypass).
    Gibt Archive.ph URL zurück oder Original-URL wenn nicht verfügbar.
    """
    async with semaphore:
        try:
            archive_check = f"https://archive.ph/newest/{url}"
            response = await session.get(archive_check, timeout=10, allow_redirects=True)
            if response.status_code == 200 and "archive.ph" in str(response.url):
                return str(response.url)
        except:
            pass
        return url


def get_wayback_urls(query: str, brand: str, year: int = None, limit: int = 50) -> list:
    """
    Holt historische URLs von der Wayback Machine CDX API.
    Gibt Liste von (url, year) Tuples zurück.
    """
    results = []
    
    for attempt in range(3):  # 3 Versuche
        try:
            params = {
                "url": f"*{brand.lower().replace(' ', '')}*",
                "output": "json",
                "limit": limit,
                "fl": "original,timestamp",
                "filter": "statuscode:200",
                "collapse": "urlkey"
            }
            if year:
                params["from"] = f"{year}0101"
                params["to"] = f"{year}1231"
            
            resp = requests.get(
                "http://web.archive.org/cdx/search/cdx",
                params=params,
                timeout=30,  # erhöht von 15
                headers={"User-Agent": "BrandResearch/1.0"}
            )
            if resp.status_code == 200:
                data = resp.json()
                for row in data[1:]:  # Erste Zeile ist Header
                    orig_url = row[0]
                    timestamp = row[1]
                    yr = int(timestamp[:4]) if timestamp else None
                    if orig_url and not orig_url.endswith(('.jpg', '.png', '.gif', '.css', '.js')):
                        results.append((f"https://web.archive.org/web/{timestamp}/{orig_url}", yr))
                return results  # Erfolg → return
            break
        except Exception as e:
            if attempt < 2:
                time.sleep(5)
                continue
            print(f"   ⚠️ Wayback CDX Fehler nach 3 Versuchen: {e}")
    
    return results


def get_semantic_scholar_urls(query: str, limit: int = 50) -> list:
    """
    Sucht wissenschaftliche Paper via Semantic Scholar API.
    Gibt Liste von (url, year, title) Tuples zurück.
    """
    results = []
    try:
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,year,openAccessPdf,externalIds"
        }
        resp = requests.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params=params,
            timeout=15,
            headers={"User-Agent": "BrandResearch/1.0"}
        )
        if resp.status_code == 200:
            data = resp.json()
            for paper in data.get("data", []):
                year = paper.get("year")
                pdf = paper.get("openAccessPdf", {})
                if pdf and pdf.get("url"):
                    results.append((pdf["url"], year, paper.get("title", "")))
                else:
                    # Fallback: DOI oder ArXiv Link
                    ext_ids = paper.get("externalIds", {})
                    if ext_ids.get("ArXiv"):
                        url = f"https://arxiv.org/abs/{ext_ids['ArXiv']}"
                        results.append((url, year, paper.get("title", "")))
        time.sleep(0.5)  # Rate limiting
    except Exception as e:
        print(f"   ⚠️ Semantic Scholar Fehler: {e}")
    
    return results
