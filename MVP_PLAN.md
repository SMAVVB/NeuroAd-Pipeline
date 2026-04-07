# NeuroAd Pipeline — MVP Plan

**Stand:** 7. April 2026  
**Hardware:** The Beast (AMD Strix Halo, Ryzen AI MAX+ 395, 96 GB Unified Memory, Radeon 8060S gfx1151, Ubuntu 24.04)  
**Scope:** Pipeline A — bestehende Werbung analysieren, keine Generierung  
**Repo:** github.com/SMAVVB/NeuroAd-Pipeline  
**Venv:** `venv_rocm` (Python 3.12, PyTorch 2.11+rocm7.11) — auto-aktiviert via `.bashrc`

---

## Aktueller Infrastruktur-Status (7. April 2026)

| Komponente | Status | Anmerkung |
|---|---|---|
| GPU/ROCm (Radeon 8060S, gfx1151) | ✅ | PyTorch 2.11.0+rocm7.11, CUDA=True |
| TRIBE v2 (GPU) | ✅ | Läuft mit venv_rocm, Transformer auf GPU |
| TRIBE v2 (V-JEPA2 Video-Encoder) | ✅ | Sequential loading via ModelManager, num_frames=16 |
| CLIP | ✅ | Import OK, läuft auf GPU |
| HSEmotion | ✅ | Import OK |
| ViNet-S | ✅ | Integriert in saliency_scorer.py |
| MiroFish + Neo4j 5.18 | ✅ | **VOLLSTÄNDIG INTEGRIERT** — localhost:3000/5001/7474 |
| MiroFish API Wrapper | ✅ | mirofish_client.py fertig, End-to-End getestet |
| Lemonade SDK | ✅ | Port 8888, Vulkan-Backend für MiroFish |
| pipeline_runner.py | ✅ | Alle 5 Module orchestriert |
| Flux.1 (diffusers) | ✅ | Import OK (Pipeline B, noch nicht genutzt) |
| DeepGaze IIE | ❌ | Bitbucket URLs tot, für MVP übersprungen |

### MiroFish Konfiguration (stabil, 7. April 2026)

**LLM:** `extra.Qwen2.5-14B-Instruct-Q4_K_M.gguf` (Vulkan, 32k ctx)  
**Lemonade starten:** `lemonade-mirofish` (Alias in ~/.bashrc)

```bash
alias lemonade-mirofish="lemonade-server serve --host 0.0.0.0 --port 8888 \
  --extra-models-dir /home/vincent/jarvis_os/models \
  --ctx-size 32768 --llamacpp vulkan"
```

**WICHTIG:** Qwen3.5 NICHT für MiroFish verwenden — Thinking-Mode produziert invalides JSON.  
**WICHTIG:** ROCm-Backend für MiroFish meidet → lädt in Shared Memory statt GPU (kein Problem, aber langsamer).

### MiroFish Docker-Patches (permanent in Source-Files, rebuild nötig nach git pull)

Alle Patches liegen in `/home/vincent/jarvis_os/MiroFish-Offline/backend/app/`:

| Datei | Patch |
|---|---|
| `utils/llm_client.py` | trailing comma JSON fix, `content=None` fallback, `enable_thinking:False`, JSON-Extraktion |
| `services/simulation_ipc.py` | `send_command` timeout 60→600s, `send_batch_interview` timeout 120→600s |
| `services/simulation_runner.py` | Interview-Timeouts 60/120/180→600s |
| `services/graph_tools.py` | timeout 180→600s |
| `api/simulation.py` | timeout defaults 60/120/180→600s |
| `services/report_agent.py` | None-Check nach `interview_agents` |
| `services/oasis_profile_generator.py` | `parallel_count` 5→1 (Lemonade single-threaded) |

**Rebuild nach Änderungen:**
```bash
cd /home/vincent/jarvis_os/MiroFish-Offline
docker compose down && docker compose build --no-cache && docker compose up -d
```

### TRIBE v2 Patches (in apply_patches.sh, nach pip install ausführen)

- `neuralset/extractors/video.py` — V-JEPA2 device handling
- `neuralset/extractors/audio.py` — Wav2Vec/Bert device
- `neuralset/extractors/text.py` — LLaMA device
- `tribev2/eventstransforms.py` — WhisperX int8 + cpu
- `demo_utils.py` — Zeile 193: `device = "cpu"` (verhindert Segfault beim Checkpoint-Laden)
- `dataloader.py` — sequentielles unload nach prepare()

### Lemonade ROCm Binary (gfx1151-spezifisch)

