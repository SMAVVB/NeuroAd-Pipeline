import json
import re
import sys
import os
import time
import asyncio
from curl_cffi.requests import AsyncSession

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_core import ask_llm, search_searxng, MODEL_WORKHORSE, SEARXNG_URL
from agents.agent_archive import get_wayback_urls, get_semantic_scholar_urls


# Pflicht-Säulen die IMMER für jede Marke recherchiert werden
MANDATORY_PILLARS = [
    {
        "id": "history",
        "label": "Unternehmensgeschichte & Gründung",
        "aspects": ["Gründer & Gründungsgeschichte", "Meilensteine & Wendepunkte", "Firmenstruktur & Eigentümer"],
        "temporal": True  # Diese Säule wird pro historischem Zeitraum wiederholt
    },
    {
        "id": "products",
        "label": "Produkte & Portfolio",
        "aspects": ["Produktlinien & Varianten", "Nährwerte & Inhaltsstoffe", "Produktinnovationen & Launches"],
        "temporal": False
    },
    {
        "id": "marketing",
        "label": "Marketing & Kampagnen",
        "aspects": ["Werbekampagnen & Slogans", "Influencer & Sponsoring", "Social Media Strategie"],
        "temporal": True
    },
    {
        "id": "financials",
        "label": "Finanzen & Investoren",
        "aspects": ["Umsatz & Wachstum", "Finanzierungsrunden & Investoren", "Bewertung & Exit-Strategie"],
        "temporal": False
    },
    {
        "id": "competition",
        "label": "Wettbewerb & Marktposition",
        "aspects": ["Hauptwettbewerber & Marktanteile", "Differenzierung & USP", "Markttrends & Segment"],
        "temporal": False
    },
    {
        "id": "controversies",
        "label": "Kontroversen & Krisen",
        "aspects": ["Rechtliche Auseinandersetzungen", "Gesundheits- & Sicherheitskritik", "PR-Krisen & Skandale"],
        "temporal": True
    },
    {
        "id": "management",
        "label": "Management & Unternehmenskultur",
        "aspects": ["Führungsteam & Wechsel", "Unternehmenskultur & Werte", "Mitarbeiterbewertungen"],
        "temporal": False
    },
]

# Zusätzliche Säulen je nach Markengröße
EXTENDED_PILLARS_MID = [
    {
        "id": "retail",
        "label": "Retail & Distribution",
        "aspects": ["Vertriebskanäle & Partner", "E-Commerce Performance", "Retail-Expansion"],
        "temporal": False
    },
    {
        "id": "sustainability",
        "label": "Nachhaltigkeit & ESG",
        "aspects": ["Umweltinitiativen", "Verpackung & CO2", "Soziale Verantwortung"],
        "temporal": False
    },
]

EXTENDED_PILLARS_GLOBAL = [
    {
        "id": "international",
        "label": "Internationale Expansion",
        "aspects": ["Markteintritte & Strategie", "Lokalisierung", "Joint Ventures & Akquisitionen"],
        "temporal": True
    },
    {
        "id": "science",
        "label": "Wissenschaft & Forschung",
        "aspects": ["Studien & Publikationen", "R&D Investitionen", "Patente & Innovation"],
        "temporal": False
    },
    {
        "id": "media",
        "label": "Medien & Content",
        "aspects": ["Owned Media", "Press Coverage", "Viral Campaigns"],
        "temporal": False
    },
]


async def search_searxng_async(session: AsyncSession, query: str, semaphore: asyncio.Semaphore) -> list:
    """
    TASK 3a: Neue async Hilfsfunktion für SearXNG Suche.
    search_searxng_async(session, query, semaphore) als async def:
    - Liest SEARXNG_URL aus config_core
    - await session.get mit params={"q": query, "format": "json"}, timeout=10
    - Gibt list[str] zurück (URLs aus results)
    - Bei Exception: return []
    """
    async with semaphore:
        try:
            params = {"q": query, "format": "json"}
            response = await session.get(SEARXNG_URL, params=params, timeout=10)
            response.raise_for_status()
            results = response.json().get("results", [])
            
            # Filter forbidden domains
            forbidden_domains = ["github.com", "huggingface.co", "reddit.com", "stackexchange.com", "facebook.com"]
            forbidden_extensions = [".pdf", ".docx", ".xlsx", ".zip"]
            
            valid_urls = []
            for r in results:
                url = r.get("url", "")
                url_lower = url.lower()
                if not any(bad in url_lower for bad in forbidden_domains) and not any(url_lower.endswith(ext) for ext in forbidden_extensions):
                    valid_urls.append(url)
            
            return valid_urls
            
        except Exception:
            return []


