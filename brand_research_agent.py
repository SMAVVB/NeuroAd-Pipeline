import sys
import json
import requests
import asyncio
import os
import re
from datetime import datetime
from crawl4ai import AsyncWebCrawler

# Importiere unseren Manager aus der anderen Datei
from brand_graph_manager import BrandGraphManager, URI, AUTH

# --- 1. KONFIGURATION ---
LLM_URL = "http://172.17.0.1:8888/v1/chat/completions" # Deine Lemonade IP
SEARXNG_URL = "http://127.0.0.1:8889/search"
RAW_DATA_DIR = "raw_data" 

# Deine Next-Gen Modell-Flotte (mit extra.-Präfix für Lemonade)
MODEL_WORKHORSE = "extra.gemma-4-31B-it-Q4_K_M.gguf"
MODEL_CRITIC = "extra.moonshotai_Kimi-Linear-48B-A3B-Instruct-Q5_K_M.gguf"
MODEL_JUDGE = "extra.DeepSeek-R1-Distill-Llama-70B-Q4_K_M.gguf"

# --- 2. DYNAMISCHER API-CALL ---
def ask_llm(system_prompt: str, user_prompt: str, model_name: str, temperature: float = 0.2) -> str:
    """Dynamischer Call: Das Backend lädt das Modell automatisch bei einem Namenswechsel."""
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature
    }
    # Timeout auf 900s erhöht für maximale Skalierung
    response = requests.post(LLM_URL, json=payload, timeout=900)
    response.raise_for_status()
    return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")

# --- 3. PHASE 0 & 1: BASELINE & SUCHBAUM ---
def generate_phase_0_baseline(brand: str, note: str) -> str:
    print(f"\n🧠 [PHASE 0] Rufe internes Basiswissen zu '{brand}' ab...")
    system_prompt = f"""Du bist ein Senior Business Analyst. Greife auf dein gesamtes Trainingswissen zurück, um eine detaillierte, ungeschönte Basis-Analyse der Marke '{brand}' zu erstellen.
    
    KONTEXT DER RECHERCHE: {note}
    
    Fülle folgende Bereiche mit harten Fakten (wenn du etwas nicht weißt, schreib 'Wissenslücke'):
    1. Kern-DNA & Historie (Gründung, Geschäftsmodell)
    2. Bekannte große Marketingkampagnen
    3. Finanzielle Einordnung (geschätzte Größe, Marktanteil)
    4. Öffentliches Sentiment & bekannte Kontroversen/Skandale
    
    Fasse dich präzise und informativ kurz."""
    
    user_prompt = f"Erstelle die Baseline für: {brand}"
    baseline = ask_llm(system_prompt, user_prompt, MODEL_WORKHORSE)
    print("✅ Baseline erfolgreich erstellt.")
    return baseline

def build_search_tree(brand: str, baseline: str, note: str) -> dict:
    print(f"\n🌳 [PHASE 1] Generiere intelligenten Suchbaum für '{brand}'...")
    system_prompt = f"""Du bist der Lead Data Engineer. Analysiere das interne Basiswissen der Marke '{brand}' und den Ziel-Kontext.
    Erstelle einen MASSIVEN Suchbaum für eine tiefgreifende Web-Recherche.
    
    STRIKTE REGELN FÜR SUCHBEGRIFFE:
    1. JEDE Query MUSS zwingend den exakten Markennamen '{brand}' enthalten!
    2. Nutze gezielte Such-Operatoren (z.B. "{brand} revenue 2024", "site:reddit.com {brand} controversies").
    3. Keine langen Fragesätze. Nutze Keyword-Ketten.
    4. Erstelle 5 Haupt-Zweige (Branches) mit jeweils exakt 10 spezifischen Such-Queries (Gesamt: 50 Queries).
    
    Gib AUSSCHLIESSLICH ein valides JSON-Objekt zurück, exakt in dieser Struktur:
    {{
      "branches": [
        {{"branch_name": "Finanzen & Markt", "queries": ["...", "..."]}},
        {{"branch_name": "Kampagnen & CSR", "queries": ["...", "..."]}},
        {{"branch_name": "Social Sentiment & Reddit", "queries": ["...", "..."]}},
        {{"branch_name": "Produktion & Supply Chain", "queries": ["...", "..."]}},
        {{"branch_name": "Skandale & Kritik", "queries": ["...", "..."]}}
      ]
    }}"""
    
    user_prompt = f"Kontext: {note}\n\nBisheriges Basiswissen:\n{baseline}\n\nGeneriere den Suchbaum als JSON."
    response = ask_llm(system_prompt, user_prompt, MODEL_WORKHORSE)
    
    try:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"⚠️ JSON Parse Fehler im Suchbaum: {e}")
        
    return {"branches": [{"branch_name": "Notfall-Zweig", "queries": [f"{brand} marketing", f"{brand} brand values", f"{brand} controversies"]}]}

