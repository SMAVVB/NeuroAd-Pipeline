import os
import json
import requests
import time
from datetime import datetime
from pathlib import Path

# --- KONFIGURATION ---
# LLM_URL: Proxy für Token Tracking (Port 8888) → Lemonade (Port 8888)
LLM_URL = "http://127.0.0.1:8888/v1/chat/completions"
SEARXNG_URL = "http://127.0.0.1:8889/search"
RAW_DATA_DIR = "raw_data" 

MODEL_WORKHORSE = "extra.gemma-4-31B-it-Q4_K_M.gguf"
MODEL_JUDGE = "extra.DeepSeek-R1-Distill-Llama-70B-Q4_K_M.gguf"
MODEL_FAST = "extra.moonshotai_Kimi-Linear-48B-A3B-Instruct-Q5_K_M.gguf"
MEMORY_FILE = "agent_learnings.json"

def load_memory() -> str:
    if not os.path.exists(MEMORY_FILE):
        default_rules = {
            "hard_rules": [
                "Generiere NIEMALS ganze Fragesätze.",
                "Nutze ausschließlich kurze, präzise Keywords."
            ]
        }
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(default_rules, f, indent=2)
        return "\n".join(default_rules["hard_rules"])
    
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return "\n".join(json.load(f).get("hard_rules", []))

def ask_llm(system_prompt: str, user_prompt: str, model_name: str, temperature: float = 0.2, max_retries: int = 3, timeout_override: int = None) -> str:
    memory_rules = load_memory()
    enhanced_system = f"{system_prompt}\n\nWICHTIGE LERN-REGELN:\n{memory_rules}"

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": enhanced_system},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": 4096
    }

    # AUTO-RETRY LOOP
    for attempt in range(max_retries):
        try:
            # Nutze timeout_override wenn gesetzt, sonst Standard-Timeout von 1200 Sekunden (20 Minuten)
            timeout = timeout_override if timeout_override is not None else 1200
            res = requests.post(LLM_URL, json=payload, timeout=timeout)
            res.raise_for_status()
            data = res.json()

            # Hat der API-Server intern einen Error in das JSON geschrieben? (Wie bei deinem Curl-Error)
            if "error" in data:
                print(f"\n⚠️ API-SERVER FEHLER (Versuch {attempt+1}/{max_retries}): {data['error']}")
                time.sleep(5) # 5 Sekunden abkühlen
                continue      # Nächster Versuch!

            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Token logging after successful API call
            try:
                usage = data.get("usage", {})
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "model": model_name,
                    "input_tokens": usage.get("prompt_tokens", 0),
                    "output_tokens": usage.get("completion_tokens", 0),
                    "project": os.path.basename(os.getcwd()),
                    "tps": usage.get("tokens_per_second", 0)
                }
                log_file = Path.home() / ".lemonade_token_log.jsonl"
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception:
                pass  # Don't fail if logging fails

            if not content.strip():
                print(f"\n⚠️ ALARM: Leere Antwort vom Modell (Versuch {attempt+1}/{max_retries}).")
                time.sleep(5)
                continue

            return content

        except Exception as e:
            print(f"\n❌ NETZWERK-FEHLER (Versuch {attempt+1}/{max_retries}): {e}")
            time.sleep(5)

    print("🚨 FEHLER: Alle Retries fehlgeschlagen. Breche LLM-Anfrage ab.")
    return ""

def search_searxng(query: str, category: str = "general") -> list:
    print(f"   🔍 Suche: {query}")
    params = {"q": query, "format": "json", "categories": category}
    
    forbidden_domains = ["github.com", "huggingface.co", "reddit.com", "stackexchange.com", "facebook.com"]
    forbidden_extensions = [".pdf", ".docx", ".xlsx", ".zip"] 
    
    try:
        res = requests.get(SEARXNG_URL, params=params, timeout=10)
        res.raise_for_status()
        
        valid_urls = []
        for r in res.json().get("results", []):
            url = r.get("url", "")
            url_lower = url.lower()
            if not any(bad in url_lower for bad in forbidden_domains) and not any(url_lower.endswith(ext) for ext in forbidden_extensions):
                valid_urls.append(url)
                
        return valid_urls[:20] 
    except Exception:
        return []
