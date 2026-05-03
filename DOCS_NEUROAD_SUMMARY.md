# NeuroAd-Pipeline — Dokumentations-Zusammenfassung

**Erstellt:** 2026-05-02  
**Letzte Aktualisierung:** 2026-05-02 (Feedback-Schleife 1)  
**Stand:** Commit 5d032bc (1. Mai 2026)  
**Quelle:** /home/vincent/neuro_pipeline_project

---

## 1. Überblick

NeuroAd ist eine **lokal laufende Neuromarketing-Analyse-Plattform** auf "The Beast" (AMD Strix Halo, 96GB RAM, Ubuntu 24.04).

**Kernprinzip:** NeuroAd ist ein **Entscheidungshilfe-Tool, kein Orakel**. Relativer Vergleich zwischen Creatives ist valide (z.B. "Creative A aktiviert emotionales Zentrum 23% stärker als B"), absolute Vorhersagen (z.B. "50% mehr Conversions") nicht.

### Zwei Pipelines

| Pipeline | Status | Beschreibung |
|---|---|---|
| **Pipeline A (MVP)** | ✅ Komplett | Analyse bestehender Werbung |
| **Pipeline B (Post-MVP)** | 🔄 Geplant | AI-generierte Kampagnen |

---

## 2. Architektur (Aktuell)

```
                    Brand Research Agent (über Pipeline A)
                            │
                            ▼
┌─────────────────────────────────────────────────┐
│              Brand Orchestrator                  │
│  (brand_orchestrator.py / brand_research_agent.py) │
├─────────────────────────────────────────────────┤
│  Phasen: 0.1 (Web) → 0.2 (Baseline) → 0.3      │
│         → Brand-Profile → Research → STORM       │
│         Report → Council Review                 │
└─────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────┐
│              Pipeline A (Analyse)                │
├─────────────────────────────────────────────────┤
│  Input: Ad Assets (Video/Bild)                  │
│      │                                            │
│      ├─ TRIBE v2         → neurale Response     │
│      ├─ ViNet-S/A        → visuelle Aufmerksamk.│
│      ├─ CLIP             → Brand Consistency    │
│      ├─ HSEmotion        → Facial Emotion       │
│      ├─ MiroFish API     → Social Simulation    │
│      │                                            │
│      └─ Composite Score  → Report + Brain Maps  │
└─────────────────────────────────────────────────┘
                            │
                            ▼
                Analyse Agent (Score-Auswertung)
```

**Start-Mechanismus:**
- **Terminal 1:** Watchdog (infinite loop guard)
- **Terminal 2:** Starter-Skript → startet Pipeline parallel
- Bei Fehler im Pipeline-Run → Watchdog erstellt Multica-Ticket

---

## 3. Scoring-Module Pipeline A

### 3.1 TRIBE v2 — Neurale Response
- **Funktion:** Vorhersage menschlicher Gehirnreaktion (fMRI-Simulation über 20.484 kortikale Vertices)
- **Laufzeit:** ~8 Min/Video
- **ROI-Scores:** TPJ, FFA, PPA, V5/MT, Broca, A1, V1
- **Limitierungen:** ~8 Min/Video, Population-Level (kein Demografie-Split), CC BY-NC Lizenz
- **Status:** ✅ Stabil, OOM-Schutz aktiv

### 3.2 ViNet-S/A — Visuelle Aufmerksamkeit
- **Funktion:** Saliency Heatmap PNG + ROI-Scores
- **Laufzeit:** ~7s/Video
- **Version:** ViNet-S (DHF1K Weights)
- **Upgrade:** ViNet-A (Audio-Visual) optional
- **Status:** ✅ Mit realen Daten im Dashboard V2

### 3.3 CLIP — Brand Consistency
- **Funktion:** ViT-B/32, Cosine Similarity zum Brand-Profil
- **Laufzeit:** ~2s/Asset
- **Output:** brand_match_score (0-1), top_label, all_scores
- **Status:** ✅ Mit realen Daten im Dashboard V2

### 3.4 HSEmotion — Facial Emotion
- **Funktion:** enet_b0_8_best_afew Modell
- **Laufzeit:** ~5s/Video
- **Output:** dominant_emotion, emotional_valence (-1 bis 1), face_coverage, emotion_distribution
- **Status:** ✅ Lauffähig

### 3.5 MiroFish — Social Simulation
- **Funktion:** Multi-Agent-Simulation über lokale API (localhost:5001/api)
- **Timeout:** 900s (via Sledgehammer-Patch im Docker-Container)
- **LLM-Scoring:** Sentiment, Virality, Controversy via Qwen 3.6 (JSON-Extraktion)
- **Auto-Retry:** 360 Versuche max (fix in pipeline_runner.py)
- **Fallback:** Bei 0 Entities oder Failed Status → neutrale Defaults (0.5)
- **Output:** mirofish_final_report.md + llm_scores JSON
- **Status:** ✅ Stabil, Report-Seite im Dashboard V2 verifiziert

