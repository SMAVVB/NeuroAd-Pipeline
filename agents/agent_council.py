import os
import sys

# Erlaubt den Import aus dem Hauptverzeichnis
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_core import ask_llm, MODEL_JUDGE, MODEL_FAST

def run_council_review(brand: str, save_dir: str):
    print(f"\n⚖️ [PHASE 5] Der Rat tritt zusammen (Executive Council Review)...")

    # Lade den fertigen Report
    report_path = os.path.join(save_dir, "Phase_4_STORM_Report.md")
    if not os.path.exists(report_path):
        print("   ⚠️ Kein STORM-Report gefunden. Council bricht ab.")
        return

    with open(report_path, "r", encoding="utf-8") as f:
        storm_report = f.read()

    # SCHRITT 1 — Gemma 4 analysiert den Report (schnell, 10 TPS)
    print("   🧐 SCHRITT 1: Gemma 4 analysiert den Report (Fakten, Lücken, Stärken)...")

    analysis_prompt = f"""Du bist der Chief Quality Officer.
Lies dir den folgenden, von Agenten generierten RAG-Report zur Marke '{brand}' durch.

Deine Aufgabe:
1. FACT-CHECK: Sind die zitierten Informationen (Zahlen, Daten, Historie) nach deinem internen Wissen korrekt?
2. VOLLSTÄNDIGKEIT: Fehlen massive, markendefinierende Aspekte, die ein Analyst wissen müsste?
3. BEWERTUNG: Gib dem Report eine Note von 1 bis 10.

Output: Strukturiere deine Analyse als JSON mit den Keys 'facts_checked', 'gaps_found', 'strengths', 'rating'."""

    analysis_result = ask_llm(analysis_prompt, storm_report, MODEL_FAST)

    print("   ✅ SCHRITT 1 abgeschlossen. Erstelle Management-Summary...")

    # SCHRITT 2 — Kimi Linear 48B schreibt das Audit-Protokoll
    # (schneller weil Input viel kleiner ist)
    audit_prompt = f"""Du bist der Chief Quality Officer.
Nutze die folgende strukturierte Analyse, um ein professionelles Management-Summary zu schreiben.

ANALYSE:
{analysis_result}

Deine Aufgabe:
Schreibe ein präzises Audit-Protokoll (max. 300 Wörter) als Management-Summary für den Vorstand.
Das Protokoll soll die wichtigsten Erkenntnisse der Prüfung zusammenfassen.

Format: Reines Markdown, keine JSON-Ausgabe."""

    audit_result = ask_llm(audit_prompt, "Erstelle das Management-Summary.", MODEL_FAST, timeout_override=1800)

    audit_path = os.path.join(save_dir, "Phase_5_Council_Audit.md")
    with open(audit_path, "w", encoding="utf-8") as f:
        f.write(audit_result)

    print(f"✅ Council-Audit abgeschlossen! Gespeichert als 'Phase_5_Council_Audit.md'.")