# --- 4. TOOLING: SEARCH, REDDIT, CRAWL & MAP ---
def search_searxng(query: str) -> list[str]:
    print(f"🌐 Suche: {query}")
    params = {"q": query, "format": "json", "engines": "google,bing,duckduckgo", "language": "en-US"}
    try:
        res = requests.get(SEARXNG_URL, params=params, timeout=15)
        res.raise_for_status()
        # MASSIVES VOLUMEN: 30 URLs pro Query (Bei 50 Queries = 1500 URLs!)
        return [r["url"] for r in res.json().get("results", [])[:30]] 
    except Exception as e:
        print(f"⚠️ SearXNG Fehler bei '{query}': {e}")
        return []

def fetch_reddit_data(brand: str, save_dir: str, limit: int = 50) -> str:
    print(f"👽 Zapfe Reddit API für '{brand}' an...")
    url = f"https://www.reddit.com/search.json?q={brand}&limit={limit}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        with open(os.path.join(save_dir, "reddit_raw.json"), "w", encoding="utf-8") as f:
            f.write(json.dumps(data, indent=2))
            
        reddit_text = f"--- REDDIT DISKUSSIONEN ZU {brand.upper()} ---\n"
        for post in data.get("data", {}).get("children", []):
            post_data = post.get("data", {})
            reddit_text += f"Titel: {post_data.get('title', '')} (Upvotes: {post_data.get('score', 0)})\n"
            if post_data.get('selftext'):
                reddit_text += f"Inhalt: {post_data.get('selftext')[:1000]}...\n"
            reddit_text += "-" * 20 + "\n"
        return reddit_text
    except Exception as e:
        return ""

def summarize_chunk(brand: str, note: str, raw_text: str) -> str:
    if not raw_text.strip(): return ""
    system_prompt = f"""Du bist ein präziser Marketing-Analyst. Extrahiere harte Fakten, Kampagnen-Infos und öffentliches Sentiment zur Marke '{brand}'.
    KONTEXT DER RECHERCHE: {note}
    STRIKTE FILTER-REGELN: Ignoriere geografische Orte, Wörterbuch-Einträge, Spam, Fake-Produkte und Werbe-Menüs. Gib einen leeren String zurück, wenn der Text irrelevantes Rauschen ist."""
    return ask_llm(system_prompt, f"Text:\n{raw_text[:12000]}", MODEL_WORKHORSE)

