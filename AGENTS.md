# NeuroAd Pipeline — Agent Context

## Projekt-Pfad
/home/vincent/neuro_pipeline_project/

## Python-Umgebung
IMMER venv_rocm verwenden — niemals venv oder system python.
Aktivieren vor jedem Python-Befehl:
source /home/vincent/neuro_pipeline_project/venv_rocm/bin/activate

Oder direkt:
/home/vincent/neuro_pipeline_project/venv_rocm/bin/python script.py

## Stack
- Python 3.12, Ubuntu 24.04, AMD ROCm (gfx1151)
- LLM: Ollama auf localhost:11434 — alles läuft über qwen3.6-64k
- SearxNG: localhost:8889
- MiroFish: Docker, localhost:5001 (Vulkan Backend)
- Dashboard V2: Next.js, Port 3002
- FastAPI Backend: Port 8080

## Zwei Pipelines

### Pipeline A (Scoring) — Entry: pipeline_runner.py
TRIBE v2 → ViNet-S → CLIP → HSEmotion → MiroFish → Composite Score
- TRIBE: ~8min/Video, nur sequenziell (VRAM), OOM-Schutz aktiv
- MiroFish: max 360 Retries, Fallback 0.5 bei Fehler
- Cache: scores_dir/{asset}_score.json

### Pipeline B (Research) — Entry: brand_orchestrator.py
Phase 0 (Web/Baseline) → Brand Profile → Social/Science → Mass Scraper → STORM Report → Council Audit
- Alles über Qwen 3.6, kein DeepSeek/Gemma/Kimi mehr aktiv
- Aggressive GC zwischen Phasen (gc.collect + torch.cuda.empty_cache)
- ChromaDB deaktiviert, TF-IDF Fallback aktiv

## Watchdog (watchdog.py)
- Location-aware MD5 Hashing (file + line)
- Max 5 Retries, dann RuntimeError
- Loop Guard: .watchdog_loop_guard.json
- Multica API für Tickets

## Kritische Bugs / Fixes die bekannt sind
- config_core.py zeigt noch Lemonade/Port 9002 — veraltet, ignorieren
- pipeline_runner.py LLM Reset bezieht sich auf Lemonade — veraltet
- TRIBE: get_events_dataframe() VOR .to('cuda') aufrufen
- MiroFish: parallel_count=1, Thinking-Mode bricht JSON

## Pipeline starten (Production)
```bash
nohup python3 brand_orchestrator.py "Brand" > run_$(date +%Y%m%d_%H%M%S).log 2>&1 &
python watchdog.py  # in separatem Terminal
```

## Was noch offen ist
- config_core.py auf Ollama updaten
- pipeline_runner.py LLM Reset fixen
- Post-MVP: CLIP → SigLIP2, ViNet-S → SalFoM

## KRITISCH: Python-Aufruf
NIEMALS `python` oder `python3` direkt aufrufen.
IMMER vollständigen Pfad nutzen:
/home/vincent/neuro_pipeline_project/venv_rocm/bin/python script.py

Oder venv aktivieren:
source /home/vincent/neuro_pipeline_project/venv_rocm/bin/activate && python script.py

## Pipeline A starten via Hermes
WICHTIG: Pipeline A nutzt GPU (TRIBE, ROCm). Während Pipeline läuft KEIN Ollama nutzen.
Hermes muss /background nutzen und dann warten — kein paralleles LLM-Calling.

Workflow:
1. /background in Discord
2. source venv_rocm/bin/activate && bash hermes_pipeline_run.sh
3. Warten bis fertig
4. Log auswerten auf Errors/Scores/Grades
5. Fehler analysieren, Fix vorschlagen — NICHT automatisch ohne Bestätigung

Nike Campaign: campaigns/nike_summer_26
Assets: assets/nike_clip_A.mp4, assets/nike_clip_B.mp4

Bei Fehler: Traceback aus Log, Ursache erklären, Fix vorschlagen.
