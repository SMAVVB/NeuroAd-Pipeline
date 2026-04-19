# NeuroAd Pipeline — MVP Plan

**Stand:** 16. April 2026  
**Hardware:** The Beast (AMD Ryzen AI MAX+ 395, Radeon 8060S iGPU, 96 GB Unified RAM, Ubuntu 24.04)  
**Repo:** github.com/SMAVVB/NeuroAd-Pipeline  
**Scope:** Pipeline A only — bestehende Werbung analysieren, keine Generierung

---

## Aktueller System-Status

| Komponente | Status | Anmerkung |
|---|---|---|
| GPU/ROCm (Radeon 8060S) | ✅ | gfx1151, PyTorch via rocm.nightlies.amd.com |
| Lemonade SDK | ✅ | Port 8888, 131k ctx, manuell via lemonade-128k |
| Lemonade Proxy | ✅ | Port 9002 → 8888, universelles Token Tracking |
| MiroFish + Neo4j | ✅ | Docker, Port 3000/5001, Vulkan Backend |
| TRIBE v2 (GPU/ROCm) | ✅ | Läuft auf gfx1151 PyTorch Nightly |
| CLIP | ✅ | Brand Consistency Scorer aktiv |
| ViNet-S | ✅ | Saliency Scorer aktiv |
| SearXNG | ✅ | Port 8889, Self-hosted |
| Brand Research Agent | ✅ | Komplett, erster erfolgreicher Run (yfood 17k Wörter STORM) |
| Pipeline A | ✅ | Erster erfolgreicher End-to-End Run (apple_vs_samsung) |
| Report Agent | ✅ | Alle 4 Module, JSON + Markdown Output |
| Dashboard v2 | 🔨 | In Entwicklung, startet lokal (Next.js 16, Port 3000) |
| GitHub | ✅ | Push abgeschlossen |

---

## Infrastruktur & Konfiguration

### Lemonade Modelle
- MODEL_WORKHORSE: extra.gemma-4-31B-it-Q4_K_M.gguf (~10-11 TPS)
- MODEL_JUDGE:     extra.DeepSeek-R1-Distill-Llama-70B-Q4_K_M.gguf
- MODEL_FAST:      extra.moonshotai_Kimi-Linear-48B-A3B-Instruct-Q5_K_M.gguf
- Claude Code:     extra.Qwen3-Coder-Next-Q4_K_M.gguf (~45-50 TPS)

### Kritische Konfiguration
- LLM_URL: http://127.0.0.1:9002/v1/chat/completions (via Proxy → 8888)
- SEARXNG_URL: http://127.0.0.1:8889/search
- global_timeout: 1800 in ~/.cache/lemonade/config.json
- PYTORCH_ALLOC_CONF=expandable_segments:True (OOM Prevention)
- BASH_DEFAULT_TIMEOUT_MS: 600000 in ~/.claude/settings.json

### Claude Code settings.json (~/.claude/settings.json)
```json
{
  "model": "extra.Qwen3-Coder-Next-Q4_K_M.gguf",
  "smallModel": "extra.Qwen3-Coder-Next-Q4_K_M.gguf",
  "largeModel": "extra.Qwen3-Coder-Next-Q4_K_M.gguf",
  "apiBaseUrl": "http://localhost:8888/api/v1",
  "env": {
    "BASH_DEFAULT_TIMEOUT_MS": "600000",
    "BASH_MAX_TIMEOUT_MS": "600000"
  }
}
```

### Lemonade starten (nach Reboot)
```bash
lemonade-128k &
# NICHT systemd — systemd-Version hat double free crash Bug
```

---

## Architektur

```
campaigns/<n>/assets/       ← Input: Videos, Bilder
        │
        ▼
Brand Research Agent        ← brand_orchestrator.py
Phase 0: Seed + Brand Profil   Gemma 4 + DeepSeek R1
Phase 1: Suchbaum              SearXNG, concurrent=5
Phase 2: Social + Science      YouTube/Reddit/Twitter/TikTok + CORE API
Phase 3: Mass Scraper          Scrapling
Phase 4: STORM TF-IDF          35k+ Chunks → 17k Wörter Report
Phase 5: Council Audit         Gemma 4 Analyse → Kimi 48B Audit
        │
        ▼
Pipeline A                  ← pipeline_runner.py
├── TRIBE v2                   ROCm GPU, Neural Engagement
├── ViNet-S                    CPU, Visual Attention / Saliency
├── CLIP                       CPU, Brand Consistency
└── MiroFish                   Docker Vulkan, Social Simulation
        │
        ▼
Report Agent                ← report_agent/report_orchestrator.py
4 Interpreter (sequenziell)    Gemma 4 für LLM-Analyse
Output: reports/*.json + .md
        │
        ▼
Dashboard v2                ← React + Vite, Port 3002
7 Seiten mit Sidebar           Recharts, Three.js, D3.js
```

---

## Dashboard v2

### Tech Stack
- Next.js 16 (App Router)
- React 19
- TypeScript
- Tailwind CSS v4
- shadcn/ui components
- Recharts (Charts), D3 v7 (Force Graph), Three.js (3D Brain)

