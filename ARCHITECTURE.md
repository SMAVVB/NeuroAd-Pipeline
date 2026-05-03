# NeuroAd Pipeline Architecture

## System Overview

The NeuroAd Pipeline is a brand intelligence system that performs multi-channel research, content scraping, neural scoring, and AI-audited report generation. It runs entirely on local hardware using the [Ollama](https://ollama.com)-compatible local LLM server (Lemonade proxy on port 9002).

**Two pipeline paths exist:**

| Path | Entry | Purpose |
|------|-------|---------|
| **Pipeline B** (Research) | `brand_orchestrator.py` or `watchdog.py` | Omni-channel brand intelligence — baseline → profile → social/science → mass scraper → STORM report → council audit |
| **Pipeline A** (Scoring) | `pipeline_runner.py` | Neural scoring on existing campaign assets — TRIBE v2, ViNet-S/A, CLIP, HSEmotion, MiroFish |

---

## Pipeline B: Brand Intelligence — 5 Phases

### Phase 0 — Macro Baseline

| Step | File | Description |
|------|------|-------------|
| 0.1 | `agents/agent_baseline.py:9` | SearXNG web context retrieval (company overview, Wikipedia, market data) |
| 0.2 | `agents/agent_baseline.py:25` | Gemma 4 31B draft + DeepSeek R1 70B validation cycle |

**Output:** `Phase_0_Verified_Seed.md` + `Phase_0_Validation.md`

### Brand Profile

| File | Description |
|------|-------------|
| `brand_profile.py` | Extracts brand pillars, competitors, founding year from the verified seed |

**Output:** Structured brand profile JSON passed downstream.

### Phase 2 — Omni-Channel Social & Science

| File | Description |
|------|-------------|
| `agents/agent_publisher.py` | Mass news/science URL discovery (10 columns × 10 queries = 100 queries) |
| `agents/agent_science.py` | Semantic Scholar paper search + citation graph traversal |
| `agents/agent_social.py` | YouTube, Reddit, Twitter/X, TikTok, IG, LinkedIn, reviews, news, HN scraping |

Social and science agents run **in parallel** via `asyncio.gather`.

### Phase 3 — Mass Scraping

| File | Description |
|------|-------------|
| `agents/agent_scraper.py` | Async mass scraping with SQLite URL queue, HTML text extraction, ChromaDB vector indexing |

All URLs from Phases 0–2 are merged into a single queue and scraped concurrently.

### Phase 4 — RAG Report (STORM)

| File | Description |
|------|-------------|
| `agents/agent_storm.py` | RAG-based Wikipedia-style report generation — 8 chapters with sub-chapters |

Gems the verified seed + brand profile as context, then generates a full brand intelligence report using the local Gemma 4 model.

### Phase 5 — Executive Council

| File | Description |
|------|-------------|
| `agents/agent_council.py` | Two-step council review: Gemma 4 fact-check → Kimi Linear 48B audit summary |

### Orchestrator

| File | Description |
|------|-------------|
| `brand_orchestrator.py` | Ties all phases together with memory cleanup between stages |

---

## Pipeline A: Neural Scoring

Runs on campaign assets (images/video) and produces composite brand-consistency grades.

| Module | File | Cost/Asset | Purpose |
|--------|------|------------|---------|
| TRIBE v2 | `model_manager.py` | ~8 min/video | Neural engagement scoring |
| ViNet-S/A | `saliency_scorer.py` | ~22s/video | Visual attention heatmap |
| CLIP | `clip_scorer.py` | ~2s/asset | Brand label consistency (ViT-B/32) |
| HSEmotion | `emotion` module | ~5s/video | Facial emotion detection |
| MiroFish | `mirofish_client.py` | API call | Social sentiment simulation |

All scores are combined via configurable weighted composite (see `DEFAULT_CONFIG["weights"]`).

---

## Watchdog (`watchdog.py`)

The Watchdog monitors campaign log files for tracebacks and creates Multica tickets for each unique error.

### Key Mechanisms

- **Per-location hash tracking**: Errors are hashed using both the error message AND the `file:line` crash location (via `extract_location()`). This prevents false positives where the same generic error (e.g. `TypeError`) occurs in different files.
- **Infinite-loop guard**: After 5 occurrences of the same error at the same location, Watchdog raises a `RuntimeError` instead of spamming tickets. The guard state is persisted in `.watchdog_loop_guard.json`.
- **Duplicate suppression**: If the same error appears again after the first occurrence (but before hitting the threshold), it returns `{"action": "duplicate"}` rather than creating a new ticket.

### How It Runs

Watchdog is invoked as a background process or via cron:

```bash
# Run once (monitor current logs)
python watchdog.py

# Start the full pipeline with watchdog monitoring
python -c "from watchdog import create_multica_ticket; ..."
```

The pipeline logs are written to `campaigns/{brand}_run.log` and Watchdog parses them for `File "..." line N` patterns.

---

## Checkpoint / Resume System

The pipeline uses **interim result caching** rather than a formal checkpoint manager. Each phase writes its output to disk, and downstream phases skip processing if inputs already exist:

| Mechanism | Location | What it does |
|-----------|----------|---------------|
| **Score caching** | `scores_dir/{asset}_score.json` | Pipeline A checks for cached scores before re-running a module |
| **Interim saves** | `scores_dir/pipeline_results_interim.json` | Pipeline A writes after each asset so partial runs survive crashes |
| **Seed reuse** | `Phase_0_Verified_Seed.md` | Storm report re-uses the Phase 0 seed if it exists |
| **Memory cleanup** | `cleanup_phases()` in `brand_orchestrator.py` | `gc.collect()` + `torch.cuda.empty_cache()` between phases |

To resume a pipeline from a specific phase, delete the files from subsequent phases and re-run the orchestrator. The existing phase outputs will be picked up as inputs.

---

## Model Management (`model_manager.py`)

The Beast (AMD Ryzen AI MAX+ 395, 96GB APU) has limited unified memory. `SequentialTribeScorer` ensures only one model is loaded at a time:

1. Loads TRIBE model
2. Scores an asset
3. Calls `aggressive_unload()` — frees GPU cache, runs CPU GC, logs memory state
4. Repeats for next asset

---

## Ollama / Local LLM Configuration

All LLM inference runs locally via the Lemonade proxy server on port 9002:

```python
# config_core.py
LLM_URL = "http://127.0.0.1:9002/v1/chat/completions"  # Lemonade proxy
```

Models are served by Lemonade (a llama.cpp-based proxy) on port 8888:

```bash
# Start the model server
lemonade-server serve \
  --host 0.0.0.0 \
  --port 8888 \
  --extra-models-dir /home/vincent/jarvis_os/models \
  --ctx-size 32768
```

### Models Used

| Role | Model | File |
|------|-------|------|
| Workhorse (draft) | Gemma 4 31B | `extra.gemma-4-31B-it-Q4_K_M.gguf` |
| Judge (validation) | DeepSeek R1 70B | `extra.DeepSeek-R1-Distill-Llama-70B-Q4_K_M.gguf` |
| Fast (summary) | Kimi Linear 48B | `extra.moonshotai_Kimi-Linear-48B-A3B-Instruct-Q5_K_M.gguf` |

---

## Directory Layout

```
neuro_pipeline_project/
├── brand_orchestrator.py      # Pipeline B entry point
├── pipeline_runner.py          # Pipeline A entry point
├── watchdog.py                 # Error monitoring + loop guard
├── config_core.py              # LLM URL, models, SearXNG config
├── model_manager.py            # Sequential VRAM management
├── brand_profile.py            # Pillar/competitor extraction
├── agents/
│   ├── agent_baseline.py       # Phase 0: web context + validation
│   ├── agent_publisher.py      # Phase 1: news/science URL discovery
│   ├── agent_science.py        # Phase 1: Semantic Scholar papers
│   ├── agent_social.py         # Phase 2: omni-channel social scraping
│   ├── agent_scraper.py        # Phase 3: mass scraping + ChromaDB
│   ├── agent_storm.py          # Phase 4: RAG Wikipedia report
│   └── agent_council.py        # Phase 5: executive audit
├── campaigns/                  # Campaign output directory
├── raw_data/                   # Raw scraped data
├── models/                     # Local GGUF model files
├── tools/                      # ViNet, CLIP, etc.
└── reports/                    # Generated reports
```
