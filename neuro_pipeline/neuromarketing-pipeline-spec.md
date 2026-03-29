# NeuroAd Pipeline — Technical Specification

## AI-Powered Neuro-Marketing Analysis & Generation Platform

**Author:** Vincent (with Claude)
**Date:** 28. März 2026
**Hardware Target:** Strix Halo Mini PC ("The Beast") — AMD APU, 96 GB Unified Memory, Ubuntu
**License Scope:** Non-commercial research (CC BY-NC for TRIBE v2)

---

## 1. Executive Summary

NeuroAd ist eine lokal laufende End-to-End-Pipeline, die bestehende Werbung analysiert und neue Werbung generiert, optimiert und bewertet — unter Einsatz von neurowissenschaftlicher Gehirnsimulation (TRIBE v2), visueller Aufmerksamkeitsvorhersage (Saliency/Eye-Tracking) und sozialer Multi-Agent-Simulation (MiroFish).

Das System besteht aus zwei Pipelines:
- **Pipeline A — Analyse:** Bestehende Werbung bewerten und optimieren
- **Pipeline B — Vollständig:** Neue Werbung generieren, testen, iterieren

Beide Pipelines teilen sich die Scoring-Module (TRIBE v2, Saliency, MiroFish) und laufen vollständig auf lokaler Hardware.

---

## 2. Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATION LAYER                         │
│                   (DeerFlow 2.0 / Custom Agent)                    │
├─────────────┬──────────────┬──────────────┬────────────────────────┤
│             │              │              │                        │
│  ┌──────────▼──────────┐   │   ┌──────────▼──────────┐            │
│  │   PIPELINE A        │   │   │   PIPELINE B        │            │
│  │   Analyse           │   │   │   Generierung       │            │
│  │                     │   │   │                     │            │
│  │  1. Brand Research  │   │   │  1. Brand Research  │            │
│  │  2. Asset Collect   │   │   │  2. Brief Erstellung│            │
│  │  3. → Scoring →     │   │   │  3. Creative Gen    │            │
│  │  4. Report          │   │   │  4. → Scoring →     │            │
│  └─────────────────────┘   │   │  5. Iteration       │            │
│                            │   │  6. Report          │            │
│                            │   └─────────────────────┘            │
│              ┌─────────────▼─────────────┐                        │
│              │     SCORING MODULES       │                        │
│              │                           │                        │
│              │  ┌─────────────────────┐  │                        │
│              │  │  TRIBE v2           │  │                        │
│              │  │  Neuro-Response     │  │                        │
│              │  │  (fMRI Prediction)  │  │                        │
│              │  └─────────────────────┘  │                        │
│              │  ┌─────────────────────┐  │                        │
│              │  │  Saliency Engine    │  │                        │
│              │  │  (DeepGaze IIE +    │  │                        │
│              │  │   Video Saliency)   │  │                        │
│              │  └─────────────────────┘  │                        │
│              │  ┌─────────────────────┐  │                        │
│              │  │  MiroFish Offline   │  │                        │
│              │  │  Social Simulation  │  │                        │
│              │  └─────────────────────┘  │                        │
│              └───────────────────────────┘                        │
│              ┌───────────────────────────┐                        │
│              │     CREATIVE MODULES      │                        │
│              │  (nur Pipeline B)         │                        │
│              │                           │                        │
│              │  Video: CogVideoX / Wan2.1│                        │
│              │  Bild:  Flux.1 / SDXL     │                        │
│              │  Text:  LLaMA / Qwen      │                        │
│              └───────────────────────────┘                        │
├─────────────────────────────────────────────────────────────────────┤
│                       INFERENCE LAYER                              │
│           Lemonade SDK / Ollama / llama.cpp (Vulkan)               │
│           + TurboQuant KV Cache Compression (3-bit)                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Hardware & Memory Management

### 3.1 Grundprinzip: Maximal 2 Modelle gleichzeitig

Mit 96 GB Unified Memory ist genug Platz vorhanden, aber nicht für alles gleichzeitig. Die Pipeline arbeitet **sequentiell mit dynamischem Model-Swapping**:

| Phase | Aktive Modelle | Geschätzter RAM |
|-------|---------------|-----------------|
| Research/Scraping | LLM (Qwen 3 ~20 GB) | ~20 GB |
| Video-Feature-Extraktion | V-JEPA2 (~20-25 GB) + TRIBE Encoder (~5 GB) | ~30 GB |
| Audio-Feature-Extraktion | Wav2Vec-BERT (~3-5 GB) + TRIBE Encoder (~5 GB) | ~10 GB |
| Text-Feature-Extraktion | LLaMA 3.2 (~10-15 GB) + TRIBE Encoder (~5 GB) | ~20 GB |
| Saliency | DeepGaze IIE (~2-4 GB) | ~4 GB |
| Video Saliency | ViNet-S (~36 MB) oder SalFoM (~2-4 GB) | ~4 GB |
| Social Simulation | LLM für MiroFish Agents (Qwen 2.5:32b ~20 GB) | ~25 GB |
| Bild-Generierung | Flux.1-dev / SDXL (~12-20 GB) | ~20 GB |
| Video-Generierung | CogVideoX-5B Q4 (~15-20 GB) | ~20 GB |

### 3.2 TurboQuant Integration

TurboQuant (Google, März 2026) komprimiert den KV-Cache auf 3 Bit ohne Qualitätsverlust:
- **6x weniger Memory** für den KV-Cache
- **Bis zu 8x schnellere Attention** Berechnung
- Training-frei und data-oblivious — direkt anwendbar

**Relevanz für NeuroAd:**
- LLM-Phasen (Research, MiroFish Agents, Creative Text) profitieren am meisten
- Ermöglicht größere Kontextfenster bei gleicher Hardware (z.B. 100k+ Token statt 16k)
- Besonders wichtig für MiroFish, wo viele Agents lange Konversationen führen

**Implementierung:**
- llama.cpp Integration: Aktiver PR auf GitHub (`ggml-org/llama.cpp/discussions/20969`) mit funktionierender CPU-Implementation, TQ3 bei 4.9x Kompression
- PyTorch Implementation: `tonbistudio/turboquant-pytorch` — validiert auf Qwen2.5-3B mit 99.5% Attention-Fidelity bei 3-bit
- MLX Implementation ebenfalls verfügbar

**Empfehlung:** Starte mit der llama.cpp TQ3 Integration, sobald sie gemerged ist. Bis dahin: Standard Q4_K_M Quantisierung als Baseline.

### 3.3 Model-Swap-Strategie

