# NeuroAd Pipeline — MVP Plan

**Stand:** 30. März 2026  
**Hardware:** The Beast (AMD Strix Halo, 96 GB Unified Memory, Ubuntu)  
**Scope:** Pipeline A only — bestehende Werbung analysieren, keine Generierung

---

## Aktueller Infrastruktur-Status

| Komponente | Status | Anmerkung |
|---|---|---|
| GPU/ROCm (Radeon 8060S) | ✅ | CUDA=True via ROCm |
| MiroFish + Neo4j 5.18 | ✅ | localhost:3000 / :7474 |
| HSEmotion | ✅ | Import OK |
| CLIP | ✅ | Import OK |
| Flux.1 (diffusers) | ✅ | Import OK |
| Lemonade SDK | ✅ | Port 8888, 131k ctx |
| TRIBE v2 (CPU) | ✅ | Läuft, Inferenz aktiv |
| TRIBE v2 (ROCm/GPU) | ❌ | Segfault — Priority Fix |
| DeepGaze IIE | ❌ | Bitbucket URLs tot, skippen |
| ViNet-S | ⚠️ | Kein pip install, direkt als Script |

### Bekannte Patches (neuralset Library)
Diese Patches wurden bereits angewandt um CPU-only Betrieb zu ermöglichen:
- `neuralset/extractors/text.py` — device auf "cpu" gepatcht (Zeilen 350, 400, 419)
- `neuralset/extractors/audio.py` — alle `.to(self.device)` auf `.to("cpu")`
- `neuralset/extractors/video.py` — device auf "cpu" gepatcht
- `tribev2/tribev2/eventstransforms.py` — WhisperX compute_type auf "int8"

### TRIBE v2 starten (CPU-only, bis ROCm gefixt)
```bash
cd ~/neuro_pipeline_project
source venv/bin/activate
HSA_OVERRIDE_GFX_VERSION="" ROCR_VISIBLE_DEVICES="" HIP_VISIBLE_DEVICES="-1" CUDA_VISIBLE_DEVICES="-1" \
python your_script.py
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
│  TRIBE v2 → Saliency → CLIP → MiroFish  │
└─────────────────────────────────────────┘
        │
        ▼
Composite Scorer                 ← Gewichteter Gesamt-Score
        │
        ▼
Dashboard (Streamlit/Tailscale)
  ├── Brain Heatmap (Nilearn)
  ├── Saliency Map Overlay
  ├── MiroFish Sentiment Report
  └── Creative Ranking Tabelle
```

---

## Ordnerstruktur pro Kampagne

```
~/neuro_pipeline_project/campaigns/
└── nike_2026/
    ├── assets/          ← Videos/Bilder rein (manuell oder per URL)
    ├── scores/          ← TRIBE + Saliency Outputs (JSON)
    ├── mirofish/        ← Simulation Reports
    └── report/          ← Finaler Output (PDF/HTML)
```

---

## Prioritäten für die nächsten Sessions

### Priorität 1 — ROCm Fix für TRIBE v2
TRIBE v2 segfaultet wenn ROCm aktiv ist. Ohne GPU-Beschleunigung dauert
Video-Encoding ~55 Min statt ~2-3 Min.

**Vorgehen:**
1. ROCm-Version prüfen: `rocminfo | head -20`
2. PyTorch ROCm-Build verifizieren: `python -c "import torch; print(torch.version.hip)"`
3. Separaten Test mit explizitem `device='cuda'` (ROCm-Alias)
4. Falls nötig: PyTorch ROCm-Build neu installieren passend zur ROCm-Version

### Priorität 2 — ViNet-S + MiroFish API testen
- ViNet-S: `generate_result.py` direkt aufrufen mit Test-Video
- MiroFish: REST API Aufruf testen, Simulation-Job starten, Report auslesen

### Priorität 3 — Pipeline-Code bauen
Drei Wrapper + ein Orchestrator:

```
neuro_pipeline_project/
├── tribe_scorer.py       ← TRIBE v2 Wrapper, gibt ROI-Scores zurück
├── saliency_scorer.py    ← ViNet-S Wrapper
├── mirofish_runner.py    ← MiroFish API Client
├── clip_scorer.py        ← CLIP Brand Consistency
├── composite_scorer.py   ← Gewichtete Kombination
└── pipeline_runner.py    ← Orchestrator: nimmt Kampagnen-Ordner, läuft alles durch
```

**pipeline_runner.py Grundstruktur:**
```python
def run_pipeline_a(campaign_dir: str):
    assets = collect_assets(campaign_dir)
    for asset in assets:
        scores = {}
        scores['tribe'] = tribe_scorer.score(asset)
        scores['saliency'] = saliency_scorer.score(asset)
        scores['clip'] = clip_scorer.score(asset)
    scores['mirofish'] = mirofish_runner.simulate(assets[:5], brand_context)
    composite = composite_scorer.combine(scores)
    generate_report(campaign_dir, composite)
```

### Priorität 4 — Dashboard
Streamlit-App, erreichbar per Tailscale:
- Kampagne auswählen
- Brain Heatmap via Nilearn (statisches PNG oder interaktiv)
- Saliency Overlay auf Original-Frame
- MiroFish Sentiment Timeline (Plotly Chart)
- Score-Tabelle: alle Creatives nebeneinander

---

## Scoring-Gewichtung (MVP Default)

```python
WEIGHTS = {
    'neural_engagement':  0.30,  # TRIBE v2 Gesamt-Aktivierung
    'emotional_impact':   0.20,  # TRIBE v2 TPJ (emotionale Verarbeitung)
    'visual_attention':   0.20,  # Saliency auf Produkt/CTA
    'brand_consistency':  0.15,  # CLIP Score
    'social_sentiment':   0.15,  # MiroFish positiver Sentiment
}
```

---

## Offene Fragen / Entscheidungen

- [ ] DeepGaze Ersatz — ViNet-S reicht für MVP, DeepGaze später wenn Bitbucket-Mirror gefunden
- [ ] Lemonade als Research-Agent konfigurieren (welches Modell, welcher Prompt)
- [ ] MiroFish Persona-Templates definieren (Zielgruppe pro Kampagne)
- [ ] Dashboard-Hosting: Streamlit lokal + Tailscale oder doch nginx?
