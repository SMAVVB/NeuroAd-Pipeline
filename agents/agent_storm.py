import os
import sys
import glob
import sqlite3
import re
import time
import gc

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_core import ask_llm, MODEL_WORKHORSE

# ─── CHROMADB INSTALLATION CHECK ────────────────────────────────────────────
try:
    import chromadb
    CHROMADB_AVAILABLE = False
except ImportError:
    print("   ⚠️ ChromaDB nicht installiert. Installiere mit:")
    print("   pip install chromadb --break-system-packages")
    CHROMADB_AVAILABLE = False

# sentence-transformers für BGE-M3
try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False


def write_chapter_with_retry(prompt: str, label: str, max_retries: int = 3) -> str:
    """
    Hilfsfunktion für LLM-Calls mit Retry-Logik.
    Bei Exception oder Antwort < 100 Zeichen: 5 Sekunden warten, nochmal versuchen.
    Nach 3 Fehlversuchen: Kapitel-Text = "## ⚠️ UNVOLLSTÄNDIG: {chapter}\n[Kapitel konnte nach 3 Versuchen nicht generiert werden]\n"
    """
    for attempt in range(max_retries):
        try:
            result = ask_llm(prompt, "Schreibe das Kapitel.", MODEL_WORKHORSE)
            if len(result) >= 100:
                return result
            print(f"      ⚠️ Antwort zu kurz ({len(result)} Zeichen), versuche es erneut...")
        except Exception as e:
            print(f"      ⚠️ Exception beim Schreiben ({attempt+1}/{max_retries}): {e}")
        
        if attempt < max_retries - 1:
            print("      ⏳ Warte 5 Sekunden vor Retry...")
            time.sleep(5)
    
    # Nach 3 Fehlversuchen: Fallback-Text
    return f"## ⚠️ UNVOLLSTÄNDIG: {label}\n[Kapitel konnte nach 3 Versuchen nicht generiert werden]\n"


class LocalBGEEmbeddingFunction:
    """
    ChromaDB-kompatible Embedding-Funktion via lokaler sentence-transformers Installation.
    Lädt BGE-M3 direkt in den Python-Prozess — kein Lemonade nötig.
    """
    def __init__(self):
        self._model = None
    
    def _load(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                print("   🧠 Lade BGE-M3 via sentence-transformers...")
                self._model = SentenceTransformer("BAAI/bge-m3")
                print("   ✅ BGE-M3 geladen")
            except Exception as e:
                print(f"   ⚠️ sentence-transformers Fehler: {e}")
                self._model = None
        return self._model
    
    def __call__(self, input: list) -> list:
        model = self._load()
        if model is None:
            return [[0.0] * 1024] * len(input)
        try:
            embeddings = model.encode(input, batch_size=16, show_progress_bar=False)
            return embeddings.tolist()
        except Exception as e:
            print(f"   ⚠️ Embedding Fehler: {e}")
            return [[0.0] * 1024] * len(input)


def build_chroma_index(texts: list, sources: list, save_dir: str):
    """
    Baut ChromaDB Index aus Chunks. Nutzt lokales BGE-M3 via Lemonade Server.
    Persistiert auf Disk für Wiederverwendung.
    """
    if not CHROMADB_AVAILABLE:
        return None
    
    chroma_dir = os.path.join(save_dir, "chroma_db")
    client = chromadb.PersistentClient(path=chroma_dir)
    
    # Collection erstellen oder laden
    try:
        collection = client.get_collection("brand_knowledge")
        print(f"   📚 ChromaDB: Bestehende Collection geladen ({collection.count()} Chunks)")
        return collection
    except:
        pass
    
    # Local BGE-M3 Embedding-Funktion via sentence-transformers
    ef = LocalBGEEmbeddingFunction()
    print(f"   🧠 ChromaDB: Nutze BGE-M3 via sentence-transformers (lokal)")
    
    collection = client.create_collection(
        name="brand_knowledge",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Chunks in Batches hinzufügen
    BATCH_SIZE = 100
    total = len(texts)
    print(f"   📥 Indexiere {total} Chunks in ChromaDB...")
    
    for i in range(0, total, BATCH_SIZE):
        batch_texts = texts[i:i+BATCH_SIZE]
        batch_sources = sources[i:i+BATCH_SIZE]
        batch_ids = [f"chunk_{i+j}" for j in range(len(batch_texts))]
        
        collection.add(
            documents=batch_texts,
            metadatas=[{"source": s} for s in batch_sources],
            ids=batch_ids
        )
        
        # Speicher nach jedem Batch freigeben
        gc.collect()
        
        if i % 1000 == 0 and i > 0:
            print(f"      {i}/{total} Chunks indexiert...")
    
    print(f"   ✅ ChromaDB Index: {collection.count()} Chunks")
    return collection


def query_chroma(collection, query: str, n_results: int = 30, ef=None) -> tuple:
    """Führt ChromaDB Query aus. Gibt (texts, sources) zurück."""
    try:
        # Wenn ef vorhanden: manuell embedden und query_embeddings nutzen
        if ef is not None:
            query_embedding = ef([query])[0]
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, collection.count())
            )
        else:
            results = collection.query(
                query_texts=[query],
                n_results=min(n_results, collection.count())
            )
        texts = results["documents"][0]
        sources = [m["source"] for m in results["metadatas"][0]]
        return texts, sources
    except Exception as e:
        print(f"   ⚠️ ChromaDB Query Fehler: {e}")
        return [], []