async def crawl_and_map_batches(urls: list[str], brand: str, note: str, save_dir: str, batch_size: int = 25) -> str:
    print(f"🕷️ Crawle und analysiere {len(urls)} URLs in Batches von {batch_size}...")
    all_summaries = ""
    async with AsyncWebCrawler(verbose=False) as crawler:
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            batch_text = ""
            for idx, url in enumerate(batch):
                try:
                    result = await crawler.arun(url=url, bypass_cache=True)
                    if result.markdown:
                        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', url)[:50]
                        with open(os.path.join(save_dir, f"batch_{i//batch_size}_url_{idx}_{safe_name}.md"), "w", encoding="utf-8") as f:
                            f.write(f"URL: {url}\n\n{result.markdown}")
                        batch_text += f"\nQuelle: {url}\n{result.markdown[:4000]}\n"
                except:
                    pass
            
            if batch_text:
                chunk_summary = summarize_chunk(brand, note, batch_text) 
                all_summaries += f"\n{chunk_summary}\n"
            await asyncio.sleep(2) 
    return all_summaries

# --- 5. PHASE 3: DER KI-RAT (COUNCIL) ---
def evaluate_data_council(brand: str, note: str, current_data: str) -> dict:
    print(f"\n⚖️ [PHASE 3] DER KI-RAT TRITT ZUSAMMEN (Sequentieller Load)...")
    
    eval_prompt = f"""Du bist ein hochkritischer Lead-Analyst für die Marke '{brand}'.
    Lies die riesige Menge an gesammelten Rohdaten. Haben wir ein absolut umfassendes Bild zu Finanzen, Historie, Kampagnen und ungeschöntem Social Sentiment? 
    Was fehlt konkret?"""
    
    print(f"   -> Lade Juror 1 ({MODEL_WORKHORSE})...")
    gemma_critique = ask_llm(eval_prompt, f"Daten:\n{current_data}", MODEL_WORKHORSE, 0.3)
    
    print(f"   -> Lade Juror 2 ({MODEL_CRITIC})...")
    kimi_critique = ask_llm(eval_prompt, f"Daten:\n{current_data}", MODEL_CRITIC, 0.3)
    
    print(f"   -> Lade den Richter ({MODEL_JUDGE})...")
    judge_system = f"""Du bist der Chief Intelligence Officer. Du evaluierst die Big-Data-Recherche zur Marke '{brand}'.
    Lies die Kritik der Juroren. Wenn alles perfekt ist, setze "ausreichend" auf true.
    Wenn gravierende Lücken bestehen, setze "ausreichend" auf false und generiere exakt 5 NEUE, messerscharfe Suchanfragen, um diese zu schließen.
    JSON Format: {{"ausreichend": boolean, "neue_queries": ["q1", "q2", "q3", "q4", "q5"], "begruendung": "..."}}"""
    
    verdict_raw = ask_llm(judge_system, f"Gemma:\n{gemma_critique}\n\nKimi:\n{kimi_critique}", MODEL_JUDGE, 0.1)
    
    try:
        json_match = re.search(r'\{.*\}', verdict_raw, re.DOTALL)
        if json_match: return json.loads(json_match.group())
    except: pass
    return {"ausreichend": True, "neue_queries": [], "begruendung": "Fallback."}

def synthesize_research(brand: str, raw_text: str) -> dict:
    print(f"🧠 Synthetisiere finales JSON für '{brand}' (Sichere Neo4j-Formatierung)...")
    system_prompt = """Du bist ein Chief Marketing Officer. Formatiere die Markenidentität AUSSCHLIESSLICH als valides JSON-Objekt.
    
    NEO4J DATENBANK-REGEL (KRITISCH!):
    Du darfst KEINE verschachtelten Objekte (Dictionaries/Maps) erstellen! Alle Werte müssen zwingend reine Text-Strings oder Arrays von Strings sein. Keine Sub-Keys!
    
    Exakte Keys:
    - "brand_name": (String) Name der Marke
    - "brand_dna": (String) Ein zusammenhängender Text über Historie und Kernwerte
    - "visual_style": (String) Ein zusammenhängender, beschreibender Text über den Stil (KEIN Objekt!)
    - "tone_of_voice": (String) Ein zusammenhängender, beschreibender Text
    - "key_messages": (Array of Strings) 3-5 Kernaussagen
    - "clip_labels": (Array of Strings) 3-5 kurze englische Labels"""
    
    # Maximaler Kontext für DeepSeek R1 für das riesige JSON
    response = ask_llm(system_prompt, f"Brand: {brand}\n\nFakten:\n{raw_text}", MODEL_JUDGE) 
    
    try:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match: return json.loads(json_match.group())
    except: pass
    return {"brand_name": brand, "error": "JSON parse failed", "raw": response}

