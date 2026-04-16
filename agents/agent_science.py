# agents/agent_science.py
import requests
import time
import re
import sys
import os
from urllib.parse import urlencode

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_core import search_searxng

SEMANTIC_SCHOLAR_BASE = "https://api.semanticscholar.org/graph/v1"
HEADERS = {"User-Agent": "BrandResearch/1.0"}


def search_papers(query: str, limit: int = 100, year_start: int = None, year_end: int = None) -> list:
    """
    Sucht Paper via Semantic Scholar API.
    Gibt Liste von paper dicts zurück.
    """
    params = {
        "query": query,
        "limit": limit,
        "fields": "paperId,title,year,openAccessPdf,externalIds,references,citationCount"
    }
    if year_start:
        params["year"] = f"{year_start}-{year_end or 2026}"
    
    try:
        resp = requests.get(f"{SEMANTIC_SCHOLAR_BASE}/paper/search",
                           params=params, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("data", [])
        time.sleep(1)
    except Exception as e:
        print(f"   ⚠️ Semantic Scholar Fehler: {e}")
    return []


def get_paper_references(paper_id: str, limit: int = 50) -> list:
    """Holt Referenzen eines Papers (Referenz-Crawler)."""
    try:
        resp = requests.get(
            f"{SEMANTIC_SCHOLAR_BASE}/paper/{paper_id}/references",
            params={"fields": "paperId,title,year,openAccessPdf,externalIds", "limit": limit},
            headers=HEADERS, timeout=15
        )
        if resp.status_code == 200:
            refs = resp.json().get("data", [])
            return [r.get("citedPaper", {}) for r in refs if r.get("citedPaper")]
        time.sleep(0.5)
    except:
        pass
    return []


def extract_paper_url(paper: dict) -> tuple:
    """Extrahiert die beste URL aus einem Paper-Dict. Gibt (url, year) zurück."""
    year = paper.get("year")
    
    # Open Access PDF bevorzugen
    pdf = paper.get("openAccessPdf", {})
    if pdf and pdf.get("url"):
        return pdf["url"], year
    
    # ArXiv
    ext = paper.get("externalIds", {})
    if ext.get("ArXiv"):
        return f"https://arxiv.org/abs/{ext['ArXiv']}", year
    
    # DOI
    if ext.get("DOI"):
        return f"https://doi.org/{ext['DOI']}", year
    
    # PubMed
    if ext.get("PubMed"):
        return f"https://pubmed.ncbi.nlm.nih.gov/{ext['PubMed']}/", year
    
    return None, year


def search_core_api(query: str, limit: int = 100) -> list:
    """Search CORE API for academic papers."""
    try:
        resp = requests.get(
            "https://api.core.ac.uk/v3/search/works",
            params={"q": query, "limit": limit},
            headers=HEADERS, timeout=15
        )
        if resp.status_code == 200:
            results = []
            for item in resp.json().get("results", []):
                url = item.get("downloadUrl") or item.get("sourceFulltextUrls", [None])[0]
                year = item.get("yearPublished")
                if url:
                    results.append((url, year))
            return results
    except:
        pass
    return []


def run_science_agent(brand: str, brand_profile: dict = None, max_depth: int = 3) -> dict:
    """
    Kompletter Wissenschafts-Sweep mit Referenz-Crawler.
    
    max_depth=1: Direkte Paper
    max_depth=2: Paper + ihre Referenzen (empfohlen)
    max_depth=3: Paper + Referenzen + Referenzen der Referenzen (langsam!)
    """
    print(f"\n🔬 [PHASE 2b] Starte Wissenschafts-Sweep für '{brand}'...")
    
    industry = brand_profile.get("industry", "Consumer Goods") if brand_profile else "Consumer Goods"
    sub_industries = brand_profile.get("sub_industries", []) if brand_profile else []
    competitors = brand_profile.get("key_competitors", []) if brand_profile else []
    
    # Query-Liste aufbauen (IMMER auf Englisch für API-Kompatibilität)
    industry_en_map = {
        "Lebensmittel und Getränke": "Food and Beverage",
        "Lebensmittel": "Food",
        "Getränke": "Beverage",
        "Energie": "Energy",
        "Technologie": "Technology",
        "Gesundheit": "Health",
        "Mode": "Fashion",
        "Automobil": "Automotive",
        "Finanzen": "Finance",
        "Einzelhandel": "Retail",
        "Ernährung": "Nutrition",
        "Sport": "Sports",
    }
    industry_en = industry_en_map.get(industry, industry)
    
    sub_en_map = {
        "Mahlzeitenersatz": "Meal Replacement",
        "Complete Food": "Complete Food",
        "Convenience Food": "Convenience Food",
        "Nahrungsergänzung": "Dietary Supplement",
        "Energie-Drinks": "Energy Drinks",
        "Proteinprodukte": "Protein Products",
    }
    sub_industries_en = [sub_en_map.get(s, s) for s in sub_industries]
    
    queries = [
        f"{brand} brand marketing",
        f"{brand} consumer behavior",
        f"{brand} market analysis",
        f"{industry_en} consumer research",
        f"{industry_en} brand loyalty",
        f"{industry_en} market trends",
        f"{industry_en} purchase intention",
        f"{industry_en} social media marketing",
    ]
    
    for sub in sub_industries_en[:3]:
        queries.append(f"{sub} nutrition study")
        queries.append(f"{sub} consumer preference")
        queries.append(f"{sub} health effects")
        queries.append(f"{sub} market growth")
    
    for comp in competitors[:3]:
        queries.append(f"{brand} vs {comp}")
        queries.append(f"{comp} consumer satisfaction")
    
    all_paper_urls = {}  # url → year
    processed_ids = set()
    
    print(f"   📚 {len(queries)} Such-Queries für {len(queries)} Themen...")
    
    # Depth 1: Direkte Suche
    depth1_papers = []
    for query in queries:
        papers = search_papers(query, limit=100)
        depth1_papers.extend(papers)
        print(f"      '{query[:40]}': {len(papers)} Paper")
        time.sleep(0.3)
    
    # URLs extrahieren und Depth 2 vorbereiten
    for paper in depth1_papers:
        pid = paper.get("paperId")
        if not pid or pid in processed_ids:
            continue
        processed_ids.add(pid)
        
        url, year = extract_paper_url(paper)
        if url:
            all_paper_urls[url] = year
        
        # Depth 2: Referenzen dieser Paper
        if max_depth >= 2 and paper.get("citationCount", 0) > 5:
            refs = get_paper_references(pid, limit=30)
            for ref in refs:
                ref_id = ref.get("paperId")
                if ref_id and ref_id not in processed_ids:
                    processed_ids.add(ref_id)
                    ref_url, ref_year = extract_paper_url(ref)
                    if ref_url:
                        all_paper_urls[ref_url] = ref_year
            time.sleep(0.3)
    
    # Depth 3: Referenzen der Referenzen (wenn max_depth >= 3)
    if max_depth >= 3:
        print(f"   🔁 Depth 3: Referenzen der Referenzen...")
        depth3_ids = list(processed_ids)
        for pid in depth3_ids:
            if len(processed_ids) > 500:
                break
            refs = get_paper_references(pid, limit=30)
            for ref in refs:
                ref_id = ref.get("paperId")
                if ref_id and ref_id not in processed_ids:
                    processed_ids.add(ref_id)
                    ref_url, ref_year = extract_paper_url(ref)
                    if ref_url:
                        all_paper_urls[ref_url] = ref_year
            time.sleep(0.2)
    
    # CORE API Sweep (zusätzlich zu Semantic Scholar)
    print(f"   📚 CORE API Sweep...")
    for query in queries[:10]:
        core_results = search_core_api(query)
        for url, year in core_results:
            all_paper_urls[url] = year
        time.sleep(0.5)
    
    # Zusätzlich PubMed für Gesundheits-relevante Marken
    health_industries = ["food", "nutrition", "supplement", "health", "beverage", "meal replacement"]
    is_health = any(h in industry.lower() for h in health_industries) or \
                any(any(h in sub.lower() for h in health_industries) for sub in sub_industries)
    
    if is_health:
        print(f"   🏥 PubMed Sweep (Gesundheits-relevante Marke)...")
        pubmed_queries = [
            f"{brand} safety",
            f"{industry} health effects",
            f"meal replacement nutritional study",
        ]
        for q in pubmed_queries:
            try:
                resp = requests.get(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                    params={"db": "pubmed", "term": q, "retmax": 50, "retmode": "json"},
                    timeout=15
                )
                ids = resp.json().get("esearchresult", {}).get("idlist", [])
                for pmid in ids:
                    all_paper_urls[f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"] = None
                time.sleep(0.5)
            except:
                pass
    
    print(f"\n✅ Wissenschafts-Sweep: {len(all_paper_urls)} Paper-URLs gefunden")
    print(f"   (Depth {max_depth}, {len(processed_ids)} Papers analysiert)")
    
    return {
        "paper_urls": list(all_paper_urls.keys()),
        "url_meta": all_paper_urls  # url → year
    }