async def fire_queries_async(queries: list, concurrent: int = 20) -> list:
    """
    TASK 3a: Neue async Hilfsfunktion für Query-Fire.
    fire_queries_async(queries, concurrent=10) als async def:
    - AsyncSession + Semaphore(concurrent)
    - asyncio.gather über alle queries
    - Gibt deduplizierte URL-Liste zurück
    """
    semaphore = asyncio.Semaphore(concurrent)
    
    async with AsyncSession(impersonate="chrome110") as session:
        tasks = [search_searxng_async(session, query, semaphore) for query in queries]
        results = await asyncio.gather(*tasks)
    
    # Deduplizieren
    all_urls = []
    for urls in results:
        all_urls.extend(urls)
    
    return list(set(all_urls))


async def generate_pillar_queries(brand: str, pillar: dict, n_queries: int, competitors: list) -> list:
    """Generiert Queries für eine Säule via LLM."""
    competitor_hint = f"Vergleiche auch mit: {', '.join(competitors[:3])}" if competitors else ""
    
    prompt = f"""Erstelle {n_queries} hochspezifische Suchanfragen für das Thema '{pillar['label']}' der Marke '{brand}'.
Aspekte die abgedeckt werden sollen: {', '.join(pillar['aspects'])}
{competitor_hint}
Gib NUR ein JSON zurück: {{"queries": ["query1", "query2", ...]}}"""
    
    response = ask_llm(prompt, "Generiere Pillar-Queries.", MODEL_WORKHORSE)
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group()).get("queries", [])
        except:
            pass
    return []


async def generate_historical_queries(brand: str, pillar: dict, period: dict, n_queries: int) -> list:
    """Generiert historische Queries für eine Säule + Zeitraum."""
    prompt = f"""Erstelle {n_queries} Suchanfragen für '{pillar['label']}' der Marke '{brand}' im Zeitraum {period['from_year']}-{period['to_year']} ({period['label']}).
Fokus auf historische Ereignisse, Veränderungen und Entwicklungen in diesem Zeitraum.
Gib NUR ein JSON zurück: {{"queries": ["query1", "query2", ...]}}"""
    
    response = ask_llm(prompt, "Generiere historische Queries.", MODEL_WORKHORSE)
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group()).get("queries", [])
        except:
            pass
    return []


async def generate_market_queries(brand: str, pillar: dict, market: dict, n_queries: int) -> list:
    """Generiert markt-spezifische Queries in der Landessprache."""
    lang_instruction = f"Schreibe die Queries auf {market['language'].upper()} (Landessprache)." if market['language'] != 'en' else ""
    
    prompt = f"""Erstelle {n_queries} Suchanfragen für '{pillar['label']}' der Marke '{brand}' speziell für den Markt {market['country']}.
{lang_instruction}
Fokus auf lokale News, lokale Kontroversen, lokale Vertriebspartner, lokale Kampagnen.
Gib NUR ein JSON zurück: {{"queries": ["query1", "query2", ...]}}"""
    
    response = ask_llm(prompt, "Generiere Markt-Queries.", MODEL_WORKHORSE)
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group()).get("queries", [])
        except:
            pass
    return []


async def generate_yearly_queries(brand: str, pillar: dict, year: int, n_queries: int) -> list:
    """Generiert jahres-spezifische Queries mit Datum-Filter."""
    prompt = f"""Erstelle {n_queries} Suchanfragen für '{pillar['label']}' der Marke '{brand}' speziell für das Jahr {year}.
Jede Query MUSS das Jahr {year} enthalten.
Beispiele: "{brand} {year} Umsatz", "{brand} Kampagne {year}", "site:reddit.com {brand} {year}"
Gib NUR JSON zurück: {{"queries": ["query1", "query2", ...]}}"""
    
    response = ask_llm(prompt, "Generiere Jahres-Queries.", MODEL_WORKHORSE)
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group()).get("queries", [])
        except:
            pass
    # Fallback: manuelle Queries mit Jahr
    return [
        f"{brand} {pillar['label']} {year}",
        f"{brand} {year} news",
        f"site:reddit.com {brand} {year}"
    ]


