import os
import sys

# Erlaubt den Import aus dem Hauptverzeichnis
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_core import ask_llm, MODEL_JUDGE

def run_council_review(brand: str, save_dir: str):
    print(f"\n⚖️ [PHASE 5] Der Rat tritt zusammen (Executive Council Review)...")
    
    # Lade den fertigen Report
    report_path = os.path.join(save_dir, "Phase_4_STORM_Report.md")
    if not os.path.exists(report_path):
        print("   ⚠️ Kein STORM-Report gefunden. Council bricht ab.")
        return
        
    with open(report_path, "r", encoding="utf-8") as f:
        storm_report = f.read()
        
    print("   🧐 DeepSeek R1 prüft den finalen Report auf Wahrheit, Lücken und Relevanz...")
    
    council_prompt = f"""Du bist der Chief Quality Officer. 
    Lies dir den folgenden, von Agenten generierten RAG-Report zur Marke '{brand}' durch.
    
    Deine Aufgabe:
    1. FACT-CHECK: Sind die zitierten Informationen (Zahlen, Daten, Historie) nach deinem internen Wissen korrekt?
    2. VOLLSTÄNDIGKEIT: Fehlen massive, markendefinierende Aspekte, die ein Analyst wissen müsste?
    3. BEWERTUNG: Gib dem Report eine Note von 1 bis 10.
    
    Verfasse eine präzise, professionelle Management-Summary (max. 300 Wörter) deiner Prüfung.
    Korrigiere keine Texte, sondern schreibe ein Audit-Protokoll, das man dem Vorstand vorlegen kann.
    
    REPORT:
    {storm_report}"""
    
    # Wir nutzen hier zwingend das JUDGE Modell (DeepSeek)
    audit_result = ask_llm(council_prompt, f"Prüfe den Report für {brand}", MODEL_JUDGE)
    
    audit_path = os.path.join(save_dir, "Phase_5_Council_Audit.md")
    with open(audit_path, "w", encoding="utf-8") as f:
        f.write(audit_result)
        
    print(f"✅ Council-Audit abgeschlossen! Gespeichert als 'Phase_5_Council_Audit.md'.")
