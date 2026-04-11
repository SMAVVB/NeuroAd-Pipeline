import os
import sys
import glob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_core import ask_llm, MODEL_WORKHORSE

def build_storm_wikipedia(brand: str, save_dir: str):
    print(f"\n🌪️ [PHASE 4] Starte STORM-Wissenssynthese (RAG Wikipedia Building)...")
    
    texts = []
    sources = []
    
    for file_path in glob.glob(os.path.join(save_dir, "url_*.txt")):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            lines = content.split('\n')
            if not lines: continue
            url = lines[0].replace("URL: ", "").strip()
            body = "\n".join(lines[1:])
            
            chunk_size = 1500
            for i in range(0, len(body), chunk_size):
                chunk = body[i:i+chunk_size].strip()
                if len(chunk) > 200:
                    texts.append(chunk)
                    sources.append(url)
                    
    if not texts:
        print("   ⚠️ Keine Textdaten für die RAG-Engine gefunden.")
        return

    print(f"   📚 RAG-Engine: {len(texts)} Text-Chunks indexiert.")
    
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(texts)
    
    outline_prompt = f"Erstelle ein Inhaltsverzeichnis (genau 5 Kapitel-Titel) für einen ultimativen Wikipedia-Artikel über die Marke '{brand}'. Von Finanzen bis Skandale."
    outline = ask_llm(outline_prompt, "Gib nur die 5 Titel aus, nummeriert.", MODEL_WORKHORSE)
    
    chapters = [c.strip() for c in outline.split('\n') if c.strip() and c[0].isdigit()]
    
    # DAS SICHERHEITSNETZ:
    if not chapters:
        print("   ⚠️ Inhaltsverzeichnis konnte nicht extrahiert werden. Nutze Notfall-Struktur.")
        chapters = [
            "1. Unternehmenshistorie", 
            "2. Marktposition & Finanzen", 
            "3. Internationale Strategie", 
            "4. Marketing & Kampagnen", 
            "5. Kritik & Kontroversen"
        ]
    
    final_report = f"# 🌐 The STORM Intelligence Report: {brand}\n\n"
    
    for chapter in chapters:
        print(f"   ✍️ Gemma 4 schreibt: {chapter}")
        
        query_vec = vectorizer.transform([f"{brand} {chapter}"])
        scores = cosine_similarity(query_vec, tfidf_matrix).flatten()
        top_indices = scores.argsort()[-5:][::-1] 
        
        context = ""
        for idx in top_indices:
            if scores[idx] > 0.02:
                context += f"QUELLE [{sources[idx]}]:\n{texts[idx]}\n\n"
        
        write_prompt = f"""Du bist ein wissenschaftlicher Autor. Schreibe das Kapitel '{chapter}' für die Marke '{brand}'.
        Nutze AUSSCHLIESSLICH diese verifizierten Rohdaten-Ausschnitte. 
        FEYNMAN-REGEL: Zitiere jede Behauptung zwingend am Ende des Satzes im Format [Quelle: URL].
        
        DATEN-AUSDZÜGE:
        {context}"""
        
        chapter_text = ask_llm(write_prompt, "Schreibe das Kapitel.", MODEL_WORKHORSE)
        final_report += f"## {chapter}\n{chapter_text}\n\n"
        
    report_path = os.path.join(save_dir, "Phase_4_STORM_Report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(final_report)
        
    print(f"✅ STORM-Report fertiggestellt! Gespeichert als 'Phase_4_STORM_Report.md'.")