```python
# Pseudocode für den Model Manager
class ModelManager:
    """Lädt/entlädt Modelle dynamisch basierend auf Pipeline-Phase"""
    
    MAX_LOADED_MODELS = 2
    TOTAL_RAM_GB = 96
    RESERVED_SYSTEM_GB = 8  # OS + Desktop
    AVAILABLE_GB = 88
    
    def load_model(self, model_name, estimated_gb):
        while self.used_memory + estimated_gb > self.AVAILABLE_GB:
            self.unload_least_recently_used()
        # Load model
        
    def transition_phase(self, from_phase, to_phase):
        """Entlädt Modelle der alten Phase, lädt neue"""
        models_to_unload = from_phase.models - to_phase.models
        models_to_load = to_phase.models - from_phase.models
        for m in models_to_unload: self.unload(m)
        for m in models_to_load: self.load(m)
```

---

## 4. Open-Source Bausteine — Detailliert

### 4.1 TRIBE v2 — Neuro-Response Scoring

**Was es tut:** Nimmt Video, Audio oder Text als Input und sagt vorher, wie ein menschliches Gehirn darauf reagiert (fMRI-Response über ~70.000 kortikale Vertices).

**Repos:**
- GitHub: `facebookresearch/tribev2`
- HuggingFace: `facebook/tribev2`
- Live Demo: `aidemos.atmeta.com/tribev2`

**Architektur:**
- Feature-Extraktoren: V-JEPA2 (Video), LLaMA 3.2 (Text), Wav2Vec-BERT (Audio)
- Encoder: Transformer, 8 Layer, 8 Attention Heads, D_model = 1152
- Input-Fenster: 100 Sekunden
- Output: 20.484 kortikale Vertices (fsaverage5 Surface)

**Lizenz:** CC BY-NC (nicht-kommerziell!)

**Key Files für Inferenz:**
```
tribev2/
├── demo_utils.py          # TribeModel Klasse — Hauptentry für Inferenz
├── model.py               # FmriEncoder Architektur
├── utils_fmri.py          # Surface Projection & ROI Analyse
└── plotting/              # Brain Visualisierung (PyVista + Nilearn)
```

**Metriken, die du pro Creative extrahieren kannst:**
- **Regionale Aktivierung:** Welche Gehirnareale reagieren wie stark?
  - FFA (Fusiform Face Area) — Gesichtserkennung
  - PPA (Parahippocampal Place Area) — Orte/Szenen
  - TPJ (Temporoparietal Junction) — Emotionale Verarbeitung
  - Broca's Area — Sprachverarbeitung/Syntax
  - V5/MT — Bewegungswahrnehmung
  - Primary Auditory Cortex — Klangverarbeitung
- **Gesamtaktivierung:** Wie stark ist die neurale Response insgesamt?
- **Modalitäts-Balance:** Reagiert das Gehirn eher auf visuell, auditiv oder textuell?
- **Temporal Profile:** Wie verändert sich die Aktivierung über die Dauer des Clips?

### 4.2 Saliency Engine — Visuelle Aufmerksamkeit

**Was es tut:** Sagt vorher, wohin ein Mensch bei einem Bild oder Video zuerst schaut — Heatmap der visuellen Aufmerksamkeit.

#### 4.2.1 Bilder: DeepGaze IIE

**Repo:** `github.com/matthias-k/DeepGaze` (Tübingen Saliency Benchmark)
**Paper:** ICCV 2021 — State-of-the-art auf MIT300 Benchmark
**Größe:** ~2-4 GB (nutzt vortrainierte Backbones: ResNet, DenseNet, etc.)
**Output:** Saliency Map (Wahrscheinlichkeits-Heatmap) pro Bild

**Metriken:**
- Fixation-Density über Produkt/Logo/CTA
- Saliency-Score der Key-Elemente relativ zum Gesamtbild
- Scanpath-Simulation (DeepGaze III): In welcher Reihenfolge schaut der Viewer?

#### 4.2.2 Videos: ViNet-S / SalFoM

**ViNet-S:** Nur 36 MB, über 1000 FPS, State-of-the-art auf DHF1K und 6 Audio-Visual Datasets
- Repo: `github.com/samyak0210/ViNet` (check neueste Version)
- Ideal für schnelle Batch-Verarbeitung vieler Video-Varianten

**SalFoM:** Video Foundation Model für dynamische Saliency
- Repo: `github.com/mr17m/SalFoM—Video-Saliency-Prediction`
- Nutzt Video Foundation Models, langsamerer aber genauer

**Metriken pro Video-Frame/-Sequenz:**
- Saliency über Brand-Elementen (Logo, Produkt, Text)
- Attention-Flow: Wie wandert der Blick über die Szene?
- Audio-Visual Congruence: Schaut der Viewer dorthin, wo der Sound herkommt?

#### 4.2.3 Kombinations-Score: Neuro + Saliency

```python
# Scoring-Komposition
def compute_creative_score(tribe_result, saliency_result):
    """
    Kombiniert Neuro-Response und Saliency zu einem Gesamt-Score.
    """
    # Neuro-Scores (TRIBE v2)
    emotional_activation = tribe_result.roi_activation['TPJ']
    face_response = tribe_result.roi_activation['FFA']
    motion_response = tribe_result.roi_activation['V5']
    language_engagement = tribe_result.roi_activation['Broca']
    total_neural = tribe_result.mean_activation
    
    # Saliency-Scores
    product_attention = saliency_result.roi_saliency['product_bbox']
    cta_attention = saliency_result.roi_saliency['cta_bbox']
    brand_attention = saliency_result.roi_saliency['logo_bbox']
    first_fixation_target = saliency_result.scanpath[0].target
    
    # Gewichteter Gesamt-Score (Gewichte anpassbar)
    score = {
        'neural_engagement': total_neural * 0.30,
        'emotional_impact': emotional_activation * 0.20,
        'visual_attention': product_attention * 0.20,
        'brand_recall': brand_attention * 0.15,
        'cta_visibility': cta_attention * 0.15,
    }
    score['total'] = sum(score.values())
    return score
```

### 4.3 MiroFish Offline — Social Simulation

**Was es tut:** Generiert hunderte/tausende AI-Agents mit eigenen Persönlichkeiten, die auf simulierten Social-Media-Plattformen interagieren. Testet, wie eine Werbekampagne sozial aufgenommen werden könnte.

**Repo:** `github.com/nikmcfly/MiroFish-Offline` (Englischer Fork, voll lokal)
**Engine:** OASIS (CAMEL-AI) — bis zu 1 Million Agent-Interaktionen
**Stack:** Neo4j (Knowledge Graph) + Ollama (LLM) + Docker

**Setup:**
```bash
git clone https://github.com/nikmcfly/MiroFish-Offline.git
cd MiroFish-Offline
cp .env.example .env
docker compose up -d
# Models pullen
docker exec mirofish-ollama ollama pull qwen2.5:32b
docker exec mirofish-ollama ollama pull nomic-embed-text
# UI: http://localhost:3000
```