- Pfad: `/home/vincent/.cache/lemonade/bin/llamacpp/rocm/llama-server`
- Build: b1231, ROCm 7, gfx1151
- Für TRIBE/andere Tasks: `lemonade-rocm` Alias (ROCm-Backend)
- Für MiroFish: `lemonade-mirofish` Alias (Vulkan-Backend, stabiler)

---

## Pipeline A — Aktuelle Architektur

```
campaigns/<name>/assets/     ← Input: Videos, Bilder
        │
        ▼
[Brand Context]              ← brand_context.txt pro Kampagne (manuell, Agent geplant)
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│              SCORING LAYER (pipeline_runner.py)          │
│                                                          │
│  [1] TRIBE v2        → neural_engagement, emotional_     │
│                         impact, ROI-Scores (fMRI)        │
│                                                          │
│  [2] ViNet-S         → visual_attention, center_bias,    │
│                         saliency maps                    │
│                                                          │
│  [3] CLIP            → brand_consistency                 │
│                                                          │
│  [4] HSEmotion       → facial_emotion, valence           │
│                                                          │
│  [5] MiroFish        → social_sentiment, virality,       │
│                         controversy_risk + Report        │
└─────────────────────────────────────────────────────────┘
        │
        ▼
Composite Score (gewichtet) → pipeline_a_results.json
```

### Scoring-Gewichtung (aktuell)

```python
WEIGHTS = {
    'neural_engagement':  0.25,   # TRIBE v2
    'emotional_impact':   0.15,   # TRIBE v2 TPJ
    'visual_attention':   0.20,   # ViNet-S
    'brand_consistency':  0.15,   # CLIP
    'social_sentiment':   0.10,   # MiroFish
    'facial_emotion':     0.10,   # HSEmotion
    'audio_engagement':   0.05,   # TRIBE v2 Broca
}
```

### Ordnerstruktur pro Kampagne

```
campaigns/apple_vs_samsung/
├── assets/              ← Videos/Bilder
├── brand_context.txt    ← Brand-Kontext für MiroFish (manuell erstellt)
├── scores/              ← JSON Outputs aller Scorer + .npy Brain-Maps
├── mirofish/            ← MiroFish Simulation Reports
└── report/              ← pipeline_a_results.json (Finale Ausgabe)
```

---

## Was noch fehlt für MVP-Abschluss

### Priorität 1 — Brand Research Agent

**Was:** Automatischer Agent der Marken-Kontext sammelt und in alle Pipeline-Schritte einspeist.

**Warum kritisch:** Aktuell ist `brand_context.txt` manuell erstellt. Für MiroFish besonders wichtig — bessere Personas, relevantere Simulation. Für CLIP: brand-spezifische Labels statt generische. Für den Final Report: wissenschaftlich fundierte Kontextualisierung.

**Stack:** Lemonade SDK + Crawl4AI/Firecrawl
- Crawlt Website, Meta Ad Library, Social Media
- Extrahiert: Brand DNA, Visual Style, Tone of Voice, Key Messages, Competitor-Liste
- Output: strukturierte `brand_context.json` die alle Module parametriert

**Integration:**
- MiroFish: bessere Personas (nicht mehr "TikTok als Agent")
- CLIP: markenspezifische Labels
- Final Report: fundierter Kontext

### Priorität 2 — Module-Upgrades (laut Open-Source Research Dokument)

Einfache Drop-In-Replacements mit besserem Output — kein großer Aufwand:

| Aktuell | Upgrade | Aufwand | Gewinn |
|---|---|---|---|
| CLIP ViT-B/32 | **SigLIP2 SO400M** | Sehr gering | Bessere multilingual/beschreibende Labels |
| ViNet-S | **SalFoM** (oder UNISAL) | Gering | Höhere Saliency-Genauigkeit |
| HSEmotion (nur Emotion) | + **LibreFace** (AU-Intensität) | Gering | Quantitative AU-Scores (0-5) statt nur Labels |
| — | **CLAP** (Audio-Emotion) | Gering | Zero-Shot Audio-Tagging für Soundtracks |

**Reihenfolge:** SigLIP2 zuerst (einfachster Swap), dann LibreFace.

### Priorität 3 — MiroFish Personas optimieren

**Problem:** Aktuell kommen manchmal Plattformen (TikTok, YouTube) als Agenten statt echter Personas. Brand-Kontext hilft, aber System-Prompts in MiroFish sollten auch angepasst werden.

**Fix:** Ontology-Generator Prompt anpassen — klare Anweisung dass Agenten echte Personen/Rollen sein müssen, keine Plattformen.

### Priorität 4 — Final Report Agent

**Was:** Reasoning-Modell (DeepSeek R1, liegt bereits in `/home/vincent/jarvis_os/models/`) das alle Scores konsolidiert und einen wissenschaftlich fundierten Gesamtreport schreibt.

