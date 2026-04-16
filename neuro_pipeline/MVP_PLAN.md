# NeuroAd Pipeline — MVP Plan

**Stand:** 5. April 2026
**Hardware:** The Beast (AMD Strix Halo, Ryzen AI MAX+ 395, 96 GB Unified Memory, Ubuntu 24.04)
**Venv:** `~/neuro_pipeline_project/venv_rocm` (Python 3.12, PyTorch 2.11+rocm7.11)
**Scope:** Pipeline A — bestehende Werbung analysieren, keine Generierung

---

## Aktueller Infrastruktur-Status

| Komponente | Status | Anmerkung |
|---|---|---|
| GPU/ROCm (Radeon 8060S) | ✅ | Performance Mode via `rocm-smi --setperflevel high` |
| TRIBE v2 (GPU) | ✅ | Läuft stabil, device-fix implementiert, OOM-Schutz aktiv |
| ViNet-S Saliency | ✅ | 36 MB, ~7s/Video, DHF1K Weights |
| CLIP Brand Consistency | ✅ | ViT-B/32, GPU |
| HSEmotion Facial Emotion | ✅ | weights_only Patch angewandt |
| Brain-Visualisierung | ✅ | 4-Panel LH/RH + Temporal Profile via Nilearn |
| Pipeline A Runner | ✅ | End-to-End lauffähig, Caching aktiv |
| **MiroFish + Neo4j 5.18** | ✅ | **API Wrapper fertig! Sledgehammer-Patch für IPC-Timeouts (900s) aktiv.** |
| **Lemonade SDK** | ✅ | **Port 8888, betreibt SOTA-Modelle (GLM-4.7-Flash) + agiert als LLM-Scoring-Brücke.** |
| DeepGaze IIE | ❌ | Bitbucket URLs tot — dauerhaft aus Scope entfernt |

---

## Projektdateien

    ~/neuro_pipeline_project/
    ├── model_manager.py        ← TRIBE v2 Inferenz
    ├── saliency_scorer.py      ← ViNet-S Wrapper
    ├── pipeline_runner.py      ← Pipeline A Orchestrator (End-to-End)
    ├── mirofish_client.py      ← MiroFish API Wrapper + Local LLM JSON-Scoring
    ├── visualize_brain.py      ← Brain Map + Temporal Profile
    ├── apply_patches.sh        ← Reproduzierbare Patches (inkl. Sledgehammer-Doku)
    └── tools/                  ← Lokale Submodule

---

## Kritische Patches & Fixes (Historie)

### 1. TRIBE v2 (Gelöst)
* **Bug:** `Expected all tensors to be on the same device` & OOM bei langen Videos.
* **Fix:** `_model.to('cuda')` Reihenfolge korrigiert + `PYTORCH_ALLOC_CONF=expandable_segments:True`. Videos sollten auf max 90s getrimmt werden.

### 2. MiroFish Backend Timeouts (Gelöst 05.04.26)
* **Bug:** Docker-Container crasht intern nach 180s bei komplexen Agenten-Interviews.
* **Fix ("The Sledgehammer"):** Hardcoded Limit direkt im Container gepatched.
  `docker exec -it mirofish-offline sed -i 's/timeout=180.0/timeout=900.0/g' /app/backend/app/services/simulation_ipc.py`
* **Client-Fix:** `max_retries` in `mirofish_client.py` für Simulation auf 360 (90 Min) erhöht.

### 3. MiroFish Qualitative Scoring (Gelöst 05.04.26)
* **Bug:** MiroFish gibt qualitativen Markdown-Report aus, Pipeline erwartet JSON-Scores.
* **Fix:** `mirofish_client.py` holt Markdown-Report und sendet ihn via API-Call (`/v1/chat/completions`) an das lokale Lemonade LLM. Das Modell extrahiert die echten Scores (`positive_sentiment`, `virality_score`, etc.) als JSON.

---

## Scoring-Module Übersicht

* **TRIBE v2 (Neurale Response):** ROI-Scores (TPJ, FFA, etc.) + `neural_engagement`
* **ViNet-S (Visuelle Aufmerksamkeit):** Saliency Heatmap PNG + `center_bias` + ROI-Scores
* **CLIP (Brand Consistency):** `brand_match_score` (0-1) + `top_label`
* **HSEmotion (Facial Emotion):** `dominant_emotion`, `emotional_valence` (-1 bis 1)
* **MiroFish (Social Simulation):** Liefert finalen Markdown-Report (`mirofish_final_report.md`) + evaluierte Scores via LLM (`social_sentiment`, `virality_score`, `controversy_risk`).

*(Hinweis: Composite Score Gewichtung in `pipeline_runner.py` ist nun vollständig an echte API-Daten angebunden).*

---

## MVP Fortschritt & Zeitplan

### Kürzlich abgeschlossen ✅
- [x] TRIBE v2 device-Mismatch und OOM-Bugs gefixt.
- [x] MiroFish API Wrapper geschrieben und integriert.
- [x] MiroFish Docker-Timeouts behoben.
- [x] Lokale LLM-Scoring-Brücke (Lemonade) für Text-to-JSON Extraktion gebaut.
- [x] Erster Apple vs. Samsung A/B Test End-to-End erfolgreich beendet!

### Was diese Woche noch fehlt für MVP

| Task | Aufwand | Priorität |
|---|---|---|
| **Code auf GitHub syncen** | 15 Min | **SOFORT** |
| Asset-Trim automatisieren (max 90s) | 1h | Hoch |
| Streamlit Dashboard Grundgerüst | 3-4h | Hoch |
| Brain Maps + Saliency im Dashboard | 2h | Mittel |
| Score-Tabelle + Ranking im Dashboard | 1h | Mittel |
| Datenbank (SQLite/Supabase) anbinden | 2h | Niedrig (Post-MVP Option) |

---

## Offene Entscheidungen & Skalierung

- [ ] **Modell-Wechsel für 100+ Agenten:** Das aktuell genutzte *GLM-4.7-Flash* ist extrem tiefgründig, aber zu langsam für Massen-Skalierung. Vor dem Stresstest mit hunderten Agenten muss auf ein diszipliniertes, schnelles Modell wie **Qwen 3.5 (9B)** oder **Gemma 4 Instruct** gewechselt werden.
- [ ] **Dashboard-Hosting:** Streamlit lokal + Tailscale (schnellster Weg) oder nginx?
- [ ] **Asset-Längen-Limit:** Hard-Cut bei 60s oder 90s im Code definieren?