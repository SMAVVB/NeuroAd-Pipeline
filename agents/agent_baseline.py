import os
import sys
from curl_cffi import requests as curl_requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_core import ask_llm, search_searxng, MODEL_WORKHORSE
from agents.agent_scraper import extract_clean_text # HIER IST DER RETTER!

def get_quick_web_context(brand: str) -> str:
    print(f"   🌐 [PHASE 0.1] Suche Basis-Informationen zu '{brand}' im Web...")
    urls = search_searxng(f"{brand} company overview OR wikipedia OR global market share 2026")
    
    context = ""
    for url in urls[:3]:
        try:
            res = curl_requests.get(url, impersonate="chrome110", timeout=10)
            # HTML Müll entfernen, nur reinen Lesetext an Gemma schicken!
            clean_text = extract_clean_text(res.content)
            if clean_text:
                context += f"QUELLE ({url}):\n{clean_text[:5000]}\n\n"
        except:
            continue
    return context

def generate_baseline(brand: str, save_dir: str) -> str:
    print(f"\n🧠 [PHASE 0.2] Gemma 4 erstellt das Makro-Fundament für '{brand}'...")
    
    web_context = get_quick_web_context(brand)
    
    draft_prompt = f"""Du bist Lead Business Analyst. Erstelle ein unfassbar breites, neutrales Lexikon-Wissen über die Marke '{brand}'.
    Es gibt KEINEN speziellen Fokus. Betrachte die KOMPLETTE HISTORIE von der Gründung bis heute.
    
    Nutze dieses frische Web-Wissen als Ergänzung zu deinem internen Training:
    {web_context}
    
    Gliedere den Report zwingend in:
    1. Historie & Evolution
    2. Globale Marktpräsenz (Nenne explizit die wichtigsten Länder/Sprachen!)
    3. Finanzielle Dimensionen
    4. Sub-Marken & Produktdiversifikation
    5. Größte globale Skandale & Kontroversen
    
    Schreibe in klaren, datengetriebenen Stichpunkten."""
    
    verified_seed = ask_llm(draft_prompt, f"Erstelle Broad-Baseline für {brand}", MODEL_WORKHORSE)
    
    file_path = os.path.join(save_dir, "Phase_0_Verified_Seed.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(verified_seed)
        
    print("✅ Phase 0 abgeschlossen: Makro-Fundament gespeichert.")
    return verified_seed
