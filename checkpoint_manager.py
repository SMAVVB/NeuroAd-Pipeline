#!/usr/bin/env python3
"""
Checkpoint Manager für die Neuro-Pipeline.

Speichert und lädt den Status der Pipeline nach jeder Phase:
- Phase 0: Makro-Fundament (baseline + brand_profile)
- Phase 1: Suchbaum (publisher URLs + metadata)
- Phase 2: Social Scrapes (social data)

Definition of Done:
Ein Abbruch während Phase 2 führt beim Neustart dazu, dass Phase 0 und 1
sofort aus dem Cache geladen werden.
"""

import os
import json
from pathlib import Path
from datetime import datetime


# --- KONSTANTEN ---
CHECKPOINT_DIR_NAME = "pipeline_checkpoints"


# --- HILFSFUNKTIONEN ---

def get_checkpoint_dir(raw_data_dir: str, brand: str) -> Path:
    """Erstellt den Checkpoint-Verzeichnis-Pfad für eine Marke."""
    # Suche das neueste raw_data Verzeichnis für diese Marke
    brand_pattern = brand.replace(" ", "_")
    raw_path = Path(raw_data_dir)

    # Finde das neueste Verzeichnis, das den Brand-Namen enthält
    brand_dirs = [
        d for d in raw_path.iterdir()
        if d.is_dir() and brand_pattern in d.name
    ]

    if not brand_dirs:
        # Fallback: nutze den aktuellen timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return raw_path / f"{brand_pattern}_{timestamp}" / CHECKPOINT_DIR_NAME

    latest_dir = max(brand_dirs, key=os.path.getmtime)
    checkpoint_dir = latest_dir / CHECKPOINT_DIR_NAME

    # Erstelle das Verzeichnis, falls es nicht existiert
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    return checkpoint_dir


def save_checkpoint(checkpoint_dir: Path, phase: int, data: dict) -> bool:
    """
    Speichert einen Checkpoint als JSON-Datei.

    Args:
        checkpoint_dir: Verzeichnis für Checkpoints
        phase: Phasennummer (0, 1, oder 2)
        data: Zu speichernde Daten

    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"checkpoint_phase_{phase}_{timestamp}.json"
        filepath = checkpoint_dir / filename

        # Füge Metadaten hinzu
        payload = {
            "phase": phase,
            "timestamp": timestamp,
            "data": data
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        print(f"   ✅ Checkpoint Phase {phase} gespeichert: {filename}")
        return True

    except Exception as e:
        print(f"   ❌ Checkpoint Phase {phase} FEHLGESCHLAGEN: {e}")
        return False


def load_checkpoint(checkpoint_dir: Path, phase: int) -> dict | None:
    """
    Lädt den neuesten Checkpoint für eine bestimmte Phase.

    Args:
        checkpoint_dir: Verzeichnis für Checkpoints
        phase: Phasennummer (0, 1, oder 2)

    Returns:
        Checkpoint-Daten als dict oder None wenn nicht gefunden
    """
    try:
        checkpoint_path = Path(checkpoint_dir)

        if not checkpoint_path.exists():
            return None

        # Finde alle Checkpoint-Dateien für diese Phase
        phase_files = list(checkpoint_path.glob(f"checkpoint_phase_{phase}_*.json"))

        if not phase_files:
            return None

        # Sortiere nach Dateiname (timestamp) und nimm das neueste
        latest_file = max(phase_files, key=lambda f: f.name)

        with open(latest_file, "r", encoding="utf-8") as f:
            payload = json.load(f)

        print(f"   📥 Checkpoint Phase {phase} geladen: {latest_file.name}")
        return payload

    except Exception as e:
        print(f"   ⚠️ Fehler beim Laden von Checkpoint Phase {phase}: {e}")
        return None


def checkpoint_exists(checkpoint_dir: Path, phase: int) -> bool:
    """Prüft, ob ein Checkpoint für eine bestimmte Phase existiert."""
    return load_checkpoint(checkpoint_dir, phase) is not None


def get_completed_phases(checkpoint_dir: Path) -> list[int]:
    """Gibt eine Liste aller abgeschlossenen Phasen zurück."""
    completed = []
    for phase in [0, 1, 2]:
        if checkpoint_exists(checkpoint_dir, phase):
            completed.append(phase)
    return completed


# --- DATENSTRUKTUREN FÜR CHECKPOINTS ---

def create_phase0_checkpoint(baseline: str, brand_profile: dict) -> dict:
    """Erstellt einen Checkpoint für Phase 0 (Makro-Fundament)."""
    return {
        "baseline": baseline,
        "brand_profile": brand_profile
    }


def create_phase1_checkpoint(urls: list, url_meta: dict) -> dict:
    """Erstellt einen Checkpoint für Phase 1 (Suchbaum)."""
    return {
        "urls": urls,
        "url_meta": url_meta
    }


def create_phase2_checkpoint(social_data: dict, science_result: dict) -> dict:
    """Erstellt einen Checkpoint für Phase 2 (Social Scrapes)."""
    return {
        "social_data": social_data,
        "science_result": science_result
    }


# --- WIEDERHERSTELLUNGS-FUNKTIONEN ---

def restore_phase0(checkpoint_data: dict) -> tuple[str, dict]:
    """Stellt Phase 0 Daten wieder her."""
    baseline = checkpoint_data.get("baseline", "")
    brand_profile = checkpoint_data.get("brand_profile", {})
    return baseline, brand_profile


def restore_phase1(checkpoint_data: dict) -> tuple[list, dict]:
    """Stellt Phase 1 Daten wieder her."""
    urls = checkpoint_data.get("urls", [])
    url_meta = checkpoint_data.get("url_meta", {})
    return urls, url_meta


def restore_phase2(checkpoint_data: dict) -> tuple[dict, dict]:
    """Stellt Phase 2 Daten wieder her."""
    social_data = checkpoint_data.get("social_data", {})
    science_result = checkpoint_data.get("science_result", {})
    return social_data, science_result