### 3.6 Composite Score
- **Gewichtung:** neural_engagement (0.25), emotional_impact (0.15), visual_attention (0.20), brand_consistency (0.15), social_sentiment (0.10), facial_emotion (0.10), audio_engagement (0.05)
- **Ausgabe:** Total-Score (0-1), Grade (A-D), Breakdown
- **Fehlende Module:** Default 0.5 (neutral)

---

## 4. Brand Research Pipeline (Pipeline B Vorschau)

### 4.1 brand_orchestrator.py — Master-Orchestrator
- Ruft alle Sub-Agents sequentiell auf
- Aggressive GC zwischen Phasen (gc.collect + torch.cuda.empty_cache())
- **Achtung:** Brand Orchestrator hat ein übergeordnetes Starter-Skript/file (in Commits zu finden)

### 4.2 Sub-Agents

| Agent | Funktion | Model (Aktuell) |
|---|---|---|
| **agent_baseline** | Makro-Fundament + Web-Kontext | **Qwen 3.6** (Ollama) |
| **agent_profile** | Brand-Profil JSON | **Qwen 3.6** (kein 2. Modell mehr) |
| **agent_scraper** | Web-Spider mit SQLite-URL-Queue | — (curl_cffi + lxml) |
| **agent_storm** | STORM Report Generator | **Qwen 3.6** (Retry-Logic) |
| **agent_science** | Semantic Scholar Paper-Suche | Semantic Scholar API |
| **agent_archive** | Wayback Machine + Archive.ph | curl_cffi (Async) |
| **agent_social** | YouTube Discovery | SearXNG + yt-dlp |
| **agent_publisher** | Mandatory Pillars Research | Crawl4AI Async |
| **agent_council** | Executive Council Review | **Qwen 3.6** (keine 2-stufige Prüfung) |

**Wichtig:** Aktuell läuft **alles über Qwen 3.6** (Ollama). Gamma 4, DeepSeek R1 und Kimi sind **nicht mehr im Einsatz**.

### 4.3 Brand Graph Manager
- **brand_graph_manager.py:** URI/AUTH für Brand-Graph Storage
- **brand_research_agent.py:** Phase 0 + 1 (Baseline + Suchbaum)

---

## 5. Infrastruktur

### 5.1 config_core.py — Zentrale Konfiguration

**ACHTUNG:** config_core.py ist **veraltet** — zeigt noch Lemonade/Proxy-Konfiguration.

Aktueller Stack: **Ollama** (kein Proxy, kein Lemonade mehr).

### 5.2 Pipeline Runner (pipeline_runner.py)

**Module (optional via --skip/--only):** tribe, saliency, clip, emotion, mirofish

**Cache-System:** Jeder Module-Output wird als JSON gecached (scores_dir/{asset}_scores.json)

**LLM Server Reset:** Funktion in pipeline_runner.py bezieht sich auf Lemonade — **veraltet** (kein Lemonade mehr)

**Default Config:** Alle Module standardmäßig aktiv, ROI-Bounding-Boxes via CLI (--roi)

### 5.3 Model Manager (model_manager.py)

- **SequentialTribeScorer:** Lädt TRIBE v2 Model nur temporär (GPU-Freigabe nach jedem Asset)
- **Memory Utilities:** get_ram_usage_gb(), get_gpu_usage_gb()
- **OOM Protection:** PYTORCH_ALLOC_CONF=expandable_segments:True

### 5.4 Dashboard V2 — Aktuelles Dashboard

**Nur Dashboard V2 ist aktuell** (Dashboard V1/Streamlit irrelevant):