# --- 6. DER MAIN AGENT ---
async def run_brand_agent(brand: str, note: str):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = os.path.join(RAW_DATA_DIR, f"{brand.replace(' ', '_')}_{timestamp}")
    os.makedirs(save_dir, exist_ok=True)
    print(f"📂 Setup abgeschlossen. Rohdaten-Ordner: {save_dir}")

    # Phase 0
    baseline = generate_phase_0_baseline(brand, note)
    
    # NEU: Das interne Wissen sofort sichtbar speichern!
    with open(os.path.join(save_dir, "Phase_0_Baseline.md"), "w", encoding="utf-8") as f:
        f.write(f"# Interne Baseline für {brand}\n\n{baseline}")
        
    # Phase 1
    search_tree = build_search_tree(brand, baseline, note)
    all_summaries = f"--- INTERNES BASISWISSEN (GEMMA 4) ---\n{baseline}\n\n"
    
    # Phase 2: Workhorse rattert den gigantischen Baum ab
    print(f"\n🐎 [PHASE 2] Gemma 4 arbeitet den strukturierten Suchbaum ab (Extreme Scale)...")
    for branch in search_tree.get("branches", []):
        branch_name = branch.get("branch_name", "Allgemein")
        queries = branch.get("queries", [])
        print(f"\n📁 Starte Zweig: {branch_name} (Queries: {len(queries)})")
        
        urls = []
        for q in queries:
            urls.extend(search_searxng(q))
        urls = list(set(urls))
        
        branch_data = await crawl_and_map_batches(urls, brand, note, save_dir, batch_size=25)
        all_summaries += f"--- ZWEIG: {branch_name} ---\n{branch_data}\n"
        
    reddit_data = fetch_reddit_data(brand, save_dir, limit=50)
    all_summaries += f"\n{reddit_data}\n"
    
    # Phase 3: Council Audit
    verdict = evaluate_data_council(brand, note, all_summaries)
    print(f"\n📢 Rats-Beschluss: Ausreichend? {verdict.get('ausreichend')}")
    print(f"📝 Begründung des Richters (DeepSeek R1): {verdict.get('begruendung')}")
    
    # Emergency Loop
    if not verdict.get("ausreichend") and verdict.get("neue_queries"):
        print(f"\n🚑 Notfall-Iteration: Der Rat verlangt gezielte Nachbesserung...")
        urls = []
        for q in verdict.get("neue_queries", []):
            urls.extend(search_searxng(q))
        emergency_data = await crawl_and_map_batches(list(set(urls)), brand, note, save_dir, batch_size=25)
        all_summaries += f"\n--- NOTFALL-ITERATION (COUNCIL) ---\n{emergency_data}\n"

    # Speichern und Synthetisieren
    with open(os.path.join(save_dir, "LLM_Summaries_Combined.md"), "w", encoding="utf-8") as f:
        f.write(all_summaries)
    
    context_data = synthesize_research(brand, all_summaries)
    
    print("💾 Speichere Resultate in Graph-Datenbank...")
    manager = BrandGraphManager(URI, AUTH)
    manager.ingest_brand_context(context_data)
    manager.close()
    print(f"✅ Skalierter Run erfolgreich! Alle Daten in '{save_dir}' gesichert.")

if __name__ == "__main__":
    brand_input = sys.argv[1] if len(sys.argv) > 1 else "Nike"
    note_input = sys.argv[2] if len(sys.argv) > 2 else "Fokus auf Nachhaltigkeitskampagnen der letzten Jahre."
    asyncio.run(run_brand_agent(brand_input, note_input))
