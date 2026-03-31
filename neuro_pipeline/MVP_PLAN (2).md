# NeuroAd Pipeline — MVP Plan

**Stand:** 31. März 2026  
**Hardware:** The Beast (AMD Strix Halo, Ryzen AI MAX+ 395, 96 GB Unified Memory, Ubuntu 24.04)  
**Venv:** `~/neuro_pipeline_project/venv_rocm` (Python 3.12, PyTorch 2.11+rocm7.11)  
**Scope:** Pipeline A — bestehende Werbung analysieren, keine Generierung

---

## Status: Was läuft

| Komponente | Status | Anmerkung |
|---|---|---|
| GPU/ROCm (Radeon 8060S, gfx1151) | ✅ | Performance Mode via `rocm-smi --setperflevel high` |
| TRIBE v2 (GPU, sequentiell) | ✅ | ~8 Min/Video, ModelManager + dataloader Patch |
| ViNet-S Saliency | ✅ | 36 MB, ~7s/Video, DHF1K Weights |
| CLIP Brand Consistency | ✅ | ViT-B/32, GPU |
| HSEmotion Facial Emotion | ✅ | weights_only Patch angewandt |
| Brain-Visualisierung (Nilearn) | ✅ | 4-Panel LH/RH + Temporal Profile |
| Pipeline A Runner | ✅ | Alle Module, Caching, MiroFish-ready |
| MiroFish + Neo4j 5.18 | ✅ | localhost:3000/5001/7474 — manuell, API pending |
| Lemonade SDK | ✅ | Port 8888, 131k ctx — manuell starten |
| DeepGaze IIE | ❌ | Bitbucket URLs tot — skippen |

---

## Projektdateien

```
~/neuro_pipeline_project/
├── model_manager.py        ← TRIBE v2 sequentielles Loading
├── saliency_scorer.py      ← ViNet-S Wrapper
├── pipeline_runner.py      ← Pipeline A Orchestrator
├── visualize_brain.py      ← Brain Map + Temporal Profile
├── apply_patches.sh        ← Reproduzierbare neuralset Patches
├── test_sequential.py      ← Smoke-Test ModelManager
└── tools/
    ├── tribev2/            ← TRIBE v2 Source (editable install)
    └── ViNet_v2/           ← ViNet++ Source + final_models/
```

---

## Patches (nach pip install erneuern: `bash apply_patches.sh`)

| Datei | Was gepatcht wird |
|---|---|
| `neuralset/extractors/video.py` | V-JEPA2 device + resamp_first_dim bug |
| `neuralset/extractors/audio.py` | Wav2VecBert/Whisper device |
| `neuralset/extractors/text.py` | HuggingFaceText device |
| `neuralset/dataloader.py` | Extraktoren nach prepare() entladen ← kritisch |
| `tools/tribev2/tribev2/demo_utils.py` | max_unmatched_ratio 0.05→0.50 |
| `venv_rocm/.../hsemotion/facial_emotions.py` | weights_only=False |

---

## Scoring-Module im MVP

### TRIBE v2 — Neurale Response
- **Output:** ROI-Scores (TPJ, FFA, PPA, V5, Broca, A1) + neural_engagement
- **Laufzeit:** ~8 Min/Video (gecacht ab zweitem Run)
- **Brain Maps:** `.npy` Predictions + 4-Panel PNG via visualize_brain.py

### ViNet-S — Visuelle Aufmerksamkeit
- **Output:** Saliency Heatmap PNG + center_bias + ROI-Scores (wenn Bounding Boxes)
- **Laufzeit:** ~7s/Video
- **Checkpoint:** `tools/ViNet_v2/final_models/ViNet_S/.../vinet_s_dhf1k.pt`

### CLIP — Brand Consistency
- **Output:** brand_match_score (0-1) + top_label
- **Laufzeit:** ~2s/Asset
- **Hinweis:** Beschreibende Labels verwenden, keine Brand-Namen

### HSEmotion — Facial Emotion
- **Output:** dominant_emotion, emotional_valence (-1 bis 1), face_coverage
- **Laufzeit:** ~5s/Video
- **Hinweis:** Nur relevant für Ads mit echten Gesichtern

### MiroFish — Social Simulation
- **Status:** Manuell via localhost:3000, API Wrapper steht aus
- **Fallback:** Placeholder 0.5 bis API fertig

---

## Composite Score Gewichtung

```python
WEIGHTS = {
    'neural_engagement':  0.25,   # TRIBE v2 Gesamt
    'emotional_impact':   0.15,   # TRIBE v2 TPJ
    'visual_attention':   0.20,   # ViNet-S
    'brand_consistency':  0.15,   # CLIP
    'social_sentiment':   0.10,   # MiroFish (Placeholder)
    'facial_emotion':     0.10,   # HSEmotion
    'audio_engagement':   0.05,   # TRIBE v2 A1
}
```

---

## Bekannte Limitierungen

| Problem | Ursache | Geplanter Fix |
|---|---|---|
| center_bias=1.0 für alle | ViNet-S zentriert Tech-Ads immer | ROI Bounding Boxes definieren |
| CLIP brand_match=0.2 für alle | 5 gleich-wahrscheinliche Labels | Brand-spezifische Labels |
| TRIBE ~8 Min/Video | V-JEPA2-vitg, 104 Clips | Flash Attention oder freq 2→1 Hz |

---

## Startbefehle

```bash
cd ~/neuro_pipeline_project
source venv_rocm/bin/activate
rocm-smi --setperflevel high

# Pipeline A vollständig
python pipeline_runner.py campaigns/apple_vs_samsung/ \
    --brand-labels "sleek minimalist" "vibrant energy" "cinematic" \
    --device cuda

# Ohne TRIBE (schnell, ~30s)
python pipeline_runner.py campaigns/apple_vs_samsung/ --skip tribe --device cuda

# Nur TRIBE (nach Cache-Löschung)
python pipeline_runner.py campaigns/apple_vs_samsung/ --only tribe --device cuda

# Brain-Visualisierung
python visualize_brain.py campaigns/test_campaign/scores/sintel_trailer_tribe_preds.npy --temporal
```

---

## Nächste Schritte

1. **Apple vs Samsung Ergebnisse auswerten** — TRIBE-Cache aus heutigem Run
2. **MiroFish API Wrapper** — `POST /api/simulation/create` etc.
3. **Platform Analyzer** — Safe Zones für Instagram/TikTok/YouTube
4. **Streamlit Dashboard** — Ranking + Brain Maps + Saliency + Platform Overlays

---

## Kampagnen-Ordnerstruktur

```
campaigns/
└── marke_2026/
    ├── assets/     ← Videos/Bilder
    ├── scores/     ← JSON Scores + .npy + PNG Outputs
    ├── mirofish/   ← Manuelle Reports (JSON ablegen)
    └── report/     ← pipeline_a_results.json
```
