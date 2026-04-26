import time
import requests
import json
import os
import sys
from dotenv import load_dotenv
import os
load_dotenv()

# Konfiguration (Hier musst du nur deinen Key prüfen)
LOG_FILE = "campaigns/nike_summer_26_run.log"
OLLAMA_URL = "http://localhost:11434/api/generate"
WATCHDOG_MODEL = "qwen3.5:4b"
MULTICA_API_URL = "https://api.multica.ai/api/issues?workspace_slug=the-beast"
MULTICA_API_KEY = os.environ.get("MULTICA_API_KEY")

def analyze_error_with_llm(error_trace):
    prompt = f"Analysiere diesen Crash: {error_trace}. Antworte nur JSON: {{\"is_critical\": true, \"summary\": \"kurze Erklärung\"}}"
    try:
        res = requests.post(OLLAMA_URL, json={"model": WATCHDOG_MODEL, "prompt": prompt, "stream": False, "format": "json", "options": {"num_ctx": 2048}})
        return res.json().get("response", "{}")
    except: return '{"is_critical": false}'

def create_multica_ticket(error_summary, raw_trace):
    headers = {"Authorization": f"Bearer {MULTICA_API_KEY}", "Content-Type": "application/json"}
    
    payload = {
        "workspace_slug": "the-beast",
        "project_id": "e07a5476-d4c2-4665-b1fc-1cf2d1b0ba69",
        "assignee_type": "agent",
        "assignee_id": "710707d6-2484-4bd3-888a-7da10b6684f1",
        "title": f"🚨 Fix Needed: {error_summary}",
        "description": f"### Pipeline Crash Report\n\n**Fehler-Details:**\n```text\n{raw_trace}\n```",
        "priority": "high",
        "status": "todo"
    }
    
    url = "https://api.multica.ai/api/issues?workspace_slug=the-beast"
    try:
        r = requests.post(url, json=payload, headers=headers)
        if r.status_code in [200, 201]:
            print(f"\n🚀 [WATCHDOG] Ticket erstellt und an den Universal-Agenten zugewiesen!")
        else:
            print(f"\n❌ [WATCHDOG] Ticket-Fehler: {r.text}")
    except Exception as e:
        print(f"\n❌ [WATCHDOG] API-Fehler: {e}")

    # Pipeline nach der Ticket-Erstellung automatisch neu starten
    print(f"\n🔄 [WATCHDOG] Starte Pipeline neu via run_pipeline.sh...")
    os.system("bash run_pipeline.sh &")
    sys.exit(0)

def follow_log(filename):
    if not os.path.exists(filename): open(filename, 'w').close()
    with open(filename, "r", encoding="utf-8", errors="ignore") as file:
        file.seek(0, os.SEEK_END)
        print(f"👀 Watchdog aktiv auf {filename}...")
        while True:
            line = file.readline()
            if not line:
                time.sleep(0.1)
                continue
            # Trigger auf Tracebacks ODER die Netzwerk-Fehlermeldung der Pipeline
            if "Traceback" in line or "NETZWERK-FEHLER" in line or "404 Client Error" in line:
                time.sleep(1) # Kurz warten bis Traceback fertig geschrieben ist
                raw_trace = line + "".join(file.readlines())
                try:
                    analysis = json.loads(analyze_error_with_llm(raw_trace))
                except:
                    analysis = {"is_critical": True, "summary": "Pipeline Crash (LLM Parse Error)"}
                if analysis.get("is_critical"):
                    create_multica_ticket(analysis.get("summary"), raw_trace)

if __name__ == "__main__":
    follow_log(sys.argv[1] if len(sys.argv) > 1 else LOG_FILE)
