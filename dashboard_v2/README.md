# NeuroAd Pipeline Dashboard v2

Next.js 16 / React 19 / TypeScript Dashboard für das NeuroAd Pipeline Projekt.

## Voraussetzungen

Das Dashboard benötigt das FastAPI Backend, das auf Port 8080 laufen muss.

### FastAPI Backend starten
```bash
bash ~/neuro_pipeline_project/start_dashboard.sh
```

Dies startet:
- **FastAPI Backend** auf Port 8080
- **Next.js Dashboard** auf Port 3000

## Lokales Setup

```bash
cd ~/neuro_pipeline_project/dashboard_v2

# Abhängigkeiten installieren (einmalig)
npm install

# Development Server starten
npm run dev
```

Das Dashboard ist dann unter [http://localhost:3000](http://localhost:3000) erreichbar.

## Umgebungsvariablen

Keine speziellen Umgebungsvariablen erforderlich. Das Dashboard holt seine Daten vom FastAPI Backend auf `http://localhost:8080`.

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **UI Library**: React 19
- **Typing**: TypeScript
- **Styling**: Tailwind CSS v4
- **Components**: shadcn/ui
- **Charts**: Recharts
- **Graphs**: D3 v7, Three.js

## Verfügbare Seiten

| Seite | Beschreibung |
|-------|-------------|
| `/` | Overview — Creative Performance Table, Modul-Cards |
| `/brand-intelligence` | Brand Profil, STORM Report, Märkte |
| `/tribe` | 3D Brain, 6 Metrik-Balken, AI Analyse |
| `/mirofish` | Animiertes Agent-Netzwerk, Sentiment Gauge |
| `/clip` | Radar Chart, Label Scores |
| `/vinet` | Heatmap, Product/Brand/CTA Attention |
| `/report` | Creative Ranking, Executive Summary |

## Design System

- **Farben**: Weiß/Schwarz, medical-precision aesthetic
- **Schriftarten**: Inter (Body), JetBrains Mono (Score Values)
- **Aesthetic**: Linear.app / Vercel inspiriert
