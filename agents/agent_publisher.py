import json
import re
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_core import ask_llm, search_searxng, MODEL_WORKHORSE

def run_publisher_agent(brand: str, note: str, baseline: str, num_pillars: int = 15, queries_per_pillar: int = 20) -> list:
    print(f"\n📰 [PHASE 1] Starte HYDRA-Publisher (Map-Reduce) für '{brand}'...")
    
    # SCHRITT 1: MAP (Forschungssäulen generieren)
    print(f"   🧠 Generiere {num_pillars} abstrakte Forschungssäulen...")
    map_prompt = f"""Du bist Head of Research. Definiere exakt {num_pillars} hochspezifische, unterschiedliche Forschungssäulen für die Marke '{brand}'.
    Beispiele: "Lieferketten-Probleme in Asien", "Sponsoring-Kritik Fußball", "Gesundheitsstudien zu Inhaltsstoffen", "Umsatzentwicklung Nordamerika".
    Gib NUR eine nummerierte Liste zurück. Keine Einleitung."""
    
    pillars_text = ask_llm(map_prompt, f"Kontext: {baseline}\nGeneriere Säulen.", MODEL_WORKHORSE)
    pillars = [p.strip() for p in pillars_text.split('\n') if p.strip() and p[0].isdigit()]
    if not pillars: pillars = [f"{brand} Finanzen", f"{brand} Kontroversen", f"{brand} Marketing"]
    
    all_urls = []
    total_queries_generated = 0
    
    # SCHRITT 2: REDUCE (Queries pro Säule generieren)
    print(f"   🐉 Hydra wächst: Iteriere durch {len(pillars)} Säulen (Generiere je {queries_per_pillar} Queries)...")
    
    for idx, pillar in enumerate(pillars):
        print(f"\n   🔬 Säule {idx+1}/{len(pillars)}: {pillar[:50]}...")
        
        reduce_prompt = f"""Erstelle für das Thema '{pillar}' zur Marke '{brand}' ein JSON mit {queries_per_pillar} hochspezifischen Suchanfragen.
        Regel: Hänge an jede Anfrage '-site:{brand.lower().replace(' ', '')}.com' an.
        
        Gib AUSSCHLIESSLICH dieses JSON zurück:
        {{
          "queries": ["query1", "query2", ...]
        }}"""
        
        response = ask_llm(reduce_prompt, "Generiere Queries.", MODEL_WORKHORSE)
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                queries = json.loads(json_match.group()).get("queries", [])
                total_queries_generated += len(queries)
                
                # Queries sofort abfeuern und sammeln
                for q in queries:
                    urls = search_searxng(q)
                    all_urls.extend(urls)
                    
            except Exception as e:
                print("      ⚠️ JSON Parsing Fehler für diese Säule, überspringe...")
                
        time.sleep(1) # Kurze Pause für den LLM-Server
        
    unique_urls = list(set(all_urls))
    print(f"\n✅ Publisher Hydra hat {total_queries_generated} Queries abgefeuert und {len(unique_urls)} externe News/Science-URLs geerntet!")
    return unique_urls