**Input:** Alle Scorer-Outputs + Brand-Kontext + MiroFish Report  
**Output:** Strukturierter Report mit: Ranking-Begründung, Stärken/Schwächen je Creative, konkrete Optimierungsempfehlungen

**Hinweis:** TurboQuant (Google, ICLR 2026) — 3-Bit KV-Cache Kompression für LLMs — ermöglicht bis zu 100k-200k Token Kontext bei deutlich weniger RAM. Sobald llama.cpp Integration stabil ist, einbauen für den Research Agent und Final Report Agent. Aktuell noch in PR-Phase.

### Priorität 5 — `failed_assets` Bug fixen

Kleiner Bug in `pipeline_runner.py`: Assets werden als "failed" markiert wenn irgendein Modul einen Fehler hatte, auch wenn die anderen Module erfolgreich waren und ein Score existiert. Fix: nur als failed markieren wenn kein Composite Score berechnet werden konnte.

### Priorität 6 — Datenbank + Dashboard

**Datenbank:** SQLite für Score-Persistenz (bereits vorhanden: `dashboard/neuro_ad.db`)  
**Dashboard:** React + FastAPI (`dashboard_v2/`) — Design Brief bereits erstellt für v0.dev/Lovable/Bolt

**Dashboard-Features:**
- Creative Ranking Tabelle
- 3D Brain Viewer (Three.js) für TRIBE-Seite
- D3 Force-Directed Agent Network für MiroFish-Seite
- Saliency Overlay auf Original-Frame
- AI-generierter Streaming Report (DeepSeek R1)
- Drei Focus-Modi (Executive, Technical, Creative)
- Tailscale Remote Access

**Design:** Radikaler Minimalismus — schwarz/weiß/off-white, Linear.app / Vercel-Ästhetik, Geist/Inter + JetBrains Mono für Score-Werte.

---

## Laufzeit-Referenz (Pipeline A, apple_vs_samsung)

| Schritt | Dauer |
|---|---|
| TRIBE v2 (Video, ~90s) | ~8-15 Min/Asset |
| ViNet-S Saliency | ~30s/Asset |
| CLIP | ~5s/Asset |
| HSEmotion | ~30s/Asset |
| MiroFish komplett (inkl. Report) | ~60-90 Min/Asset |
| **Gesamt für 2 Assets** | **~3-4 Stunden** |

MiroFish dominiert die Laufzeit. Optimierungspotential: weniger Simulation-Rounds, kleineres LLM (7B statt 14B wenn JSON-Qualität ausreicht).

---

## Offene Technische Schulden

- [ ] `brand_context` in `pipeline_runner.py` noch hardcoded — muss aus `brand_context.txt` oder Brand Agent kommen
- [ ] `failed_assets` Bug im Report — zeigt Assets als failed obwohl Score existiert
- [ ] MiroFish Persona-Qualität — Plattformen erscheinen manchmal als Agenten
- [ ] TRIBE v2 Flash Attention noch nicht aktiviert (`TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1`)
- [ ] neuralset Patches gehen bei `pip install` verloren — `apply_patches.sh` manuell ausführen
- [ ] MiroFish: `lemonade-mirofish` muss vor jedem Run manuell gestartet werden

---

## Priorisierungs-Matrix (verbleibende Arbeit)

| Feature | Schwierigkeit | Impact | Empfehlung |
|---|---|---|---|
| `failed_assets` Bug | Sehr gering | Mittel | Sofort |
| SigLIP2 statt CLIP | Sehr gering | Mittel | Nächste Session |
| Brand Context aus Datei lesen | Sehr gering | Hoch | Nächste Session |
| LibreFace AU-Intensität | Gering | Mittel | Bald |
| MiroFish Persona-Prompts | Gering | Hoch | Bald |
| Flash Attention aktivieren | Sehr gering | Hoch (Speed) | Bald |
| Brand Research Agent | Mittel | Sehr hoch | MVP-Phase |
| Final Report Agent (DeepSeek R1) | Mittel | Sehr hoch | MVP-Phase |
| Dashboard (React + FastAPI) | Mittel | Hoch | MVP-Phase |
| SalFoM statt ViNet-S | Gering | Mittel | Optional |
| CLAP Audio-Emotion | Gering | Mittel | Optional |
| TurboQuant KV-Cache | Niedrig (warten auf PR) | Hoch | Post-MVP |
| Pipeline B (Generation) | Hoch | Hoch | Post-MVP |
| KPI-Kalibrierung (XGBoost) | Mittel | Sehr hoch | Post-MVP |