**Alternativ-Setup mit Lemonade SDK (statt Ollama):**
Du könntest MiroFish so konfigurieren, dass es gegen dein bestehendes Lemonade SDK auf Port 8888 feuert (OpenAI-compatible API). Das spart doppelte Model-Instanzen.

**Relevante Use Cases für NeuroAd:**
- Werbe-Reaction-Test: "Wie reagiert die Öffentlichkeit auf diesen Spot?"
- Sentiment-Analyse: Positiv/Negativ/Neutral Verteilung über Agenten
- Virality-Prediction: Wird geteilt? Entsteht Diskussion?
- PR-Risiko-Check: Gibt es kontroverse Interpretationen?
- Zielgruppen-Segmentierung: Verschiedene Agenten-Demografien konfigurieren

**Seed Material für Simulation:**
```
Input: Generiertes Werbevideo/-bild + Beschreibungstext
       + Brand Context Dokument
       + Zielgruppen-Definition

Output: Simulations-Report mit:
        - Sentiment-Verteilung über Zeit
        - Key Opinion Leader Meinungen
        - Virale Momente identifiziert
        - Kontroverse Punkte
        - Empfohlene Anpassungen
```

### 4.4 TurboQuant — KV-Cache Compression

**Was es tut:** Komprimiert den KV-Cache von LLMs auf 3 Bit ohne Qualitätsverlust — 6x weniger Memory, bis zu 8x schnellere Attention.

**Status (März 2026):**
- Paper: ICLR 2026
- llama.cpp: Aktiver PR mit funktionierender CPU-Implementation
- PyTorch: `tonbistudio/turboquant-pytorch` — validiert
- Anwendbar auf Qwen, LLaMA, Mistral, Gemma

**Integration in NeuroAd:** Anwenden auf alle LLM-Phasen (Research Agent, MiroFish Agents, Creative Text Generation) für größere Kontextfenster bei weniger RAM-Verbrauch.

### 4.5 Creative Generation (nur Pipeline B)

#### Video-Generierung
- **CogVideoX-5B** (Tsinghua/ZhipuAI) — Q4 quantisiert ~15-20 GB
- **Wan2.1** (Alibaba) — Neueres Modell, verschiedene Größen
- Empfehlung: Starte mit dem kleinsten Modell, das akzeptable Qualität liefert

#### Bild-Generierung
- **Flux.1-dev** (Black Forest Labs) — High Quality, ~12-15 GB
- **SDXL** (Stability AI) — Bewährt, ~6-8 GB, viele ControlNet-Erweiterungen
- Empfehlung: SDXL für schnelle Iteration, Flux für finale Varianten

#### Text/Copy-Generierung
- **Qwen 3 Coder Next 70B** (via Lemonade SDK, bereits laufend auf Port 8888)
- Alternativ: Kleineres Modell wie Qwen 2.5:32b für schnellere Iteration
- Prompt-Templates für verschiedene Ad-Formate (Social Copy, Headline, CTA, Script)

### 4.6 Research & Brand Intelligence

#### Web Scraping & Datensammlung
- **Firecrawl** (`github.com/mendableai/firecrawl`) — AI-optimierter Webcrawler
- **Crawl4AI** (`github.com/unclecode/crawl4ai`) — Alternative, async, lightweight
- **Meta Ad Library API** — Competitor-Ads öffentlich einsehbar
- **Social Media APIs** — Platform-spezifisch, teilweise Rate-Limited

#### Orchestrierung
- **DeerFlow 2.0** — Bereits im Setup-Versuch, ideal für den Research-Teil
- **Fallback:** Custom Python-basierter Agent mit LangChain/LangGraph

### 4.7 Zusätzliche sinnvolle Projekte

#### Emotion Recognition: HSEmotion
- **Repo:** `github.com/HSE-asavchenko/face-emotion-recognition`
- Erkennt Emotionen in Gesichtern (Werbung mit Menschen)
- Lightweight, läuft auf CPU
- Kann auf generierte Bilder/Videos angewandt werden: "Drücken die Gesichter in meiner Werbung die richtige Emotion aus?"

#### Brand Consistency Check: CLIP
- **Model:** OpenAI CLIP (oder SigLIP)
- Misst semantische Ähnlichkeit zwischen generierter Werbung und Brand-Referenzen
- "Passt das generierte Bild zur Markenidentität?"
- ~2-4 GB, extrem schnelle Inferenz

#### Audio Analysis: Wav2Vec2 / Whisper
- Transkription und Sentiment-Analyse von Audio in Video-Ads
- Prüfung: "Ist die gesprochene Message klar und emotional passend?"

#### Attention Flow Visualization: Scanpath Prediction
- **DeepGaze III** erweitert DeepGaze IIE um sequentielle Fixations-Vorhersage
- Zeigt nicht nur WO jemand hinschaut, sondern IN WELCHER REIHENFOLGE
- Kritisch für Storytelling in Ads: Schaut der Viewer erst auf das Problem, dann auf die Lösung, dann auf den CTA?

---

## 5. Pipeline A — Analyse bestehender Werbung

### 5.1 Ablauf

```
Input: Unternehmensname / URL / vorhandene Ad-Assets
                    │
                    ▼
         ┌─────────────────────┐
  Step 1 │  Brand Research     │
         │  Agent              │
         │                     │
         │  - Website crawlen  │
         │  - Social Media     │
         │  - Meta Ad Library  │
         │  - News/PR          │
         │  - Wettbewerber     │
         └────────┬────────────┘
                  │
                  ▼
         ┌─────────────────────┐
  Step 2 │  Asset Collection   │
         │                     │
         │  - Video-Ads laden  │
         │  - Image-Ads laden  │
         │  - Text-Ads laden   │
         │  - Metadaten        │
         └────────┬────────────┘
                  │
                  ▼
         ┌─────────────────────┐
  Step 3 │  Scoring            │  ← Sequentiell, Model-Swapping
         │                     │
         │  3a. TRIBE v2       │  ~5-15 Min pro Video-Clip
         │      Neuro-Response │
         │                     │
         │  3b. Saliency       │  ~Sekunden pro Frame
         │      Eye-Tracking   │
         │                     │
         │  3c. MiroFish       │  ~30-60 Min pro Simulation
         │      Social Sim     │
         │                     │
         │  3d. CLIP Score     │  ~Sekunden
         │      Brand Match    │
         └────────┬────────────┘
                  │
                  ▼
         ┌─────────────────────┐
  Step 4 │  Report Generation  │
         │                     │
         │  - Ranking aller    │
         │    Creatives        │
         │  - Brain Heatmaps   │
         │  - Saliency Maps    │
         │  - Social Sentiment │
         │  - Optimierungs-    │
         │    empfehlungen     │
         └─────────────────────┘
```

### 5.2 Erwartete Laufzeit (Pipeline A)

| Step | Dauer (geschätzt) | Anmerkung |
|------|-------------------|-----------|
| Brand Research | 10-30 Min | Abhängig von Crawl-Tiefe |
| Asset Collection | 5-15 Min | Download + Preprocessing |
| TRIBE v2 Scoring (5 Videos) | 30-75 Min | ~5-15 Min/Clip auf CPU/iGPU |
| Saliency Scoring | 2-5 Min | Sehr schnell |
| MiroFish Simulation | 30-60 Min | Abhängig von Agent-Anzahl |
| Report Generation | 5-10 Min | LLM-basiert |
| **Gesamt** | **~1.5-3 Stunden** | Für 5 Video-Creatives |

---

## 6. Pipeline B — Generierung neuer Werbung

### 6.1 Ablauf

```
Input: Unternehmensname + Kampagnenziel + Zielgruppe
                    │
                    ▼
         ┌─────────────────────┐
  Step 1 │  Brand Research     │  (identisch mit Pipeline A Step 1)
         └────────┬────────────┘
                  │
                  ▼
         ┌─────────────────────┐
  Step 2 │  Creative Brief     │
         │                     │
         │  LLM erstellt:      │
         │  - Key Messages     │
         │  - Tone of Voice    │
         │  - Visual Direction │
         │  - Target Emotions  │
         │  - CTA              │
         │  - 3-5 Konzepte     │
         └────────┬────────────┘
                  │
                  ▼
         ┌─────────────────────┐
  Step 3 │  Creative Gen       │  ← Pro Konzept
         │                     │
         │  3a. Video Gen      │  CogVideoX / Wan2.1
         │  3b. Image Gen      │  Flux / SDXL
         │  3c. Copy Gen       │  Qwen / LLaMA
         │  3d. Audio Gen      │  (optional: Bark/XTTS)
         └────────┬────────────┘
                  │
                  ▼
         ┌─────────────────────┐
  Step 4 │  Scoring            │  (identisch mit Pipeline A Step 3)
         │  TRIBE + Saliency   │
         │  + MiroFish + CLIP  │
         └────────┬────────────┘
                  │
                  ▼
         ┌─────────────────────┐
  Step 5 │  Iteration          │  ← Feedback Loop (1-3 Runden)
         │                     │
         │  LLM analysiert     │
         │  Scoring-Ergebnisse │
         │  und generiert      │
         │  optimierte         │
         │  Varianten          │
         └────────┬────────────┘
                  │
                  ▼
         ┌─────────────────────┐
  Step 6 │  Final Report       │
         │                     │
         │  - Top 3 Creatives  │
         │  - Vollständige     │
         │    Neuro-Analyse    │
         │  - A/B Test         │
         │    Empfehlungen     │
         │  - Social Prognose  │
         └─────────────────────┘
```

### 6.2 Erwartete Laufzeit (Pipeline B)

| Step | Dauer (geschätzt) | Anmerkung |
|------|-------------------|-----------|
| Brand Research | 10-30 Min | Einmalig |
| Creative Brief | 5-10 Min | LLM-basiert |
| Creative Generation (5 Varianten) | 60-120 Min | Video am langsamsten |
| Scoring (5 Varianten) | 90-150 Min | TRIBE + Saliency + MiroFish |
| Iteration (1 Runde, 3 Varianten) | 90-120 Min | Gen + Scoring |
| Final Report | 5-10 Min | |
| **Gesamt** | **~4-7 Stunden** | Für 1 Kampagne mit 1 Iteration |

---

## 7. Datenmodell & Scoring-Schema

### 7.1 Campaign Object

```python
@dataclass
class Campaign:
    id: str
    company_name: str
    company_url: str
    brand_profile: BrandProfile        # Ergebnis aus Research
    target_audience: str
    campaign_goal: str
    creatives: List[Creative]
    pipeline_type: Literal['A', 'B']   # Analyse oder Generierung

@dataclass
class BrandProfile:
    description: str
    tone_of_voice: str
    visual_style: str
    key_messages: List[str]
    competitors: List[str]
    existing_ads: List[str]            # URLs oder Pfade
    social_sentiment: dict             # Allgemeines Sentiment

@dataclass
class Creative:
    id: str
    type: Literal['video', 'image', 'text', 'multimodal']
    source: Literal['existing', 'generated']
    file_path: str
    metadata: dict
    scores: CreativeScores

@dataclass
class CreativeScores:
    # TRIBE v2 Neuro-Scores
    neural_engagement: float           # 0-1, Gesamtaktivierung
    emotional_impact: float            # TPJ Aktivierung
    face_response: float               # FFA Aktivierung
    scene_response: float              # PPA Aktivierung
    motion_response: float             # V5 Aktivierung
    language_engagement: float         # Broca Aktivierung
    temporal_profile: List[float]      # Aktivierung über Zeit
    brain_heatmap_path: str            # Visualisierung
    
    # Saliency Scores
    product_attention: float           # 0-1
    brand_attention: float             # 0-1
    cta_attention: float               # 0-1
    first_fixation: str                # Wo schaut man zuerst hin?
    scanpath: List[dict]               # Sequenz der Blickbewegung
    saliency_map_path: str             # Visualisierung
    
    # MiroFish Social Scores
    positive_sentiment: float          # 0-1
    negative_sentiment: float          # 0-1
    virality_score: float              # 0-1
    controversy_risk: float            # 0-1
    key_reactions: List[str]           # Top Agent-Reaktionen
    
    # Brand Consistency (CLIP)
    brand_match_score: float           # 0-1, Cosine Similarity
    
    # Composite
    total_score: float                 # Gewichteter Gesamt-Score
```

---

## 8. Setup-Roadmap

### Phase 1: Foundation (Woche 1-2)

**Ziel:** TRIBE v2 lokal zum Laufen bringen, erste Brain-Response auf ein Video sehen.

```bash
# 1. TRIBE v2 klonen und Dependencies installieren
git clone https://github.com/facebookresearch/tribev2.git
cd tribev2
pip install -r requirements.txt

# 2. Model Weights von HuggingFace laden
# (HuggingFace CLI oder Python)
huggingface-cli download facebook/tribev2

# 3. Quick Test mit demo_utils.py
python -c "
from demo_utils import TribeModel
model = TribeModel.from_pretrained('facebook/tribev2')
# Test mit einem kurzen Video
result = model.predict_video('test_clip.mp4')
print(result.shape)  # Erwartung: (time_steps, 20484) Vertices
"

# 4. Visualisierung
# Nutze plotting/ Modul für Brain Heatmaps
```

**Risiken:**
- ROCm-Kompatibilität auf Strix Halo iGPU — Fallback: CPU-Inferenz
- V-JEPA2 Dependencies — Muss separat installiert werden
- Speicherbedarf der Feature-Extraktoren testen

**Deliverable:** Script `test_tribe.py` das ein Video nimmt und Brain-Heatmap ausgibt.

### Phase 2: Saliency (Woche 2-3)

**Ziel:** DeepGaze IIE + Video Saliency laufen, kombinierter Score mit TRIBE.

```bash
# DeepGaze IIE
pip install deepgaze-pytorch  # oder manuell von GitHub

# Video Saliency (ViNet-S)
git clone https://github.com/samyak0210/ViNet.git
# Weights herunterladen

# Test: Bild-Saliency
python -c "
import deepgaze_pytorch
model = deepgaze_pytorch.DeepGazeIIE(pretrained=True)
# ... Saliency Map generieren
"
```

**Deliverable:** Script `saliency_score.py` das Bild/Video nimmt und Attention-Heatmap + Scores ausgibt.

### Phase 3: MiroFish (Woche 3-4)

**Ziel:** MiroFish Offline lokal laufen, erste Social-Simulation einer Werbung.

```bash
# MiroFish Offline
git clone https://github.com/nikmcfly/MiroFish-Offline.git
cd MiroFish-Offline
cp .env.example .env

# Konfiguriere .env für lokalen Ollama/Lemonade
# OLLAMA_HOST=http://localhost:11434
# oder: Umkonfigurieren auf Lemonade SDK Port 8888

docker compose up -d

# Neo4j: http://localhost:7474
# MiroFish UI: http://localhost:3000
```

**Deliverable:** Erste Simulation mit einem Werbe-Seed-Dokument, Sentiment-Report.

### Phase 4: Pipeline Integration (Woche 4-6)

**Ziel:** Pipeline A vollständig lauffähig — bestehende Werbung End-to-End analysieren.

Baue einen zentralen Pipeline-Runner:

```python
# pipeline_runner.py
class NeuroAdPipeline:
    def __init__(self, config):
        self.model_manager = ModelManager()
        self.tribe = TribeScorer(self.model_manager)
        self.saliency = SaliencyScorer(self.model_manager)
        self.mirofish = MiroFishRunner(config.mirofish)
        self.research = BrandResearcher(config.research)
        
    async def run_pipeline_a(self, company: str):
        # Step 1: Research
        brand = await self.research.analyze(company)
        
        # Step 2: Collect Assets
        assets = await self.research.collect_ads(brand)
        
        # Step 3: Score (sequentiell mit Model-Swap)
        for creative in assets:
            # 3a. TRIBE
            self.model_manager.transition('idle', 'tribe')
            creative.scores.update(
                await self.tribe.score(creative)
            )
            
            # 3b. Saliency
            self.model_manager.transition('tribe', 'saliency')
            creative.scores.update(
                await self.saliency.score(creative)
            )
        
        # 3c. MiroFish (einmal für alle Top-Creatives)
        self.model_manager.transition('saliency', 'mirofish')
        social_scores = await self.mirofish.simulate(
            brand_context=brand,
            creatives=assets[:5]  # Top 5 nach Neuro-Score
        )
        
        # Step 4: Report
        return self.generate_report(brand, assets, social_scores)
```

**Deliverable:** Pipeline A läuft End-to-End für ein Testunternehmen.

### Phase 5: Creative Generation (Woche 6-8)

**Ziel:** Pipeline B — Video/Bild/Text-Generierung + Feedback-Loop.

- Flux.1/SDXL für Bilder integrieren
- CogVideoX/Wan2.1 für Videos integrieren
- Prompt-Templates basierend auf Brand-Profil erstellen
- Iteration-Loop: Score → Analyse → Re-Generate

**Deliverable:** Pipeline B läuft End-to-End, generiert und bewertet neue Werbung.

### Phase 6: Dashboard (Woche 8-10)

**Ziel:** Streamlit/Gradio Dashboard für den gesamten Prozess.

- Campaign Input (Unternehmen, Ziel, Zielgruppe)
- Pipeline-Auswahl (A oder B)
- Live-Status der einzelnen Pipeline-Schritte
- Ergebnis-Darstellung: Brain-Maps, Saliency-Maps, Scores, Social-Report
- Vergleichs-Ansicht: Multiple Creatives nebeneinander
- Export: PDF-Report

---

## 9. ROCm & Compute Strategy

### 9.1 Compute-Optionen auf Strix Halo

| Option | Pro | Contra |
|--------|-----|--------|
| ROCm (iGPU) | Schnellste Option wenn es läuft | Kompatibilität unsicher für V-JEPA2 |
| Vulkan (llama.cpp) | Stabil, gut getestet für LLMs | Nicht für alle PyTorch-Modelle |
| CPU (PyTorch) | Funktioniert immer | 3-10x langsamer |
| Hybrid | CPU für Features, GPU für LLM | Komplex, aber flexibel |

### 9.2 Empfohlene Strategie

1. **LLM-Inferenz (Research, MiroFish, Text-Gen):** Lemonade SDK / llama.cpp mit Vulkan — das läuft bereits stabil auf The Beast
2. **TRIBE v2 Feature-Extraktion:** Starte mit CPU-Inferenz, teste dann ROCm
3. **Saliency Models:** CPU reicht (DeepGaze IIE ist klein genug)
4. **Image/Video Generation:** Hier ist GPU am wertvollsten — teste ROCm/Vulkan zuerst für Flux/SDXL

### 9.3 Fallback: Cloud-Burst für Heavy Compute

Wenn TRIBE v2 Feature-Extraktion lokal zu langsam ist:
- **Option 1:** RunPod/Vast.ai für sporadische GPU-Sessions (A100 ~$1.50/h)
- **Option 2:** Google Colab Pro für Prototyping
- Das wäre nur für den V-JEPA2 Feature-Extraktion-Teil nötig, alles andere läuft lokal

---

## 10. Limitationen & Ehrliche Einschätzung

### Was TRIBE v2 kann und was nicht

**Kann:**
- Vorhersagen, welche Gehirnregionen auf Stimuli reagieren
- Regionale Aktivierung vergleichen (Video A vs Video B)
- Zero-Shot auf neue Personen generalisieren
- Population-Level Vorhersagen (Durchschnitt über viele Menschen)

**Kann nicht:**
- Individuelle Gedanken lesen
- Kaufentscheidungen direkt vorhersagen
- Kulturelle Unterschiede in der Wahrnehmung abbilden
- Ersetzen von echten fMRI-Studien für klinische Zwecke

### Was MiroFish kann und was nicht

**Kann:**
- Sentiment-Trends simulieren
- Emergente Gruppen-Dynamiken modellieren
- PR-Risiken identifizieren

**Kann nicht:**
- Exakte Viral-Zahlen vorhersagen
- Reale kulturelle Kontexte perfekt abbilden
- Garantieren, dass die Simulation der Realität entspricht
- Ersetzen von echten Marktforschungs-Panels

### Gesamtbewertung

NeuroAd ist ein **Research-Tool und Entscheidungshilfe**, kein Orakel. Die Stärke liegt im relativen Vergleich: "Creative A aktiviert das Gehirn stärker als Creative B in der emotionalen Verarbeitung" ist eine valide Aussage. "Creative A wird 50% mehr Conversions bringen" ist es nicht.

Der größte Wert entsteht durch die Kombination der drei Scoring-Dimensionen — ein Creative kann ein starkes Neuro-Signal haben, aber visuell am Produkt vorbeischauen (Saliency) oder sozial kontrovers sein (MiroFish). Erst die Kombination gibt ein vollständiges Bild.

---

## 11. Projektstruktur

```
neuroadpipeline/
├── README.md
├── docker-compose.yml               # MiroFish + Neo4j
├── requirements.txt
├── config/
│   ├── pipeline_config.yaml          # Haupt-Konfiguration
│   ├── model_registry.yaml           # Alle Modelle + RAM-Schätzungen
│   └── scoring_weights.yaml          # Gewichtung der Scores
├── src/
│   ├── orchestrator/
│   │   ├── pipeline_runner.py        # Haupt-Pipeline
│   │   ├── model_manager.py          # Dynamisches Model-Loading
│   │   └── phase_controller.py       # Phasen-Steuerung
│   ├── research/
│   │   ├── brand_researcher.py       # Web Crawling + Analyse
│   │   ├── ad_collector.py           # Ad-Asset-Sammlung
│   │   └── competitor_analyzer.py    # Wettbewerbs-Analyse
│   ├── scoring/
│   │   ├── tribe_scorer.py           # TRIBE v2 Wrapper
│   │   ├── saliency_scorer.py        # DeepGaze + ViNet Wrapper
│   │   ├── mirofish_runner.py        # MiroFish API Client
│   │   ├── clip_scorer.py            # Brand Consistency
│   │   └── composite_scorer.py       # Gewichtete Kombination
│   ├── generation/
│   │   ├── brief_generator.py        # Creative Brief aus Research
│   │   ├── video_generator.py        # CogVideoX / Wan2.1
│   │   ├── image_generator.py        # Flux / SDXL
│   │   ├── text_generator.py         # Ad Copy
│   │   └── iteration_engine.py       # Feedback-Loop
│   ├── reporting/
│   │   ├── report_generator.py       # Finale Reports
│   │   ├── brain_visualizer.py       # PyVista Brain Maps
│   │   └── saliency_visualizer.py    # Attention Heatmaps
│   └── utils/
│       ├── video_utils.py            # Video Processing
│       ├── audio_utils.py            # Audio Extraktion
│       └── data_models.py            # Pydantic Models
├── dashboard/
│   └── app.py                        # Streamlit/Gradio UI
├── tests/
│   ├── test_tribe.py
│   ├── test_saliency.py
│   └── test_mirofish.py
└── scripts/
    ├── setup_tribe.sh                # TRIBE v2 Installation
    ├── setup_mirofish.sh             # MiroFish Setup
    └── test_hardware.sh              # RAM/GPU Capability Check
```

---

## 12. Quick-Start Checkliste

- [ ] TRIBE v2 Repo klonen + Weights herunterladen
- [ ] Python-Environment einrichten (Python 3.11+, PyTorch)
- [ ] TRIBE v2 Demo mit einem Test-Video laufen lassen
- [ ] DeepGaze IIE installieren + Test-Bild analysieren
- [ ] MiroFish Offline via Docker aufsetzen
- [ ] Neo4j + Ollama verifizieren
- [ ] Erste MiroFish Simulation starten
- [ ] Model Manager bauen (RAM-Tracking + Swap-Logik)
- [ ] Pipeline A Runner implementieren
- [ ] Scoring-Kombination kalibrieren
- [ ] Test-Run: Ein Unternehmen End-to-End durch Pipeline A
- [ ] Pipeline B: Creative Generation Module hinzufügen
- [ ] Iteration-Engine bauen
- [ ] Dashboard aufsetzen

---

## 13. Optionale Erweiterungen

### Phase 7: KPI-Kalibrierung — Von Scores zu echten Performance-Vorhersagen

**Ziel:** Ein Regressionsmodell trainieren, das NeuroAd-Scores auf echte Kampagnen-KPIs mappt.

**Konzept:**
Wenn du historische Kampagnen-Daten hast (Creatives + zugehörige KPIs), kannst du ein Kalibrierungsmodell bauen, das lernt: "Wenn TRIBE-Score = X und Saliency = Y und MiroFish-Sentiment = Z, dann war historisch die CTR/ROAS/Conversion Rate im Bereich W."

**Voraussetzungen:**
- Minimum 200-500 Creatives mit zugehörigen KPIs (gleiche Branche/Plattform)
- Je homogener die Bedingungen (gleiche Plattform, ähnliches Budget, ähnliche Zielgruppe), desto weniger Daten brauchst du
- Idealerweise A/B-Test-Paare, die unter gleichen Bedingungen liefen

**Architektur:**

```
┌────────────────────────────────────────────────────┐
│           KALIBRIERUNGS-PIPELINE                   │
│                                                    │
│  ┌──────────────┐    ┌──────────────────────────┐  │
│  │ Historische   │    │  NeuroAd Scoring         │  │
│  │ Creatives     │───▶│  (Batch-Mode)            │  │
│  │ + KPI CSV     │    │  TRIBE + Saliency +      │  │
│  └──────────────┘    │  MiroFish + CLIP          │  │
│                      └────────────┬─────────────┘  │
│                                   │                │
│                                   ▼                │
│                      ┌──────────────────────────┐  │
│                      │  Feature Matrix           │  │
│                      │                           │  │
│                      │  neural_engagement: 0.72  │  │
│                      │  emotional_impact:  0.85  │  │
│                      │  product_attention: 0.63  │  │
│                      │  brand_attention:   0.71  │  │
│                      │  virality_score:    0.58  │  │
│                      │  ...                      │  │
│                      │  + Confounders:            │  │
│                      │  platform: "instagram"    │  │
│                      │  budget_range: "mid"      │  │
│                      │  audience_size: 500000    │  │
│                      │  season: "Q4"             │  │
│                      └────────────┬─────────────┘  │
│                                   │                │
│                                   ▼                │
│                      ┌──────────────────────────┐  │
│                      │  XGBoost / LightGBM      │  │
│                      │                           │  │
│                      │  Target: CTR, CPA, ROAS,  │  │
│                      │  View-Through-Rate,        │  │
│                      │  Engagement Rate           │  │
│                      │                           │  │
│                      │  Output: Prediction +      │  │
│                      │  Confidence Interval       │  │
│                      └──────────────────────────┘  │
└────────────────────────────────────────────────────┘
```

**Wichtige Design-Entscheidungen:**

1. **Confounders als Features einbeziehen:** Plattform, Budget-Range, Audience-Größe, Saison, Branche, Wochentag — ohne diese Variablen wird das Modell stark rauschen

2. **Relative statt absolute Vorhersage bevorzugen:** Statt "CTR wird 2.3%" besser "Creative A wird voraussichtlich 35% bessere CTR haben als Creative B" — das ist robuster gegen Confounders

3. **Confidence Intervals ausgeben:** Nie einen Punkt-Schätzwert ohne Unsicherheits-Range liefern

4. **Regelmäßig re-kalibrieren:** Plattform-Algorithmen ändern sich, Nutzerverhalten shiftet — das Modell braucht frische Daten

**Implementierung:**

```python
# calibration_model.py
import xgboost as xgb
from sklearn.model_selection import cross_val_score
import numpy as np

class KPICalibrator:
    def __init__(self):
        self.models = {}  # Ein Modell pro KPI
        self.is_calibrated = False
    
    def train(self, features_df, kpi_df, confounders_df):
        """
        features_df: NeuroAd Scores (TRIBE, Saliency, MiroFish, CLIP)
        kpi_df: Echte KPIs (CTR, CPA, ROAS, etc.)
        confounders_df: Kontrollvariablen (Platform, Budget, etc.)
        """
        X = pd.concat([features_df, confounders_df], axis=1)
        
        for kpi_name in kpi_df.columns:
            y = kpi_df[kpi_name]
            model = xgb.XGBRegressor(
                n_estimators=200,
                max_depth=4,        # Flach halten, wenig Daten
                learning_rate=0.05,
                reg_alpha=1.0,      # L1 Regularisierung
                reg_lambda=1.0,     # L2 Regularisierung
            )
            
            # Cross-Validation Score
            cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')
            print(f"{kpi_name}: R² = {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
            
            # Warnung bei schlechter Fit
            if cv_scores.mean() < 0.3:
                print(f"⚠️  Warnung: {kpi_name} hat schwache Korrelation "
                      f"mit Neuro-Scores. Mehr Daten oder Features nötig.")
            
            model.fit(X, y)
            self.models[kpi_name] = model
        
        self.is_calibrated = True
    
    def predict(self, neuro_scores, confounders):
        """Gibt KPI-Prognose mit Confidence Interval zurück"""
        X = pd.concat([neuro_scores, confounders], axis=1)
        predictions = {}
        
        for kpi_name, model in self.models.items():
            pred = model.predict(X)
            # Bootstrapped Confidence Interval
            boot_preds = []
            for _ in range(100):
                idx = np.random.choice(len(X), len(X), replace=True)
                boot_model = xgb.XGBRegressor(**model.get_params())
                boot_model.fit(X.iloc[idx], pred[idx])  # Simplified
                boot_preds.append(boot_model.predict(X))
            
            ci_low = np.percentile(boot_preds, 5, axis=0)
            ci_high = np.percentile(boot_preds, 95, axis=0)
            
            predictions[kpi_name] = {
                'prediction': pred,
                'ci_90_low': ci_low,
                'ci_90_high': ci_high
            }
        
        return predictions
```

**Datenquellen für historische Kampagnen:**
- Eigene Kampagnen-Daten (idealerweise über Meta/Google Ads API exportiert)
- Agentur-Partner, die aggregierte anonymisierte Daten teilen
- Öffentliche Case Studies (weniger strukturiert, aber besser als nichts)
- Meta Ad Library für Creative-Assets + geschätzte Impressions

**Ehrliche Einschätzung:**
- Mit 200+ homogenen Creatives + KPIs erreichst du wahrscheinlich ein R² von 0.3-0.5 — genug für nützliche relative Rankings, nicht für exakte Punkt-Vorhersagen
- Mit 1000+ Creatives und guter Confounder-Kontrolle könnte R² auf 0.5-0.7 steigen
- Die Feature Importance aus XGBoost zeigt dir, welche Neuro-Scores am prädiktivsten sind — das ist allein schon wertvoll

---

### Phase 8: Audio/Musik-Generierung — Sonic Branding

**Ziel:** Audio-Tracks für Video-Ads generieren und ebenfalls gegen TRIBE v2 testen.

**Warum relevant:** TRIBE v2 hat explizit einen Audio-Stream (Wav2Vec-BERT). Du kannst also nicht nur testen, wie das Gehirn auf das Video reagiert, sondern auch separat auf den Audio-Track — und dann auf die Kombination. Das eröffnet eine ganz neue Optimierungs-Dimension: "Welcher Soundtrack macht das Video neurologisch wirksamer?"

**Open-Source Tools:**

| Tool | Was es tut | Größe | Lizenz |
|------|-----------|-------|--------|
| DiffRhythm | Full-Song-Generierung via Diffusion | ~2-4 GB | MIT |
| Qwen3-TTS (0.6B-1.7B) | Text-to-Speech, Voiceover | ~1-3 GB | Apache 2.0 |
| Bark (Suno) | TTS mit Emotionen, Musik, Sound-Effekte | ~5 GB | MIT |
| HunyuanVideo-Foley | Foley Sound-Effekte synchron zum Video | ~4-8 GB | Open Source |
| MusicGen (Meta) | Text-to-Music, verschiedene Genres | ~3-10 GB | CC BY-NC |

**Pipeline-Integration:**
1. Video-Creative wird generiert (CogVideoX/Wan2.1)
2. LLM beschreibt die gewünschte Stimmung/Audio-Direction
3. Audio-Track wird generiert (DiffRhythm/MusicGen)
4. Video + Audio werden kombiniert
5. TRIBE v2 scored: Video-only vs. Audio-only vs. Kombination
6. Vergleich: Welcher Soundtrack maximiert die neurale Response?

**Besonders spannend:** Du könntest mehrere Audio-Varianten für dasselbe Video testen und sehen, wie sich die Gehirnaktivierung ändert — quasi ein neurales A/B-Testing für Soundtracks.

---

### Phase 9: Arousal-Valence-Mapping — Emotionale Landkarte

**Ziel:** Zusätzlich zu den TRIBE v2 Region-Scores eine explizite Einordnung auf der Arousal-Valence-Skala.

**Konzept:** Das Circumplex-Modell der Emotionen hat zwei Achsen: Arousal (Erregung, von ruhig bis aufgeregt) und Valence (Wertigkeit, von negativ bis positiv). Ein Creative, das hohe Arousal + positive Valence hat, erzeugt Begeisterung. Hohe Arousal + negative Valence = Angst/Schock. Niedrige Arousal + positive Valence = Entspannung.

```
        Hohe Arousal
            │
   Angst    │    Begeisterung
   Stress   │    Freude
            │
 Negative ──┼── Positive Valence
            │
   Trauer   │    Entspannung
   Langeweile│   Zufriedenheit
            │
        Niedrige Arousal
```

**Implementierung:**
- TRIBE v2 liefert regionale Aktivierung — TPJ (emotional), Amygdala-nahe Regionen, etc.
- Zusätzlich: HSEmotion auf Gesichter im Creative anwenden (Facial Emotion Recognition)
- Zusätzlich: Text-Sentiment-Analyse auf Ad Copy (Arousal/Valence Lexikon)
- Fusion: Kombinierter Arousal-Valence-Score pro Creative
- Visualisierung: Jedes Creative als Punkt auf der 2D Arousal-Valence Map

**Warum nützlich:** Du kannst gezielt steuern, welche Emotion die Werbung auslösen soll und validieren, ob das Creative auch dort landet. "Wir wollen Begeisterung" → Creative muss in den oberen rechten Quadranten.

---

### Phase 10: Multivariate Creative-Zerlegung — Was genau macht den Unterschied?

**Ziel:** Verstehen, WELCHES Element eines Creatives für den Score verantwortlich ist.

**Konzept:** Wenn Creative A besser scored als Creative B, will man wissen: Liegt es am Farbschema? Am Gesicht? Am Text-Overlay? Am Tempo? Das geht über ablative Analyse:

**Methode:**
1. Nimm ein Creative und erzeuge systematische Varianten:
   - Gleicher Inhalt, anderes Farbschema
   - Gleiche Szene, anderer Text-Overlay
   - Gleicher Text, andere Schriftart/Position
   - Gleiche Szene, mit vs. ohne Gesichter
   - Gleicher Clip, verschiedene Schnittrhythmen
2. Score jede Variante durch die Pipeline
3. Vergleiche: ΔTRIBE, ΔSaliency, ΔMiroFish pro Veränderung
4. Feature Attribution Report: "Der größte Score-Treiber ist das Gesicht im Thumbnail (+23% Neural Engagement)"

**Tools:**
- Bild-Manipulation: PIL/Pillow für systematische Varianten (Farbe, Text, Crop)
- SDXL InPaint: Teile eines Bildes austauschen
- FFmpeg: Video-Schnitt-Varianten automatisieren

**Warum wertvoll:** Das ist der Schritt von "dieses Creative ist besser" zu "dieses Creative ist besser WEIL..." — und das ist die Information, die ein Marketing-Team wirklich braucht.

---

### Phase 11: Zielgruppen-Differenzierung — Personas im Gehirn

**Ziel:** Testen, ob verschiedene Zielgruppen (simuliert) unterschiedlich auf Creatives reagieren.

**Konzept:** TRIBE v2 kann Zero-Shot auf neue Subjekte generalisieren. Wenn du es mit wenig Finetuning-Daten auf verschiedene demografische Gruppen anpasst, könntest du simulieren: "Wie reagiert ein 25-jähriger Tech-Affiner vs. ein 55-jähriger Traditionalist?"

**Realistischer Ansatz:**
- TRIBE v2 selbst ist momentan nicht nach Demografie differenziert (trained auf Population-Average)
- **Aber:** MiroFish kann Agenten-Demografien konfigurieren — verschiedene Altersgruppen, Interessen, Kulturen
- Kombination: TRIBE v2 für neurale Baseline + MiroFish-Segmente für soziale Differenzierung
- Langfristig: Wenn TRIBE v2 weiterentwickelt wird und Subject-spezifisches Finetuning besser wird, kann dieser Layer wachsen

**MiroFish-Konfiguration für Personas:**
```yaml
# Persona-Templates für MiroFish Agenten
personas:
  gen_z_urban:
    age_range: [18, 28]
    interests: ["tech", "sustainability", "social_media"]
    skepticism: high
    platform_native: true
    
  millennial_parent:
    age_range: [30, 42]
    interests: ["family", "health", "convenience"]
    skepticism: medium
    price_sensitive: true
    
  boomer_traditional:
    age_range: [55, 70]
    interests: ["quality", "trust", "brand_loyalty"]
    skepticism: low
    ad_tolerance: higher
```

---

### Phase 12: Competitive Intelligence Dashboard — Wettbewerbs-Radar

**Ziel:** Automatisiertes, regelmäßiges Scoring der Wettbewerber-Werbung.

**Konzept:**
- Cronjob/Scheduler crawlt wöchentlich die Meta Ad Library für definierte Wettbewerber
- Neue Ads werden automatisch durch Pipeline A geschickt
- Dashboard zeigt: "Wettbewerber X hat diese Woche 3 neue Ads gelauncht. Neuro-Score: 0.72, 0.65, 0.81. Trend: steigend."
- Vergleich mit eigenen Scores: "Unser bestes Creative scored 0.78 — Wettbewerber hat uns mit 0.81 überholt."
- Alert-System: "Wettbewerber hat ein Creative mit ungewöhnlich hohem Emotional-Impact-Score gestartet."

**Technisch:**
- Meta Ad Library API für Asset-Collection
- Scheduling: Simple Cron oder Airflow
- Persistent Storage: SQLite/PostgreSQL für historische Scores
- Trend-Visualisierung im Streamlit Dashboard

---

### Erweiterungs-Priorisierung

| Phase | Schwierigkeit | Impact | Abhängigkeiten | Empfehlung |
|-------|--------------|--------|----------------|------------|
| 7: KPI-Kalibrierung | Mittel (Modell simpel, Daten schwer) | Sehr hoch | Historische KPI-Daten benötigt | Starten sobald Daten verfügbar |
| 8: Audio-Generierung | Mittel | Hoch | Pipeline B muss laufen | Phase 5+ |
| 9: Arousal-Valence | Niedrig | Mittel | TRIBE v2 + HSEmotion | Phase 2+ |
| 10: Creative-Zerlegung | Mittel | Sehr hoch | Pipeline A muss laufen | Phase 4+ |
| 11: Zielgruppen | Hoch (Finetuning) | Hoch | MiroFish + Persona-Design | Phase 3+ |
| 12: Competitive Intel | Niedrig-Mittel | Hoch | Pipeline A muss laufen | Phase 4+ |

---

*Dieses Dokument ist ein lebendiges Spec — es wird sich mit den ersten Implementierungserfahrungen weiterentwickeln. Besonders die RAM-Schätzungen und Laufzeiten sind Annäherungen, die durch reales Testing auf The Beast kalibriert werden müssen.*
