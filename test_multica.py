import requests
import os
from dotenv import load_dotenv

load_dotenv()
MULTICA_API_KEY = os.environ.get("MULTICA_API_KEY")
MULTICA_API_URL = "https://api.multica.ai/api/issues"

if not MULTICA_API_KEY:
    print("❌ FEHLER: API_KEY fehlt in der .env!")
    exit(1)

payload = {
    "workspace_slug": "the-beast",
    "title": "🧪 SYSTEM-TEST: Watchdog Setup",
    "description": "Nachtschicht-Test für The Beast.",
    "project": "NeuroAd-Pipeline"
}

headers = {"Authorization": f"Bearer {MULTICA_API_KEY}", "Content-Type": "application/json"}

res = requests.post(MULTICA_API_URL, json=payload, headers=headers)
if res.status_code in [200, 201]:
    print("✅ MULTICA VERBINDUNG STEHT! Gute Nacht!")
else:
    print(f"❌ FEHLER {res.status_code}: {res.text}")
