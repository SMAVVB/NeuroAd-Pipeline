import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

# --- VERZEICHNISSE (Original-Struktur) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = os.path.join(BASE_DIR, "raw_data")
CAMPAIGNS_DIR = os.path.join(BASE_DIR, "campaigns")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# --- API & ENDPUNKTE (Nur hier wurde geändert) ---
OPENAI_API_KEY = "ollama"
OPENAI_API_BASE = "http://127.0.0.1:11434/v1"
SEARXNG_URL = "http://127.0.0.1:8889"

# --- MODELLE (Alle auf Qwen 3.6 35B umgebogen) ---
MODEL_WORKHORSE = "qwen3.6:35b-a3b-q4_K_M"
MODEL_FAST = "qwen3.6:35b-a3b-q4_K_M"
MODEL_JUDGE = "qwen3.6:35b-a3b-q4_K_M"
MODEL_VISION = "qwen3.6:35b-a3b-q4_K_M"

# --- KERN-FUNKTIONEN ---

def ask_llm(prompt, context_msg="System", model=MODEL_WORKHORSE):
    """Zentrale LLM-Anfrage (OpenAI-kompatibel via Ollama)"""
    url = f"{OPENAI_API_BASE}/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": context_msg},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2048 # VRAM Schutz
    }

    for attempt in range(1, 16):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=120)
            
            # Falls der v1-Wrapper von Ollama zickt, Fallback auf nativ
            if response.status_code == 404:
                native_url = "http://127.0.0.1:11434/api/chat"
                native_data = {
                    "model": model,
                    "messages": [{"role": "user", "content": f"{context_msg}\n{prompt}"}],
                    "stream": False
                }
                response = requests.post(native_url, json=native_data, timeout=120)
            
            response.raise_for_status()
            res_json = response.json()
            
            # Ergebnis extrahieren (je nach Endpunkt-Struktur)
            if 'choices' in res_json:
                return res_json['choices'][0]['message']['content']
            return res_json['message']['content']
            
        except Exception as e:
            print(f"❌ NETZWERK-FEHLER (Versuch {attempt}/15): {e}")
            if attempt == 15: raise e
            time.sleep(2)

def search_searxng(query):
    """Web-Suche via SearxNG"""
    try:
        response = requests.get(
            f"{SEARXNG_URL}/search",
            params={"q": query, "format": "json"},
            timeout=10
        )
        response.raise_for_status()
        return response.json().get("results", [])
    except Exception as e:
        print(f"⚠️ Search Error: {e}")
        return []

# --- INITIALISIERUNG ---
for d in [RAW_DATA_DIR, CAMPAIGNS_DIR, LOG_DIR]:
    os.makedirs(d, exist_ok=True)
