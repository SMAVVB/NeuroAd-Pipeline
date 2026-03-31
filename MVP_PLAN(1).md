# NeuroAd Pipeline — MVP Plan

**Stand:** 31. März 2026  
**Hardware:** The Beast (AMD Strix Halo, Ryzen AI MAX+ 395, 96 GB Unified Memory, Ubuntu 24.04)  
**Scope:** Pipeline A only — bestehende Werbung analysieren, keine Generierung

---

## Aktueller Infrastruktur-Status

| Komponente | Status | Anmerkung |
|---|---|---|
| GPU/ROCm (Radeon 8060S, gfx1151) | ✅ | PyTorch 2.11.0+rocm7.11 |
| MiroFish + Neo4j 5.18 | ✅ | localhost:3000 / :5001 / :7474 |
| HSEmotion | ✅ | Import OK |
| CLIP | ✅ | Import OK, läuft auf GPU |
| Flux.1 (diffusers) | ✅ | Import OK |
| Lemonade SDK | ✅ | Port 8888, 131k ctx — manuell starten |
| TRIBE v2 (GPU, sequentiell) | ✅ | Stabil via ModelManager + dataloader Patch |
| Brain-Visualisierung (Nilearn) | ✅ | 4-Panel + Temporal Profile funktioniert |
| DeepGaze IIE | ❌ | Bitbucket URLs tot, skippen für MVP |
| ViNet-S | ⚠️ | Repo vorhanden, noch nicht als Scorer integriert |

---

## Was heute erreicht wurde

**TRIBE v2 End-to-End stabil** — das war der kritische Blocker.

Gelöst durch drei aufeinander aufbauende Maßnahmen:

1. **ModelManager** (`model_manager.py`) — sequentielles Loading der Extraktoren mit explizitem Unload + `gc.collect()` + `cuda.empty_cache()` nach jeder Phase
2. **dataloader.py Patch** — `prepare_extractors()` entlädt jeden Extraktor direkt nach `prepare()`, sodass nie mehr als ein großes Modell gleichzeitig im RAM liegt
3. **V-JEPA2 Config-Patch** — `num_frames 64→16` und `max_imsize→256` reduzieren GPU-Aktivierungen ~4x und verhindern OOM bei der Video-Encoding-Phase

**Erstes echtes Ergebnis** auf `sintel_trailer.mp4` (52s):
```json
{
  "neural_engagement": 0.204,
  "emotional_impact":  0.183,
  "face_response":     0.222,
  "scene_response":    0.198,
  "motion_response":   0.199,
  "language_engagement": 0.194,
  "temporal_peak": 52,
  "n_segments": 53,
  "brain_map_path": "campaigns/test_campaign/scores/sintel_trailer_tribe_preds.npy"
}
```

Brain-Heatmap (4-Panel LH/RH lateral/medial) und Temporal Activation Profile wurden erfolgreich gerendert.

---

## ⚠️ Bekannte Limitierung: Video-Inferenz-Geschwindigkeit

**Aktuell:** ~8 Minuten für ein 52-Sekunden-Video (V-JEPA2 Encoding: ~4.6s/Frame × 104 Frames)

Das ist für einzelne Analysen akzeptabel, aber nicht für Batch-Verarbeitung vieler Creatives.

**Ursache:** V-JEPA2-vitg ist das größte V-JEPA2 Modell (Giant). `num_frames=16` (reduziert von 64) hilft beim Speicher, ändert aber die Frame-Rate nicht.

**Optimierungsoptionen für spätere Skalierung (nicht MVP-blocking):**
- `TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1` — Flash Attention auf AMD aktivieren, potenziell 2-3x schneller
- `frequency 2.0 Hz → 1.0 Hz` — 52 statt 104 Clips, 2x schneller, leichter Qualitätsverlust
- `clip_duration 4.0s → 2.0s` — kleinere Clips, weniger Speicher pro Forward Pass
- Caching-Layer — Features werden von neuralset/exca gecacht, zweiter Run ist schnell
- Für Produktion: Batch-Queue mit Overnight-Processing

**Aktueller Richtwert:** ~10 Min/Video auf The Beast. Für MVP mit 5-10 Videos pro Kampagne = ~1 Stunde TRIBE-Scoring, was im akzeptablen Rahmen liegt.

---

## Patches & Infrastruktur

### Aktive neuralset Patches (in venv_rocm)
Werden durch `apply_patches.sh` reproduzierbar angewandt:
- `neuralset/extractors/video.py` — V-JEPA2 device handling, `resamp_first_dim` fix
- `neuralset/extractors/audio.py` — Wav2VecBert/Whisper device auf cuda-or-cpu
- `neuralset/extractors/text.py` — HuggingFaceText device auf cuda-or-cpu
- `neuralset/dataloader.py` — `prepare_extractors()` entlädt nach jeder Phase ← **neu, kritisch**

### Neue Files im Projekt
```
model_manager.py      ✅ SequentialTribeScorer — stabiles sequentielles Loading
apply_patches.sh      ✅ Reproduzierbare neuralset Patches
test_sequential.py    ✅ Smoke-Test für ModelManager
visualize_brain.py    ✅ 4-Panel Brain Map + Temporal Profile
```

