import requests
import json

# Konfiguration
PROJECT_ID = "proj_0efadc2567cf" 
URL = "http://localhost:5001/api/graph/build"

print(f"--- Test Step 2: Build Graph for {PROJECT_ID} ---")
try:
    # Wir senden die Project ID an den Build-Endpoint
    res = requests.post(URL, json={"project_id": PROJECT_ID}, timeout=30)
    print(f"Status: {res.status_code}")
    
    if res.status_code == 200:
        data = res.json()
        print("Response JSON:")
        print(json.dumps(data, indent=2))
        
        # Überprüfung der Struktur für den MiroFishClient
        if "data" in data and "graph_id" in data["data"]:
            print(f"\n✅ Struktur erkannt! Graph ID: {data['data']['graph_id']}")
        elif "graph_id" in data:
            print(f"\n✅ Struktur erkannt (ohne 'data' Key)! Graph ID: {data['graph_id']}")
        else:
            print("\n⚠️ 'graph_id' nicht gefunden. Bitte prüfe die obige Struktur.")
    else:
        print(f"Fehler vom Server: {res.text.strip()}")
        
except Exception as e:
    print(f"Verbindungsfehler: {e}")
