import os
import json
import logging
import requests
import time
from datetime import datetime
from pathlib import Path

# --- KONFIGURATION ---
LLM_URL = "http://127.0.0.1:11434/v1/chat/completions"
SEARXNG_URL = "http://127.0.0.1:8889/search"
RAW_DATA_DIR = "raw_data" 

MODEL_WORKHORSE = "qwen3.6:35b-a3b-q4_K_M"
MODEL_JUDGE = "qwen3.6:35b-a3b-q4_K_M"
MODEL_FAST = "qwen3.5:4b"
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

    # DEFAULT timeout: 180 seconds (3 minutes)
    default_timeout = 180

    # AUTO-RETRY LOOP with exponential backoff
    for attempt in range(max_retries):
        try:
            timeout = timeout_override if timeout_override is not None else default_timeout
            res = requests.post(LLM_URL, json=payload, timeout=timeout)
            res.raise_for_status()
            data = res.json()

            # Hat der API-Server intern einen Error in das JSON geschrieben? (Wie bei deinem Curl-Error)
            if "error" in data:
                print(f"\n⚠️ API-SERVER FEHLER (Versuch {attempt+1}/{max_retries}): {data['error']}")
                time.sleep(5) # 5 Sekunden abkühlen
                continue      # Nächster Versuch!

            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Token logging REMOVED - Ollama does not support token tracking
            # Ollama provides no token_usage data, this code was legacy from lemonade proxy era

            if not content.strip():
                print(f"\n⚠️ ALARM: Leere Antwort vom Modell (Versuch {attempt+1}/{max_retries}).")
                time.sleep(5)
                continue

            return content

        except requests.exceptions.RequestException as e:
            print(f"\n❌ NETZWERK-FEHLER (Versuch {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                backoff = 5 * (2 ** attempt)  # 5, 10, 20 seconds
                print(f"   Warte {backoff}s vor Wiederholungsversuch...")
                time.sleep(backoff)

    # All retries exhausted — return safe fallback instead of crashing
    print("🚨 FEHLER: Alle Retries fehlgeschlagen. Breche LLM-Anfrage ab.")
    return "LLM API Error: Timeout or Unreachable"

def search_searxng(query: str, category: str = "general") -> list:
    print(f"   🔍 Suche: {query}")
    params = {"q": query, "format": "json", "categories": category}
    
    forbidden_domains = ["github.com", "huggingface.co", "reddit.com", "stackexchange.com", "facebook.com"]
    forbidden_extensions = [".pdf", ".docx", ".xlsx", ".zip"] 
    
    try:
        res = requests.post(SEARXNG_URL, data=params, timeout=10)
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


def get_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """Return a logger that writes to both the default stream and a campaign log file."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)

    fmt = logging.Formatter("%(asctime)s %(levelname)s - %(message)s", datefmt="%H:%M:%S")

    # console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger
