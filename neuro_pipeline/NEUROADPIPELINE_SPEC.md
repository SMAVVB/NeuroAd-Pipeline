# NeuroAd Pipeline — Technical Specification

**Version:** 2.0 — 31. März 2026  
**Autoren:** Vincent + Claude  
**Hardware:** The Beast (AMD Strix Halo, Ryzen AI MAX+ 395, 96 GB Unified Memory)  
**Lizenz:** Non-commercial research (CC BY-NC für TRIBE v2, CC BY-NC-SA für ViNet++)

---

## 1. Zusammenfassung

NeuroAd ist eine lokal laufende Neuromarketing-Analyse-Plattform. Sie bewertet bestehende Werbung (Pipeline A) und generiert neue Werbung (Pipeline B) unter Einsatz neurowissenschaftlicher KI-Modelle:

- **TRIBE v2** — fMRI-basierte neurale Response-Vorhersage
- **ViNet++** — visuelle Aufmerksamkeitsvorhersage (Eye-Tracking Simulation)
- **MiroFish** — soziale Multi-Agent-Simulation
- **CLIP / HSEmotion** — Brand Consistency + Facial Emotion

Das System läuft vollständig lokal auf The Beast — keine Cloud-Abhängigkeiten.

**Kernprinzip:** NeuroAd ist ein Entscheidungshilfe-Tool, kein Orakel. Die Stärke liegt im relativen Vergleich: "Creative A aktiviert das emotionale Verarbeitungszentrum 23% stärker als Creative B" ist eine valide Aussage. "Creative A wird 50% mehr Conversions bringen" ist es nicht.

---

## 2. Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    PIPELINE A (MVP)                         │
│                                                             │
│  Input: Ad Assets (Video/Bild)                              │
│      │                                                      │
│      ├─ TRIBE v2        → neurale Response (fMRI)           │
│      ├─ ViNet-S/A       → visuelle Aufmerksamkeit           │
│      ├─ CLIP            → Brand Consistency                 │
│      ├─ HSEmotion       → Facial Emotion                    │
│      └─ MiroFish        → Social Simulation                 │
│                  │                                          │
│                  └─ Composite Score → Report + Brain Maps   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    PIPELINE B (Post-MVP)                    │
│                                                             │
│  Input: Brand + Kampagnenziel + Zielgruppe                  │
│      │                                                      │
│      ├─ Brand Research Agent (Lemonade + Crawl4AI)          │
│      ├─ Creative Brief (LLM)                                │
│      ├─ Video Gen (Wan2.1 / CogVideoX)                      │
│      ├─ Bild Gen (Flux.1 / SDXL)                            │
│      ├─ Copy Gen (Qwen / LLaMA)                             │
│      └─ → Pipeline A Scoring → Iteration Loop              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Scoring-Module (MVP — implementiert)

### 3.1 TRIBE v2 — Neurale Response

**Was:** Sagt vorher wie ein menschliches Gehirn auf Video/Audio/Text reagiert (fMRI-Simulation über 20.484 kortikale Vertices, fsaverage5).

**Architektur:** Feature-Extraktoren (V-JEPA2 für Video, LLaMA 3.2-3B für Text, Wav2Vec-BERT für Audio) → FmriEncoder Transformer (8 Layer, D=1152) → kortikale Aktivierungskarte.

**ROI-Scores:**
| ROI | Gehirnregion | Bedeutung für Werbung |
|---|---|---|
| TPJ | Temporoparietal Junction | Emotionale Verarbeitung, Empathie |
| FFA | Fusiform Face Area | Gesichtserkennung, soziale Bindung |
| PPA | Parahippocampal Place Area | Szenen, Umgebungen, Kontext |
| V5/MT | Motion Area | Bewegungswahrnehmung, Dynamik |
| Broca | Sprachzentrum | Sprachverarbeitung, Syntax |
| A1 | Auditory Cortex | Klang, Musik, Stimme |

**Limitierungen:** ~8 Min/Video, Population-Level (kein Demografie-Split), CC BY-NC Lizenz.

**Optimierungsoptionen (noch nicht implementiert):**
- `TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1` → Flash Attention ~2-3x schneller
- `frequency 2.0→1.0 Hz` → 2x schneller, leichter Qualitätsverlust
- neuralset/exca Feature-Cache → zweiter Run in Sekunden

### 3.2 ViNet++ (ViNet-S/A) — Visuelle Aufmerksamkeit

**Was:** Sagt vorher wohin ein Mensch bei einem Video zuerst schaut — Saliency Heatmap.

**ViNet-S:** 36 MB, 1000+ fps, state-of-the-art auf DHF1K.  
**ViNet-A:** 148 MB, Audio-Visual, nutzt zusätzlich den Audio-Track des Videos.

**Output:** Per-Frame Saliency Maps + Heatmap PNGs + ROI-Scores (wenn Bounding Boxes definiert).

**Limitierung aktuell:** `center_bias` als Aggregationsmetrik ist zu grob. ROI Bounding Boxes (Produkt, Logo, CTA) müssen manuell oder via Auto-Detektion definiert werden.

### 3.3 CLIP — Brand Consistency

**Was:** Misst semantische Ähnlichkeit zwischen Creative und Brand-Beschreibungen.

**Hinweis:** Labels müssen beschreibend sein ("sleek minimalist design"), keine Brand-Namen. Brand-spezifische Referenz-Embeddings wären präziser als Text-Labels.

### 3.4 HSEmotion — Facial Emotion

**Was:** Erkennt Emotionen in menschlichen Gesichtern im Creative.

**Relevant für:** People-Ads, Testimonials, Lifestyle. Nicht relevant für Product-Shot-lastige Tech-Ads.

**Emotions:** happiness, sadness, anger, fear, disgust, surprise, neutral → emotional_valence (-1 bis 1).

### 3.5 MiroFish — Social Simulation

**Was:** Generiert AI-Agents mit Persönlichkeiten die auf simulierten Social-Media-Plattformen auf das Creative reagieren.

**Status:** Läuft lokal (localhost:3000/5001/7474), REST API Wrapper steht aus.

**Output:** positive_sentiment, virality_score, controversy_risk, key_reactions.

---

## 4. Post-MVP Erweiterungen

### 4.1 Platform Analyzer — Safe Zone Scoring

**Priorität: Hoch — direkt nächste Session**

Für Werbung auf sozialen Plattformen ist entscheidend ob wichtige visuelle Elemente vom Platform-UI verdeckt werden.

```
TikTok/Stories (9:16, 1080×1920):
  Gesperrt:  Like/Comment/Share (rechts, y:800-1400)
             Username + Caption (unten, y:1600-1920)
  Safe Zone: x:0-880, y:80-1600

Instagram Feed (4:5, 1080×1350):
  Gesperrt:  Username + Interaktionen (oben/unten ~120px)
  Safe Zone: x:0-1080, y:120-1230

YouTube Pre-Roll (16:9):
  Kritisch:  Erste 5 Sekunden (Skip Window)
             Skip-Button unten links (nach 5s)
  Safe Zone: Erste 5s vollständig frei halten
```

**Output:** Annotiertes PNG + "X% der Top-Saliency liegt in sicherer Zone" + Warnung wenn Produkt/Logo in gesperrter Zone.

### 4.2 MiroFish API Wrapper

**Priorität: Hoch**

MiroFish läuft bereits. Wrapper in `pipeline_runner.py` einbauen:

```python
# Bekannte Endpoints
POST /api/graph/ontology/generate  # Ontologie aus Brand-Context
POST /api/graph/build              # Knowledge Graph aufbauen
POST /api/simulation/create        # Simulation erstellen
POST /api/simulation/prepare       # Agents vorbereiten
GET  /api/simulation/<id>          # Status pollen
POST /api/report/generate          # Report erstellen
GET  /api/report/by-simulation/<id> # Report abrufen
```

### 4.3 Streamlit Dashboard

**Priorität: Mittel**

Erreichbar per Tailscale. Features:
- Creative Ranking Tabelle (sortiert nach Composite Score)
- Brain Heatmap (Nilearn PNG, später interaktiv via Plotly)
- Temporal Activation Profile (welche Momente aktivieren das Gehirn?)
- Saliency Overlay + Platform Safe Zone Annotation
- MiroFish Sentiment Timeline
- Export als PDF-Report

### 4.4 Brand Research Agent

**Priorität: Mittel (Voraussetzung für vollständige Kalibrierung)**

Agent der automatisch Brand-DNA extrahiert und alle Scorer kalibriert:

```
Brand Research Agent (Lemonade SDK + Crawl4AI)
    ├── Crawlt Website, Ad Library, Social Media
    ├── Extrahiert Brand DNA (Visual Style, Tone, Key Messages)
    ├── Generiert CLIP Labels (brand-spezifisch)
    ├── Definiert ROI-Templates (wo ist typisch Produkt/Logo/CTA?)
    ├── Schlägt Composite Weights vor
    └── Validierungs-Modell prüft Konsistenz
```

**TurboQuant-Integration:** 3-Bit KV-Cache Kompression ermöglicht ~100k-200k Token Kontext für den Research Agent — genug für komplette Brand Guidelines + Ad-Bibliothek + Competitor-Analysis in einem einzigen Pass. TurboQuant PR für llama.cpp ist aktiv, bei Merge direkt testen.

### 4.5 Weitere sinnvolle Scoring-Tools (nicht im MVP)

#### ViNet-A statt ViNet-S
Audio-Visual Saliency nutzt zusätzlich den Audio-Track. Checkpoint liegt bereits unter `tools/ViNet_v2/final_models/ViNet_A/`. Swap ist ein Einzeiler im pipeline_runner.

#### Grounding DINO — Auto-ROI-Detektion
Erkennt automatisch Produkt, Logo und CTA in Frames ohne manuelle Bounding Boxes. Open-Source, ~700 MB. Würde den center_bias-Bug vollständig lösen.

```python
# Konzept
from groundingdino.util.inference import load_model, predict
boxes = predict(model, image, caption="product . logo . call to action")
# → automatische ROI-Definitionen für Saliency Scorer
```

#### EfficientFace / MTCNN — besserer Face Detector
HSEmotion verlässt sich auf einen schwachen internen Detektor. MTCNN findet Gesichter zuverlässiger — besonders bei kleinen/seitlichen Gesichtern in Werbung.

#### Whisper Large v3 — Audio-Analyse
Transkription + Sentiment des gesprochenen Texts im Ad. "Ist die Message klar und emotional passend?" Läuft bereits teilweise über TRIBE v2, aber separater dedizierter Pass wäre präziser.

#### SigLIP statt CLIP
Google SigLIP ist CLIP-ähnlich aber deutlich besser für nicht-englische Texte und beschreibende Labels. Gleiches Interface, Drop-In-Replacement. Besonders relevant für deutsche/europäische Marken.

---

## 5. Pipeline B — Creative Generation (Post-MVP)

### 5.1 Video-Generierung
- **Wan2.1** (Alibaba) — aktuell state-of-the-art, verschiedene Modellgrößen
- **CogVideoX-5B** (Tsinghua/ZhipuAI) — Q4 quantisiert, ~15-20 GB

### 5.2 Bild-Generierung
- **Flux.1-dev** (Black Forest Labs) — High Quality, ~12-15 GB, bereits installiert
- **SDXL** — schnelle Iteration, viele ControlNet-Erweiterungen

### 5.3 Audio/Musik-Generierung
Neurales A/B-Testing für Soundtracks: TRIBE v2 scored Video-only vs. Audio-only vs. Kombination.

| Tool | Was | Größe | Lizenz |
|---|---|---|---|
| DiffRhythm | Full-Song Diffusion | ~2-4 GB | MIT |
| Qwen3-TTS (0.6B-1.7B) | Voiceover | ~1-3 GB | Apache 2.0 |
| MusicGen (Meta) | Text-to-Music | ~3-10 GB | CC BY-NC |

### 5.4 Iteration Loop
Score → LLM-Analyse → Re-Generate → Score (1-3 Runden). Creative mit höchstem Composite Score wird als Grundlage für die nächste Generation genutzt.

---

## 6. Erweiterte Analyse-Features (Forschungs-Roadmap)

### 6.1 KPI-Kalibrierung
XGBoost/LightGBM Regression die NeuroAd-Scores auf echte Kampagnen-KPIs (CTR, ROAS, CPA) mappt. Benötigt 200+ historische Creatives mit KPI-Daten. R² von 0.3-0.5 realistisch für relative Rankings.

### 6.2 Arousal-Valence Mapping
Circumplex-Modell der Emotionen (Erregung × Wertigkeit) pro Creative. Jedes Creative als Punkt auf 2D-Map: "Wir wollen Begeisterung (hoch Arousal, positiv Valence)" → Validierung ob Creative dorthin landed.

### 6.3 Ablative Creative-Zerlegung
Systematische Varianten eines Creatives (anderes Farbschema, ohne Gesicht, anderer Schnittrhythmus) → ΔTRIBE, ΔSaliency pro Änderung. "Das Logo im Thumbnail ist für +23% Neural Engagement verantwortlich."

### 6.4 Zielgruppen-Differenzierung
MiroFish Persona-Templates für verschiedene Demografien (Gen Z, Millennials, Boomers). Kombination: TRIBE v2 Population-Level + MiroFish-Segmente für soziale Differenzierung.

### 6.5 Competitive Intelligence Dashboard
Automatisches wöchentliches Scoring der Wettbewerber-Ads via Meta Ad Library API. Alert wenn Wettbewerber ungewöhnlich hohen Emotional-Impact-Score erzielt.

---

## 7. Hardware & Memory Management

### 7.1 Memory Budget (48 GB CPU-RAM, 48 GB GPU-Buffer)

| Phase | Aktive Modelle | GPU Peak |
|---|---|---|
| TEXT (LLaMA 3.2-3B) | LLaMA ~6 GB | ~6 GB |
| AUDIO (Wav2Vec-BERT) | Wav2Vec ~2 GB | ~2 GB |
| VIDEO (V-JEPA2-vitg) | V-JEPA2 ~20 GB | ~25 GB |
| TRIBE Transformer | FmriEncoder ~1 GB | ~1 GB |
| ViNet-S Saliency | ViNet ~0.04 GB | ~0.5 GB |
| CLIP | ViT-B/32 ~0.6 GB | ~0.6 GB |

**Prinzip:** Nie mehr als ein großes Modell gleichzeitig. `dataloader.py` Patch entlädt nach jedem `prepare()`. V-JEPA2 Config: num_frames=16, max_imsize=256.

### 7.2 TurboQuant (Zukunft)
3-Bit KV-Cache Kompression für alle LLM-Phasen:
- 6x weniger Memory für KV-Cache
- 8x schnellere Attention
- Ermöglicht ~100k-200k Token Kontext für Brand Research Agent
- Testen sobald llama.cpp PR gemerged ist

### 7.3 Flash Attention (Optimierung)
```bash
export TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1
```
Aktiviert Flash Attention + Memory Efficient Attention auf AMD. Warnung erscheint bereits im Log — Schätzung 2-3x schneller für V-JEPA2.

---

## 8. Ehrliche Einschätzung

**Was NeuroAd kann:**
- Relative Vergleiche: "Creative A aktiviert FFA 23% stärker als Creative B"
- Schwachstellen identifizieren: "Logo wird vom TikTok-UI verdeckt"
- Hypothesen generieren: "Diese Szene ist der emotionale Höhepunkt"
- Creatives vor dem Launch testen ohne Fokusgruppen

**Was NeuroAd nicht kann:**
- Kaufentscheidungen direkt vorhersagen
- Kulturelle Nuancen abbilden (TRIBE v2 ist auf Population-Average trainiert)
- Echte fMRI-Studien ersetzen für klinische Zwecke
- Exakte Viral-Zahlen garantieren (MiroFish ist Simulation, nicht Realität)

**Wann NeuroAd am wertvollsten ist:**
Wenn mehrere Creatives zur Auswahl stehen und die Frage lautet "welches ist neurobiologisch stärker?" — nicht "wird dieses Creative erfolgreich sein?"

---

## 9. Priorisierungs-Matrix

| Feature | Schwierigkeit | Impact | MVP? |
|---|---|---|---|
| MiroFish API Wrapper | Niedrig | Hoch | ✅ Nächste Session |
| Platform Analyzer | Niedrig | Hoch | ✅ Nächste Session |
| Streamlit Dashboard | Mittel | Hoch | Ja |
| Brand Research Agent | Mittel | Sehr hoch | Nein |
| ViNet-A statt ViNet-S | Sehr niedrig | Mittel | Optional |
| Grounding DINO ROI-Auto | Niedrig | Hoch | Empfohlen |
| SigLIP statt CLIP | Sehr niedrig | Mittel | Optional |
| Flash Attention | Niedrig | Hoch (Speed) | Empfohlen |
| KPI-Kalibrierung | Mittel | Sehr hoch | Post-MVP |
| Pipeline B (Generation) | Hoch | Hoch | Post-MVP |
| Ablative Analyse | Mittel | Sehr hoch | Post-MVP |
| Arousal-Valence Map | Niedrig | Mittel | Post-MVP |
| TurboQuant | Niedrig (warten) | Hoch | Post-MVP |
| Competitive Intelligence | Mittel | Hoch | Post-MVP |
| KPI-Kalibrierung | Mittel | Sehr hoch | Post-MVP |
| Zielgruppen-Differenzierung | Hoch | Hoch | Post-MVP |