def build_storm_wikipedia(brand: str, save_dir: str, seed_content: str = "", brand_profile: dict = None):
    """
    Multi-Query-RAG + Seed-Integration für STORM-Wissenssynthese.
    
    TASK 1a: Funktionssignatur erweitert mit seed_content Parameter
    TASK 1b: Multi-Query-RAG statt single TF-IDF query
    TASK 1c: Seed als Ground Truth in den Write-Prompt einbauen
    TASK 1d: Retry-Logic für LLM-Calls
    TASK 1e: Leere Kapitel detektieren
    TASK 1f: SQLite read mit txt-glob fallback
    TASK 2a: ChromaDB statt TF-IDF
    TASK 2b: 8 Haupt-Kapitel statt 5
    TASK 2c: Pro Kapitel bis zu 250 unique Chunks (5 Queries × 50)
    TASK 2d: Mindestens 800 Wörter pro Kapitel
    """
    print(f"\n🌪️ [PHASE 4] Starte STORM-Wissenssynthese (RAG Wikipedia Building)...")
    
    texts = []
    sources = []
    
    db_path = os.path.join(save_dir, "url_queue.sqlite")
    
    if os.path.exists(db_path):
        # Primär: aus SQLite lesen
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT url, content FROM chunks WHERE char_count > 200").fetchall()
        conn.close()
        for url, content in rows:
            texts.append(content)
            sources.append(url)
        print(f"   📚 SQLite: {len(texts)} Chunks geladen.")
    else:
        # Fallback: txt-glob (für Kompatibilität mit alten Runs)
        for file_path in glob.glob(os.path.join(save_dir, "url_*.txt")):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split('\n')
                if not lines:
                    continue
                url = lines[0].replace("URL: ", "").strip()
                body = "\n".join(lines[1:])
                
                chunk_size = 1500
                for i in range(0, len(body), chunk_size):
                    chunk = body[i:i+chunk_size].strip()
                    if len(chunk) > 200:
                        texts.append(chunk)
                        sources.append(url)
        print(f"   📚 txt-Fallback: {len(texts)} Chunks geladen.")
    
    if not texts:
        print("   ⚠️ Keine Textdaten für die RAG-Engine gefunden.")
        return
    
    print(f"   📚 RAG-Engine: {len(texts)} Text-Chunks indexiert.")
    
    # ChromaDB oder TF-IDF
    chroma_collection = None
    vectorizer = None
    tfidf_matrix = None
    
    if CHROMADB_AVAILABLE:
        chroma_collection = build_chroma_index(texts, sources, save_dir)
    
    if chroma_collection is None:
        # TF-IDF Fallback
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        print(f"   📊 TF-IDF Fallback: Indexiere {len(texts)} Chunks...")
        vectorizer = TfidfVectorizer(stop_words='english', max_features=50000)
        tfidf_matrix = vectorizer.fit_transform(texts)
    
    # Local BGE-M3 Embedding-Funktion für spätere Queries
    lemonade_ef = LocalBGEEmbeddingFunction() if CHROMADB_AVAILABLE else None
    
    # BGE-M3 einmal vorladen damit Lemonade danach freie Ressourcen hat
    if lemonade_ef is not None:
        print("   🧠 Vorladen BGE-M3 (einmalig)...")
        lemonade_ef._load()
        print("   ✅ BGE-M3 bereit — LLM-Server hat wieder freie Ressourcen")
        time.sleep(10)  # 10 Sekunden warten damit RAM sich stabilisiert
    
    def retrieve_chunks(query: str, n: int = 50) -> tuple:
        """Unified retrieval: ChromaDB oder TF-IDF."""
        if chroma_collection:
            return query_chroma(chroma_collection, query, n_results=n, ef=lemonade_ef)
        else:
            query_vec = vectorizer.transform([query])
            scores = cosine_similarity(query_vec, tfidf_matrix).flatten()
            top_idx = scores.argsort()[-n:][::-1]
            return [texts[i] for i in top_idx if scores[i] > 0.01], [sources[i] for i in top_idx if scores[i] > 0.01]
    
    # Kapitel-Struktur aus brand_profile oder Standard
    # Aus brand_profile Pillars ableiten wenn vorhanden
    outline_prompt = f"""Erstelle ein detailliertes Inhaltsverzeichnis für einen umfassenden Intelligence Report über '{brand}'.
 Struktur: Genau 8 Haupt-Kapitel, jedes mit 3-4 Unter-Kapiteln.
 Format: nummeriert, z.B. "1. Unternehmensgeschichte" dann "1.1 Gründung" etc.
 Gib NUR die Kapitel-Liste zurück."""
    
    outline = ask_llm(outline_prompt, "Erstelle detailliertes Inhaltsverzeichnis.", MODEL_WORKHORSE)
    
    # Haupt-Kapitel extrahieren
    main_chapters = [c.strip() for c in outline.split('\n')
                     if c.strip() and re.match(r'^\d+\.(?!\d)', c.strip())]
    
    # Unter-Kapitel extrahieren
    sub_chapters = [c.strip() for c in outline.split('\n')
                    if c.strip() and re.match(r'^\d+\.\d+', c.strip())]
    
    # Unter-Kapitel den Haupt-Kapiteln zuordnen
    chapter_map = {}
    current_main = None
    for line in outline.split('\n'):
        line = line.strip()
        if not line:
            continue
        if re.match(r'^\d+\.(?!\d)', line):
            current_main = line
            chapter_map[current_main] = []
        elif re.match(r'^\d+\.\d+', line) and current_main:
            chapter_map[current_main].append(line)
    
    if not main_chapters:
        main_chapters = [
            "1. Unternehmensgeschichte & Gründung",
            "2. Produkte & Portfolio",
            "3. Marketing & Kampagnen",
            "4. Finanzen & Investoren",
            "5. Wettbewerb & Marktposition",
            "6. Internationale Märkte",
            "7. Kontroversen & Kritik",
            "8. Management & Kultur"
        ]
    
    final_report = f"# 🌐 The Intelligence Report: {brand}\n\n"
    total_words = 0
    
    for chapter in main_chapters:
        print(f"   ✍️ Schreibe: {chapter}")
        
        # Unter-Kapitel für dieses Haupt-Kapitel
        subs = chapter_map.get(chapter, [])
        
        # 5 Sub-Queries für dieses Kapitel
        sub_query_prompt = f"Erstelle 5 spezifische Suchanfragen für '{chapter}' der Marke '{brand}'. Nur die 5 Queries, eine pro Zeile."
        sub_queries_text = ask_llm(sub_query_prompt, "Sub-Queries.", MODEL_WORKHORSE)
        sub_queries = [q.strip() for q in sub_queries_text.split('\n') if q.strip() and len(q.strip()) > 5][:5]
        while len(sub_queries) < 5:
            sub_queries.append(f"{brand} {chapter}")
        
        # Chunks sammeln: pro Sub-Query 50 Chunks → bis zu 250 unique
        all_chunk_texts = []
        all_chunk_sources = []
        seen = set()
        
        for sq in sub_queries:
            chunk_texts, chunk_sources = retrieve_chunks(sq, n=50)
            for t, s in zip(chunk_texts, chunk_sources):
                if t not in seen:
                    seen.add(t)
                    all_chunk_texts.append(t)
                    all_chunk_sources.append(s)
        
        # Kontext aufbauen (max 20.000 Zeichen)
        context = ""
        for t, s in zip(all_chunk_texts[:100], all_chunk_sources[:100]):
            if len(context) >= 20000:
                break
            context += f"QUELLE [{s}]:\n{t}\n\n"
        
        write_prompt = f"""Du bist ein wissenschaftlicher Analyst. Schreibe ein ausführliches Kapitel '{chapter}' für den Intelligence Report über '{brand}'.
 
 ANFORDERUNGEN:
 - Mindestens 800 Wörter
 - Nutze ALLE verfügbaren Quellen-Daten
 - Strukturiere mit Unter-Abschnitten (##)
 - Zitiere jede Behauptung: [Quelle: URL]
 - Keine Floskeln, nur Fakten und Analyse
 
 """
        if seed_content:
            write_prompt += f"SEED (Ground Truth):\n{seed_content[:2000]}\n\n---\n\n"
        
        write_prompt += f"QUELLEN-DATEN:\n{context}"
        
        chapter_text = write_chapter_with_retry(write_prompt, chapter, max_retries=3)
        word_count = len(chapter_text.split())
        total_words += word_count
        
        final_report += f"## {chapter}\n{chapter_text}\n\n"
        print(f"      → {word_count} Wörter (Haupt-Kapitel)")
        
        # Unter-Kapitel schreiben
        for sub in subs[:4]:  # Max 4 Unter-Kapitel pro Haupt-Kapitel
            print(f"      ✍️ Unter-Kapitel: {sub}")
            
            # Spezifische Chunks für Unter-Kapitel holen
            sub_chunks, sub_sources = retrieve_chunks(f"{brand} {sub}", n=30)
            sub_context = ""
            sub_seen = set()
            for t, s in zip(sub_chunks, sub_sources):
                if t not in sub_seen and len(sub_context) < 10000:
                    sub_seen.add(t)
                    sub_context += f"QUELLE [{s}]:\n{t}\n\n"
            
            sub_prompt = f"""Schreibe den Abschnitt '{sub}' für den Intelligence Report über '{brand}'.
Mindestens 400 Wörter. Nur Fakten aus den Quellen. Zitiere mit [Quelle: URL].

QUELLEN-DATEN:
{sub_context}"""
            
            if seed_content:
                sub_prompt = f"SEED (Ground Truth):\n{seed_content[:1000]}\n\n---\n\n" + sub_prompt
            
            sub_text = write_chapter_with_retry(sub_prompt, sub, max_retries=2)
            sub_word_count = len(sub_text.split())
            total_words += sub_word_count
            
            final_report += f"### {sub}\n{sub_text}\n\n"
            print(f"         → {sub_word_count} Wörter")
        
        if len(chapter_text.strip()) < 200 or "UNVOLLSTÄNDIG" in chapter_text:
            print(f"      ❌ Kapitel unvollständig: {chapter}")
    
    print(f"\n📊 Report-Statistik: {len(main_chapters)} Kapitel, {total_words:,} Wörter gesamt")
    
    report_path = os.path.join(save_dir, "Phase_4_STORM_Report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(final_report)
    
    print(f"✅ STORM-Report fertiggestellt: {report_path}")
