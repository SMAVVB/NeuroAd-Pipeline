# NeuroAd Pipeline

A Python brand intelligence pipeline that performs omni-channel research, neural scoring, and AI-audited report generation — running entirely on local hardware via Ollama-compatible models.

## Overview

The pipeline has two independent paths:

### Pipeline B — Brand Intelligence (Research)

```
SearXNG Web Context → Gemma 4 Baseline → DeepSeek R1 Validation
    → Brand Profile → Social/Science Scraping → Mass Scraper
    → STORM Report (RAG) → Council Audit
```

**Entry:** `brand_orchestrator.py` or `watchdog.py`

### Pipeline A — Neural Scoring

```
TRIBE v2 + ViNet-S/A + CLIP + HSEmotion → Composite Brand Grade
```

**Entry:** `pipeline_runner.py`

## Prerequisites

- Ubuntu 24.04 with AMD ROCm drivers
- Python 3.12+
- [Lemonade](https://github.com/ollama/ollama) server (port 8888 + proxy on 9002)
- SearXNG instance (port 8889)
- PyTorch with ROCm support
- ChromaDB, yt-dlp, curl_cffi, sentence-transformers

## Local LLM Setup (Ollama)

All LLM inference runs locally — no OpenAI, Anthropic, or other cloud API keys required.

### 1. Start the model server

```bash
lemonade-server serve \
  --host 0.0.0.0 \
  --port 8888 \
  --extra-models-dir /home/vincent/jarvis_os/models \
  --ctx-size 32768
```

Models are loaded from `extra_models_dir` via GGUF format. The server exposes an OpenAI-compatible API at `http://127.0.0.1:8888`.

### 2. Configure the proxy

In `config_core.py`, the proxy listens on port 9002:

```python
LLM_URL = "http://127.0.0.1:9002/v1/chat/completions"
```

### 3. Verify the server

```bash
curl http://127.0.0.1:8888/models | python -m json.tool
```

### Models

| Role | Model | GGUF File |
|------|------|-----------|
| Workhorse | Gemma 4 31B | `extra.gemma-4-31B-it-Q4_K_M.gguf` |
| Judge | DeepSeek R1 70B | `extra.DeepSeek-R1-Distill-Llama-70B-Q4_K_M.gguf` |
| Fast | Kimi Linear 48B | `extra.moonshotai_Kimi-Linear-48B-A3B-Instruct-Q5_K_M.gguf` |

Configured in `config_core.py`:

```python
MODEL_WORKHORSE = "extra.gemma-4-31B-it-Q4_K_M.gguf"
MODEL_JUDGE     = "extra.DeepSeek-R1-Distill-Llama-70B-Q4_K_M.gguf"
MODEL_FAST      = "extra.moonshotai_Kimi-Linear-48B-A3B-Instruct-Q5_K_M.gguf"
```

## Running the Pipeline

### Direct invocation (Pipeline B — Research)

```bash
python brand_orchestrator.py "Apple"
```

Or with a custom brand:

```bash
python brand_orchestrator.py "Nike"
```

Results are saved to `raw_data/{brand}_YYYYMMDD_HHMMSS/`.

### Watchdog mode (self-healing)

```bash
python watchdog.py
```

Watchdog monitors campaign logs (`campaigns/{brand}_run.log`) for errors and creates Multica tickets for unique tracebacks. It includes an infinite-loop guard that stops ticket spam after 5 occurrences of the same error at the same location.

### Direct invocation (Pipeline A — Scoring)

```bash
# Run on a campaign
python pipeline_runner.py campaigns/nike_2026/

# Skip slow modules
python pipeline_runner.py campaigns/nike_2026/ --skip tribe emotion

# Run only CLIP scoring
python pipeline_runner.py campaigns/nike_2026/ --only clip

# With custom brand labels
python pipeline_runner.py campaigns/nike_2026/ --brand-labels "sporty" "premium"
```

### Quick setup

```bash
bash setup.sh
```

## Output

Pipeline B produces:
- `Phase_0_Verified_Seed.md` — validated brand baseline
- `Phase_4_STORM_Report.md` — 8-chapter Wikipedia-style intelligence report
- `Phase_5_Council_Audit.md` — executive audit summary
- `raw_data/` — all scraped URLs, text, and structured data

Pipeline A produces:
- `reports/pipeline_a_results.json` — ranked asset scores with grades (A-D)
- `scores/` — per-asset JSON scores for each module

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for full details on:
- The 5 phases of Pipeline B
- Pipeline A scoring modules
- Watchdog infinite-loop guard mechanism
- Checkpoint / resume system
- VRAM management via SequentialTribeScorer

## License

MIT
