from neo4j import GraphDatabase

# Zugriff vom Host-System auf den Docker-Container
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "mirofish") # Deine Credentials aus der .env

class BrandGraphManager:
    def __init__(self, uri, auth):
        print("🔌 Verbinde mit lokaler Neo4j Datenbank...")
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        self.driver.close()

    def ingest_brand_context(self, brand_data: dict):
        """Schreibt das vom LLM generierte JSON als Graph in Neo4j."""
        query = """
        // 1. Erstelle oder aktualisiere den Brand-Knoten
        MERGE (b:Brand {name: $brand_name})
        SET b.dna = $brand_dna,
            b.visual_style = $visual_style,
            b.tone_of_voice = $tone_of_voice
            
        // 2. Erstelle Kernaussagen und verknüpfe sie
        WITH b
        UNWIND $key_messages AS msg
        MERGE (k:KeyMessage {text: msg})
        MERGE (b)-[:COMMUNICATES]->(k)
        
        // 3. Füge die CLIP-Labels für die visuelle Pipeline hinzu
        WITH b
        UNWIND $clip_labels AS label
        MERGE (c:ClipLabel {text: label})
        MERGE (b)-[:HAS_VISUAL_LABEL]->(c)
        """
        
        with self.driver.session() as session:
            session.run(query, 
                        brand_name=brand_data.get("brand_name", "Unknown"),
                        brand_dna=brand_data.get("brand_dna", ""),
                        visual_style=brand_data.get("visual_style", ""),
                        tone_of_voice=brand_data.get("tone_of_voice", ""),
                        key_messages=brand_data.get("key_messages", []),
                        clip_labels=brand_data.get("clip_labels", []))
            print(f"✅ Brand '{brand_data.get('brand_name')}' erfolgreich als Graph in Neo4j integriert!")

# ==========================================
# 🚀 TEST-LAUF (Direkt ausführbar)
# ==========================================
if __name__ == "__main__":
    # Simulierter Output deines Qwen 2.5 32B Research Agenten
    test_data = {
        "brand_name": "Apple",
        "brand_dna": "Innovation, Minimalismus und die Schnittstelle zwischen Technologie und Geisteswissenschaften.",
        "visual_style": "Viel Weißraum, San Francisco Font, kühle Grautöne, hochauflösende Produkt-Closeups.",
        "tone_of_voice": "Selbstbewusst, inspirierend, simpel, fokussiert auf das 'Warum' statt das 'Wie'.",
        "key_messages": [
            "Think Different.",
            "Privacy. That's Apple.",
            "Pro cameras. Pro display. Pro performance."
        ],
        "clip_labels": [
            "minimalist tech product",
            "sleek design",
            "premium quality electronics",
            "clean white background"
        ]
    }

    # Wenn du 'pip install neo4j' im venv_rocm gemacht hast, läuft das hier direkt durch:
    try:
        manager = BrandGraphManager(URI, AUTH)
        manager.ingest_brand_context(test_data)
        manager.close()
    except Exception as e:
        print(f"❌ Fehler bei der Verbindung: {e}\n(Ist der MiroFish-Container gestartet?)")