**dashboard_v2/** — Next.js (v0), Port 3000/3002, mit:
- Sidebar mit Campaign Selector + Dark Mode
- Overview Page mit D3 Force Graph (MiroFish Agents)
- Brain Viewer (TRIBE 3D, LH/RH 4-Panel + Temporal Profile)
- CLIP Radar Chart (reale all_scores Daten)
- ViNet Heatmap (reale Saliency Maps)
- Report Page mit dynamischen API-Daten
- FastAPI Backend (port 8080)

---

## 6. Watchdog System

### watchdog.py — Infinite Loop Guard
- **MD5 Hash:** Fehler-Hash mit Location-aware (file + line number)
- **MAX_RETRIES:** 3 Wiederholungen
- **Loop Guard File:** .watchdog_loop_guard.json
- **Ticket-Erstellung:** via Multica API (THE-95, THE-94 etc.)
- **Timeout:** 160 Minuten Wartezeit auf Ticket-Abschluss
- **Pre-flight:** Prüft Ticket-Status vor Pipeline-Restart
- **Start:** Läuft in eigenem Terminal parallel zur Pipeline

---

## 7. Token Tracking — ❌ Entfallen

Token Tracking ist **nicht mehr relevant**:
- Kein Token Tracking mehr möglich auf Ollama (nur OpenClaw/Claude Code trackbar)
- tools/token_tracker.py und Proxy-Logging veraltet
- tools/token_tracker.py kann entfernt werden

---

## 8. Aktuelle Commit-Historie (letzte 8 Commits)

| Commit | Datum | Beschreibung |
|---|---|---|
| **5d032bc** | 1.5. | Aggressive GC zwischen Pipeline-Phasen (OOM-Schutz) |
| **19897ae** | 1.5. | Watchdog Loop Guard mit Location-aware hashing |
| **120b5d7** | 1.5. | MiroFish Client Auto-Retry + Fallback Werte |
| **f9a3e4a** | 1.5. | MiroFish Failed-Status Handling (keine Infinite Loops) |
| **a3f1161** | 1.5. | Invalid timeout_override Fix in agent_council.py |
| **1326953** | 1.5. | Checkpoint System für Pipeline Resilience |
| **a5929a9** | 1.5. | Pre-flight script check vor Pipeline-Restart |
| **d16cf85** | 1.5. | Infinite Loop Guard gegen wiederholte Pipeline-Crashes |

**Branches:**
- **main** (aktuell)
- **fix/mirofish-polling-loop** (Feature Branch, divergiert von main)

---

## 9. Bekannte Limitierungen

1. **GPU-Contention:** Nur ein Modell gleichzeitig auf GPU (96GB Unified Memory)
2. **TRIBE v2:** ~8 Min/Video, Population-Level, CC BY--NC Lizenz
3. **MiroFish Docker:** Timeout-Patch via Sledgehammer (docker exec sed -i)
4. **Kein 2. Modell:** Brand Profile validiert nur über Qwen 3.6
5. **Kein Token Tracking:** Auf Ollama nicht möglich
6. **config_core.py veraltet:** Zeigt Lemonade/Proxy statt Ollama
7. **Pipeline Runner veraltet:** LLM Reset-Code bezieht sich auf Lemonade

---

## 10. Veraltete Komponenten

### Dateien
- `pipeline_runner_old.py` — Alte Pipeline-Version
- `dashboard_v2_old/` — Veraltete Dashboard-Variante

### Komponenten (nicht mehr im Einsatz)
- ❌ **Lemonade SDK** — Kein Lemonade mehr
- ❌ **Proxy (Port 9002/9003 → 8888)** — Direkte Ollama-Kommunikation
- ❌ **Gemma 4, DeepSeek R1, Kimi Linear 48B** — Nicht mehr konfiguriert
- ❌ **Token Tracking** — Auf Ollama nicht möglich
- ❌ **Dashboard V1 (Streamlit)** — Nur V2 aktuell

---

## 11. Beispiel-Kampagnen

- **Nike Summer 26:** campaigns/nike_summer_26_run/
  - nike_clip_A.mp4, nike_clip_B.mp4 (echte_test_assets/)
  - Full Pipeline A Output in report/ und scores/

---

## 12. Multica Integration

- **Workspace:** the-beast (a5271b2f...)
- **API:** https://api.multica.ai/api/issues?workspace_slug=the-beast
- **API-Key:** mul_60eb5a4547ccb85f11e35cd588e7b724e6eb5c90
- **Project ID:** e07a5476-d4c2-4665-b1fc-1cf2d1b0ba69
- **Agent ID:** 710707d6-2484-4bd3-888a-7da10b6684f1

### Ticket-Historie (Auswahl)

| ID | Titel | Status |
|---|---|---|
| THE-12 | Fix Phase 5 Council Audit | done |
| THE-13 | YouTube Channel Discovery | done |
| THE-14 | Pipeline Module-Upgrade Prep | done |
| THE-17 | Lemonade Universal Token Tracker | done |
| THE-92 | MiroFish Client Auto-Retry | in_review |
| THE-93 | Watchdog Loop Guard | in_review |
| THE-94 | Aggressive GC | done |
| THE-95 | OpenClaw Ticket-Erstellung (TEST) | in_review |

---

*Stand: Feedback-Schleife 1 (2. Mai 2026). config_core.py und pipeline_runner.py zeigen noch veraltete Lemonade-Konfiguration — müssen später aktualisiert werden.*