async def run_publisher_agent(brand: str, note: str, baseline: str, brand_profile: dict = None, num_pillars: int = None, queries_per_pillar: int = None) -> tuple:
    """
    FIX 1: run_publisher_agent auf async def umgestellt.
    asyncio.run(fire_queries_async(...)) ersetzt durch await fire_queries_async(...)
    LLM-Calls (ask_llm) bleiben seriell — nicht ändern.
    
    NEU: Brand-Profil gesteuert mit fixem hierarchischem Suchbaum.
    """
    print(f"\n📰 [PHASE 1] Starte strukturierten Suchbaum für '{brand}'...")
    
    # Profil-Parameter auslesen
    profile = brand_profile or {}
    size = profile.get("size", "mid")
    qv = profile.get("query_volume", {})
    n_queries = queries_per_pillar or qv.get("queries_per_pillar", 20)
    historical_periods = profile.get("historical_periods", [])
    primary_markets = profile.get("primary_markets", [{"country": "Deutschland", "language": "de", "depth": "deep"}])
    key_competitors = profile.get("key_competitors", [])
    
    # Säulen zusammenstellen
    # large als global behandeln (Normalisierungs-Fallback)
    effective_size = size if size in ("startup", "mid", "global") else "global"
    
    pillars = list(MANDATORY_PILLARS)
    if effective_size in ("mid", "global"):
        pillars += EXTENDED_PILLARS_MID
    if effective_size == "global":
        pillars += EXTENDED_PILLARS_GLOBAL
    
    print(f"   📋 Suchbaum: {len(pillars)} Säulen, {n_queries} Queries/Säule, {len(primary_markets)} Märkte")
    
    all_urls = []
    total_queries = 0
    
    for pillar in pillars:
        print(f"\n   🔬 Säule: {pillar['label']}...")
        
        # Basis-Queries für diese Säule (marktübergreifend)
        queries = await generate_pillar_queries(brand, pillar, n_queries, key_competitors)
        total_queries += len(queries)
        
        if queries:
            urls = await fire_queries_async(queries, concurrent=5)
            all_urls.extend(urls)
        
        # Historische Queries (nur für temporal=True Säulen)
        if pillar.get("temporal") and historical_periods:
            for period in historical_periods:
                if period.get("priority") == "low":
                    continue
                from_year = period.get("from_year", 2015)
                to_year = period.get("to_year", 2026)
                
                # Pro Jahr einen Sweep
                for year in range(from_year, to_year + 1):
                    year_queries = await generate_yearly_queries(brand, pillar, year, max(n_queries // 3, 3))
                    total_queries += len(year_queries)
                    if year_queries:
                        urls = await fire_queries_async(year_queries, concurrent=5)
                        # Mit Jahr-Metadaten speichern (für spätere Filterung)
                        all_urls.extend([(u, year) for u in urls])
        
        # Markt-spezifische Queries (für deep/medium Märkte)
        for market in primary_markets:
            if market.get("depth") == "shallow":
                continue
            market_n = n_queries if market["depth"] == "deep" else n_queries // 2
            market_queries = await generate_market_queries(brand, pillar, market, market_n)
            total_queries += len(market_queries)
            if market_queries:
                urls = await fire_queries_async(market_queries, concurrent=5)
                all_urls.extend(urls)
        
        time.sleep(1)  # Kurze Pause für den LLM-Server
    
    # Wayback Machine: historische Brand-Snapshots
    print(f"\n   📼 Wayback Machine: Historische Snapshots...")
    founding = brand_profile.get("founding_year") if brand_profile else None
    if founding:
        for year in range(founding, 2027):
            wayback_results = get_wayback_urls(brand, brand, year=year, limit=100)
            for wb_url, wb_year in wayback_results:
                all_urls.append((wb_url, wb_year))
            if len(wayback_results) > 0:
                print(f"      {year}: {len(wayback_results)} Snapshots")
    
    # Semantic Scholar: wissenschaftliche Paper
    print(f"\n   🔬 Semantic Scholar: Wissenschaftliche Paper...")
    science_queries = [
        f"{brand} brand marketing",
        f"{brand} consumer behavior",
        f"{brand} market analysis",
    ]
    # Industrie-spezifische Queries
    if brand_profile:
        for sub in brand_profile.get("sub_industries", [])[:3]:
            science_queries.append(f"{sub} consumer research")
            science_queries.append(f"{sub} market study")
    
    for sq in science_queries:
        papers = get_semantic_scholar_urls(sq, limit=50)
        for paper_url, paper_year, title in papers:
            all_urls.append((paper_url, paper_year))
        print(f"      '{sq[:40]}': {len(papers)} Paper")
    
    # URLs und Metadaten trennen (nach Wayback/Semantic Scholar)
    url_list = [u[0] if isinstance(u, tuple) else u for u in all_urls]
    url_meta = {u[0]: u[1] for u in all_urls if isinstance(u, tuple)}
    unique_urls = list(set(url_list))
    
    print(f"\n✅ Suchbaum komplett: {total_queries} Queries, {len(unique_urls)} unique URLs")
    return unique_urls, url_meta