### Port Konfiguration
- Frontend: Port 3000 (Next.js dev server)
- Backend: Port 8080 (FastAPI)

### Starten
```bash
bash ~/neuro_pipeline_project/start_dashboard.sh
```

### Verfügbare Seiten
1. Overview — Creative Performance Table, Modul-Cards
2. Brand Intelligence — Brand Profil, STORM Report, Märkte
3. TRIBE Neural — 3D Brain, 6 Metrik-Balken, AI Analyse
4. MiroFish Social — Animiertes Agent-Netzwerk (D3.js), Sentiment Gauge
5. CLIP Brand — Radar Chart, Label Scores
6. ViNet Attention — Heatmap, Product/Brand/CTA Attention
7. Report & Ranking — Creative Ranking, Executive Summary, Export

---

## Bekannte kritische Fixes & Patches

### TRIBE v2
- get_events_dataframe() muss VOR .to('cuda') aufgerufen werden
- demo_utils.py Zeile 193: device = "cpu" (verhindert Segfault beim Load)
- PyTorch Index: https://rocm.nightlies.amd.com/v2/gfx1151/
- Assets müssen auf 90s via FFmpeg getrimmt werden

### MiroFish
- Vulkan Backend (NICHT ROCm) für Stabilität
- Modell: Qwen2.5-14B-Instruct-Q4_K_M.gguf
- Qwen3.5-9B abandoned — Thinking-Mode bricht JSON
- Alle Timeouts auf 600s: simulation_ipc.py, simulation_runner.py, graph_tools.py, api/simulation.py
- parallel_count=1

### Brand Research Agent
- ChromaDB DEAKTIVIERT (CHROMADB_AVAILABLE = False) — TF-IDF Fallback aktiv
- SearXNG concurrent=5 (höher → OOM)
- Phase 5: Zwei-Schritt (Gemma 4 Analyse → Kimi 48B Audit)
- YouTube: yt-dlp Fallback wenn Channel-Discovery < 5 Videos
- agent_social.py Zeile 168: doppelte } entfernt (Syntax-Bug)

### Report Agent
- asyncio.gather → sequenziell (verhindert Hängen)
- MiroFish Scores: pipeline_results_final.json ist Liste → Transform nötig
- MiroFish Transform: mirofish.llm_scores → social_score berechnen

### Pipeline A
- MiroFish-Scores in pipeline_results_final.json als Liste (nicht Dict)

---

## Multica Setup

### Agents
- NeuroAd-Dev: General Coding (Qwen3-Coder-Next via Lemonade)

### Claude Code 2h Session Limit
Claude Code hat ein hardcodiertes 2h Timeout.
Lösung: Prozesse mit nohup starten, Claude Code überwacht nur.
```bash
nohup python3 brand_orchestrator.py "Brand" > run_$(date +%Y%m%d_%H%M%S).log 2>&1 &
```

---

## Token Tracking

### tools/token_tracker.py
- Primäre Quelle: ~/.lemonade_token_log.jsonl
- Fallback: Lemonade /api/v1/stats
- Alias: tokens (in ~/.bashrc)

### Lemonade Proxy (tools/lemonade_proxy.py)
- Port 9002 → 8888
- Loggt ALLE Requests unabhängig vom Projekt
- Service: ~/tools/lemonade-proxy.service

---

## Dashboard v2 Seitenstruktur

1. Overview — Creative Performance Table (Kernfeature), Modul-Cards
2. Brand Intelligence — Brand Profil, STORM Report Link, Märkte
3. TRIBE Neural — 3D Brain (Three.js), 6 Metrik-Balken, AI Analyse
4. MiroFish Social — Animiertes Agent-Netzwerk (D3.js), Sentiment Gauge
5. CLIP Brand — Radar Chart (Recharts), Label Scores
6. ViNet Attention — Heatmap, Product/Brand/CTA Attention
7. Report & Ranking — Creative Ranking, Executive Summary, Export

Design: Weiß/Schwarz, Inter + JetBrains Mono, Linear.app Aesthetic

---

## Offene Punkte

### Sofort
- [ ] ViNet ROIs definieren für apple_vs_samsung Assets
- [ ] Pipeline A mit yfood Creatives testen
- [ ] Brand Research Nachtrun vollständig

### Kurzfristig
- [ ] Lemonade Proxy testen und aktivieren

### Geplante Module-Upgrades (Post-MVP)
| Aktuell | Ersatz | Grund |
|---|---|---|
| CLIP | SigLIP2 SO400M | Apache 2.0, besser, multilingual |
| ViNet-S | SalFoM | State-of-the-Art Video Saliency |
| - | LibreFace + OpenFace 2.0 | FACS/AU Intensity |
| - | CLAP + Essentia | Audio Emotion |
| - | Emotion-LLaMA | Multimodale Emotion (NeurIPS 2024) |
| - | Qwen2.5-VL-7B | Ad Understanding |
| - | IC9600 | Cognitive Load |
| - | Detoxify + Marqo-NSFW | Brand Safety |

### Langfristig
- [ ] Supabase Migration (aktuell SQLite)
- [ ] KPI Kalibrierung (CTR/ROAS/CPA Regression)
- [ ] TurboQuant (Google ICLR 2026)
