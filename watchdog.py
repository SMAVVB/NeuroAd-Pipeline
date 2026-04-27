import time
import requests
import json
import os
import sys
import hashlib
from dotenv import load_dotenv
import os
load_dotenv()

# Loop guard configuration
LOOP_GUARD_FILE = ".watchdog_loop_guard.json"
MAX_RETRIES = 3

# Konfiguration (Hier musst du nur deinen Key prüfen)
LOG_FILE = "campaigns/nike_summer_26_run.log"
OLLAMA_URL = "http://localhost:11434/api/generate"
WATCHDOG_MODEL = "qwen3.5:4b"
MULTICA_API_URL = "https://api.multica.ai/api/issues?workspace_slug=the-beast"
MULTICA_API_KEY = os.environ.get("MULTICA_API_KEY")


def get_loop_guard_state(error_summary):
    """Track error occurrences using MD5 hash of error_summary.
    Returns (current_count, is_loop) tuple.
    """
    error_hash = hashlib.md5(error_summary.encode('utf-8')).hexdigest()

    # Load existing state
    state = {}
    if os.path.exists(LOOP_GUARD_FILE):
        try:
            with open(LOOP_GUARD_FILE, 'r') as f:
                state = json.load(f)
        except:
            state = {}

    # Check if this is the same error as before
    if state.get("last_hash") == error_hash:
        current_count = state.get("count", 0) + 1
    else:
        current_count = 1

    # Update state
    state["last_hash"] = error_hash
    state["count"] = current_count

    # Write state file
    try:
        with open(LOOP_GUARD_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"[WATCHDOG] Could not write loop guard file: {e}")

    return current_count, current_count >= MAX_RETRIES


def analyze_error_with_llm(error_trace):
    prompt = f"Analysiere diesen Crash: {error_trace}. Antworte nur JSON: {{\"is_critical\": true, \"summary\": \"kurze Erklärung\"}}"
    try:
        res = requests.post(OLLAMA_URL, json={"model": WATCHDOG_MODEL, "prompt": prompt, "stream": False, "format": "json", "options": {"num_ctx": 2048}})
        return res.json().get("response", "{}")
    except: return '{"is_critical": false}'

def create_multica_ticket(error_summary, raw_trace):
    # Check for infinite loop before creating ticket
    current_count, is_loop = get_loop_guard_state(error_summary)

    if is_loop:
        print(f"\n🛑 [FATAL] INFINITE LOOP DETECTED - Same error {current_count}/{MAX_RETRIES} times. Stopping watchdog immediately.")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {MULTICA_API_KEY}", "Content-Type": "application/json"}

    payload = {
        "workspace_slug": "the-beast",
        "project_id": "e07a5476-d4c2-4665-b1fc-1cf2d1b0ba69",
        "assignee_type": "agent",
        "assignee_id": "710707d6-2484-4bd3-888a-7da10b6684f1",
        "title": f"🚨 Fix Needed ({current_count}/{MAX_RETRIES}): {error_summary}",
        "description": f"### Pipeline Crash Report\n\n**Fehler-Details:**\n```text\n{raw_trace}\n```",
        "priority": "high",
        "status": "todo"
    }

    url = "https://api.multica.ai/api/issues?workspace_slug=the-beast"
    ticket_id = None
    try:
        r = requests.post(url, json=payload, headers=headers)
        if r.status_code in [200, 201]:
            response_data = r.json()
            ticket_id = response_data.get("id")
            print(f"\n🚀 [WATCHDOG] Ticket erstellt und an den Universal-Agenten zugewiesen! ID: {ticket_id}")
        else:
            print(f"\n❌ [WATCHDOG] Ticket-Fehler: {r.text}")
    except Exception as e:
        print(f"\n❌ [WATCHDOG] API-Fehler: {e}")

    # Ticket-Abschluss abwarten mit Timeout von 160 Minuten
    if ticket_id:
        poll_watchdog_ticket(ticket_id)


def poll_watchdog_ticket(ticket_id):
    """Polls the Multica API to check if the ticket is resolved."""
    timeout_seconds = 160 * 60  # 160 Minuten
    poll_interval = 60  # 60 Sekunden
    elapsed = 0

    print(f"\n⏳ [WATCHDOG] Warte auf Ticket-Abschluss (Timeout: {timeout_seconds} Sekunden)...")

    while elapsed < timeout_seconds:
        try:
            # Ticket status abfragen
            status_url = f"https://api.multica.ai/api/issues/{ticket_id}?workspace_slug=the-beast"
            headers = {"Authorization": f"Bearer {MULTICA_API_KEY}"}
            r = requests.get(status_url, headers=headers)

            if r.status_code == 200:
                response_data = r.json()
                status = response_data.get("status", "").lower()

                # Prüfen auf Abschluss-Status
                if status in ["done", "completed", "resolved", "closed"]:
                    print(f"\n✅ [WATCHDOG] Ticket ist erledigt (Status: {status}). Starte Pipeline neu...")
                    break
                else:
                    print(f"📋 [WATCHDOG] Ticket Status: {status} - warte {poll_interval} Sekunden...")
            else:
                print(f"⚠️ [WATCHDOG] Status-Abfrage fehlgeschlagen: {r.status_code} {r.text}")

        except Exception as e:
            print(f"⚠️ [WATCHDOG] API-Fehler bei Status-Abfrage: {e}")

        # Wartezeit bis zur nächsten Abfrage
        time.sleep(poll_interval)
        elapsed += poll_interval

    # Timeout erreicht
    if elapsed >= timeout_seconds:
        print(f"\n[FATAL] [WATCHDOG] Timeout von 160 Minuten erreicht. Ticket nicht rechtzeitig erledigt.")
        sys.exit(1)

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
