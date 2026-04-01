"""
Score file loader for NeuroAd Dashboard.
Reads score JSON files from campaigns and loads them into the database.
"""

import json
import glob
import os
from pathlib import Path
from typing import Optional

from .db import upsert_asset, get_all_campaigns

PROJECT_ROOT = Path.home() / "neuro_pipeline_project"
CAMPAIGNS_DIR = PROJECT_ROOT / "campaigns"


def get_campaign_names() -> list[str]:
    """
    Scan campaigns/ directory for subdirectories that have a scores/ subfolder.
    
    Returns:
        List of campaign names
    """
    if not CAMPAIGNS_DIR.exists():
        return []
    
    campaigns = []
    for item in CAMPAIGNS_DIR.iterdir():
        if item.is_dir():
            scores_dir = item / "scores"
            if scores_dir.exists() and scores_dir.is_dir():
                campaigns.append(item.name)
    
    return sorted(campaigns)


def load_single_score_file(filepath: Path) -> Optional[dict]:
    """
    Load a single score JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Dictionary with scores or None if file cannot be read
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def extract_asset_name_from_filename(filename: str) -> str:
    """
    Extract asset name from filename prefix.
    e.g., "apple_iphone17_scratch_tribe_scores.json" -> "apple_iphone17_scratch"
    """
    # Remove extension
    name = Path(filename).stem
    # Remove score type suffix
    suffixes = ["_tribe_scores", "_saliency_scores", "_clip_scores", "_emotion_scores"]
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break
    return name


def load_pipeline_results(campaign: str) -> list[dict]:
    """
    Load pipeline_results_final.json or pipeline_results_interim.json.
    
    Args:
        campaign: Campaign name
        
    Returns:
        List of asset data dictionaries
    """
    scores_dir = CAMPAIGNS_DIR / campaign / "scores"
    
    # Try final first, then interim
    for filename in ["pipeline_results_final.json", "pipeline_results_interim.json"]:
        filepath = scores_dir / filename
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                continue
    
    return []


def load_campaign(campaign: str) -> int:
    """
    Load all scores for a campaign from JSON files into the database.
    
    Args:
        campaign: Campaign name
        
    Returns:
        Number of assets loaded
    """
    scores_dir = CAMPAIGNS_DIR / campaign / "scores"
    
    if not scores_dir.exists():
        return 0
    
    assets_loaded = 0
    
    # First, try to load from pipeline_results JSON
    pipeline_results = load_pipeline_results(campaign)
    
    if pipeline_results:
        for asset_data in pipeline_results:
            data = extract_scores_from_pipeline_result(campaign, asset_data)
            upsert_asset(campaign, data)
            assets_loaded += 1
    else:
        # Fall back to loading individual score files
        assets_loaded = load_from_individual_files(campaign)
    
    return assets_loaded


def extract_scores_from_pipeline_result(campaign: str, asset_data: dict) -> dict:
    """
    Extract all score fields from a pipeline_results entry.
    
    Args:
        campaign: Campaign name
        asset_data: Asset data from pipeline_results JSON
        
    Returns:
        Dictionary with all score fields
    """
    result = {
        "asset_name": asset_data.get("asset_name", ""),
        "asset_path": asset_data.get("asset_path", ""),
    }
    
    # TRIBE scores
    tribe = asset_data.get("tribe", {})
    result.update({
        "neural_engagement": tribe.get("neural_engagement"),
        "emotional_impact": tribe.get("emotional_impact"),
        "face_response": tribe.get("face_response"),
        "scene_response": tribe.get("scene_response"),
        "motion_response": tribe.get("motion_response"),
        "language_engagement": tribe.get("language_engagement"),
        "temporal_peak": tribe.get("temporal_peak"),
        "n_segments": tribe.get("n_segments"),
        "tribe_error": tribe.get("error"),
        "brain_map_path": tribe.get("brain_map_path"),
    })
    
    # Saliency scores
    saliency = asset_data.get("saliency", {})
    result.update({
        "center_bias": saliency.get("center_bias"),
        "saliency_score": saliency.get("saliency_score"),
    })
    
    # CLIP scores
    clip = asset_data.get("clip", {})
    result.update({
        "brand_match_score": clip.get("brand_match_score"),
        "top_label": clip.get("top_label"),
    })
    
    # HSEmotion scores
    emotion = asset_data.get("emotion", {})
    result.update({
        "dominant_emotion": emotion.get("dominant_emotion"),
        "emotional_valence": emotion.get("emotional_valence"),
    })
    
    # Composite scores
    composite = asset_data.get("composite", {})
    result.update({
        "total_score": composite.get("total_score"),
        "grade": composite.get("grade"),
    })
    
    # Check for tribe_preds file
    brain_map_path = tribe.get("brain_map_path", "")
    if brain_map_path:
        npy_path = Path(PROJECT_ROOT) / brain_map_path
        result["has_tribe_preds"] = npy_path.exists()
    else:
        result["has_tribe_preds"] = False
    
    return result


def load_from_individual_files(campaign: str) -> int:
    """
    Load scores from individual JSON files when pipeline_results is not available.
    
    Args:
        campaign: Campaign name
        
    Returns:
        Number of assets loaded
    """
    scores_dir = CAMPAIGNS_DIR / campaign / "scores"
    assets_loaded = 0
    
    # Find all score files
    tribe_files = list(scores_dir.glob("*_tribe_scores.json"))
    saliency_files = list(scores_dir.glob("*_saliency_scores.json"))
    clip_files = list(scores_dir.glob("*_clip_scores.json"))
    emotion_files = list(scores_dir.glob("*_emotion_scores.json"))
    
    # Collect all unique asset names
    asset_names = set()
    
    for f in tribe_files:
        asset_names.add(extract_asset_name_from_filename(f.name))
    for f in saliency_files:
        asset_names.add(extract_asset_name_from_filename(f.name))
    for f in clip_files:
        asset_names.add(extract_asset_name_from_filename(f.name))
    for f in emotion_files:
        asset_names.add(extract_asset_name_from_filename(f.name))
    
    # Load each asset
    for asset_name in asset_names:
        data = {
            "asset_name": asset_name,
            "asset_path": f"campaigns/{campaign}/assets/{asset_name}.mp4",
            "has_tribe_preds": False,
        }
        
        # Load tribe scores
        tribe_file = scores_dir / f"{asset_name}_tribe_scores.json"
        if tribe_file.exists():
            tribe_data = load_single_score_file(tribe_file)
            if tribe_data:
                data.update({
                    "neural_engagement": tribe_data.get("neural_engagement"),
                    "emotional_impact": tribe_data.get("emotional_impact"),
                    "face_response": tribe_data.get("face_response"),
                    "scene_response": tribe_data.get("scene_response"),
                    "motion_response": tribe_data.get("motion_response"),
                    "language_engagement": tribe_data.get("language_engagement"),
                    "temporal_peak": tribe_data.get("temporal_peak"),
                    "n_segments": tribe_data.get("n_segments"),
                    "tribe_error": tribe_data.get("error"),
                    "brain_map_path": tribe_data.get("brain_map_path"),
                })
                # Check for tribe_preds file
                brain_map_path = tribe_data.get("brain_map_path", "")
                if brain_map_path:
                    npy_path = Path(PROJECT_ROOT) / brain_map_path
                    if npy_path.exists():
                        data["has_tribe_preds"] = True
        
        # Load saliency scores
        saliency_file = scores_dir / f"{asset_name}_saliency_scores.json"
        if saliency_file.exists():
            saliency_data = load_single_score_file(saliency_file)
            if saliency_data:
                data.update({
                    "center_bias": saliency_data.get("center_bias"),
                    "saliency_score": saliency_data.get("saliency_score"),
                })
        
        # Load clip scores
        clip_file = scores_dir / f"{asset_name}_clip_scores.json"
        if clip_file.exists():
            clip_data = load_single_score_file(clip_file)
            if clip_data:
                data.update({
                    "brand_match_score": clip_data.get("brand_match_score"),
                    "top_label": clip_data.get("top_label"),
                })
        
        # Load emotion scores
        emotion_file = scores_dir / f"{asset_name}_emotion_scores.json"
        if emotion_file.exists():
            emotion_data = load_single_score_file(emotion_file)
            if emotion_data:
                data.update({
                    "dominant_emotion": emotion_data.get("dominant_emotion"),
                    "emotional_valence": emotion_data.get("emotional_valence"),
                })
        
        # Set defaults for composite if not available
        if "total_score" not in data:
            data["total_score"] = None
        if "grade" not in data:
            data["grade"] = None
        
        upsert_asset(campaign, data)
        assets_loaded += 1
    
    return assets_loaded


def refresh_campaign(campaign: str) -> int:
    """
    Delete existing scores for a campaign and reload them.
    
    Args:
        campaign: Campaign name
        
    Returns:
        Number of assets loaded
    """
    from .db import delete_campaign
    
    delete_campaign(campaign)
    return load_campaign(campaign)