### Venv & Startbefehle
```bash
cd ~/neuro_pipeline_project
source venv_rocm/bin/activate

# TRIBE v2 Score eines Videos
python model_manager.py campaigns/test_campaign/assets/sintel_trailer.mp4 --device cuda

# Brain-Visualisierung
python visualize_brain.py campaigns/test_campaign/scores/sintel_trailer_tribe_preds.npy --temporal
```

---

## MVP Pipeline-Architektur

```
campaigns/marke/assets/          ← Input: Videos, Bilder
        │
        ▼
Brand Research                   ← Lemonade SDK (noch offen)
        │
        ▼
┌─────────────────────────────────────────┐
│         SCORING LAYER (sequentiell)     │
│                                         │
│  TRIBE v2 ✅ → Saliency ⚠️ → CLIP ✅ → MiroFish ✅  │
└─────────────────────────────────────────┘
        │
        ▼
Composite Scorer ✅               ← Gewichteter Gesamt-Score
        │
        ▼
Dashboard (Streamlit/Tailscale)  ← nächste Priorität
  ├── Brain Heatmap (Nilearn) ✅
  ├── Saliency Map Overlay ⚠️
  ├── MiroFish Sentiment Report
  └── Creative Ranking Tabelle
```

---

## Ordnerstruktur pro Kampagne

```
~/neuro_pipeline_project/campaigns/
└── nike_2026/
    ├── assets/          ← Videos/Bilder rein (manuell oder per URL)
    ├── scores/          ← TRIBE JSON + .npy Predictions + Brain Map PNGs
    ├── mirofish/        ← Simulation Reports
    └── report/          ← Finaler Output (PDF/HTML)
```

---

## Prioritäten — Nächste Sessions

### Priorität 1 — ViNet-S Integration (Saliency Scorer)
Das letzte fehlende Scoring-Modul für Pipeline A.

```bash
ls ~/neuro_pipeline_project/tools/ViNet/
# generate_result.py direkt aufrufen mit Test-Video
```

Ziel: `saliency_scorer.py` der ein Video/Bild nimmt und zurückgibt:
- Saliency Map als PNG (Heatmap über Original-Frame)
- `product_attention`, `brand_attention`, `cta_attention` Scores (via Bounding Box ROI)

### Priorität 2 — Pipeline End-to-End
`pipeline_runner.py` der einen Kampagnen-Ordner nimmt und alle Scorer durchläuft:

```python
def run_pipeline_a(campaign_dir: str):
    assets = collect_assets(campaign_dir)
    for asset in assets:
        scores['tribe']    = model_manager.SequentialTribeScorer().score_asset(asset)
        scores['saliency'] = saliency_scorer.score(asset)
        scores['clip']     = clip_scorer.score(asset)
    scores['mirofish'] = mirofish_runner.simulate(assets[:5], brand_context)
    composite = composite_scorer.combine(scores)
    generate_report(campaign_dir, composite)
```

### Priorität 3 — MiroFish programmatisch einbinden
MiroFish läuft bereits (localhost:3000/5001). REST API Wrapper bauen:
- Simulation starten mit Brand-Context + Creative Description
- Status pollen bis fertig
- Report auslesen und in Composite Score einfließen lassen

Bekannte API Endpoints:
```
POST /api/graph/ontology/generate
POST /api/graph/build
POST /api/simulation/create
POST /api/simulation/prepare
GET  /api/simulation/<id>
POST /api/report/generate
GET  /api/report/by-simulation/<id>
```

### Priorität 4 — Streamlit Dashboard
Erreichbar per Tailscale, zeigt pro Kampagne:
- Creative Ranking Tabelle (alle Assets, sortiert nach Composite Score)
- Brain Heatmap (Nilearn PNG, später interaktiv via Plotly)
- Temporal Activation Profile
- Saliency Overlay auf Original-Frame
- MiroFish Sentiment Timeline

---

## Scoring-Gewichtung (MVP Default)

```python
WEIGHTS = {
    'neural_engagement':  0.30,  # TRIBE v2 Gesamt-Aktivierung
    'emotional_impact':   0.20,  # TRIBE v2 TPJ
    'visual_attention':   0.20,  # Saliency auf Produkt/CTA  ← Placeholder bis ViNet-S da
    'brand_consistency':  0.15,  # CLIP Score
    'social_sentiment':   0.15,  # MiroFish positiver Sentiment ← Placeholder bis MiroFish API
}
```

---

## Offene Fragen / Entscheidungen

- [ ] ViNet-S Bounding Box Input — wie definieren wir Produkt/Logo/CTA Bereiche pro Asset?
- [ ] Lemonade als Research-Agent konfigurieren (welches Modell, welcher Prompt)
- [ ] MiroFish Persona-Templates definieren (Zielgruppe pro Kampagne)
- [ ] Dashboard-Hosting: Streamlit lokal + Tailscale oder nginx Reverse Proxy?
- [ ] TRIBE v2 Speed-Optimierung: Flash Attention testen wenn Skalierung nötig wird
- [ ] ROI Vertex Ranges kalibrieren — aktuell heuristische Schätzungen, Atlas-basierte Ranges wären präziser
