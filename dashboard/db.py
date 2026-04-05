"""
SQLite database layer for NeuroAd Dashboard.
Handles all database operations for campaign scores.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

DB_PATH = Path.home() / "neuro_pipeline_project" / "dashboard" / "neuro_ad.db"


def init_db() -> None:
    """Initialize the database with the scores table."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign TEXT,
            asset_name TEXT,
            asset_path TEXT,
            -- TRIBE scores
            neural_engagement REAL,
            emotional_impact REAL,
            face_response REAL,
            scene_response REAL,
            motion_response REAL,
            language_engagement REAL,
            temporal_peak REAL,
            n_segments INTEGER,
            tribe_error TEXT,
            brain_map_path TEXT,
            -- Saliency
            center_bias REAL,
            saliency_score REAL,
            -- CLIP
            brand_match_score REAL,
            top_label TEXT,
            -- HSEmotion
            dominant_emotion TEXT,
            emotional_valence REAL,
            -- Composite
            total_score REAL,
            grade TEXT,
            -- Meta
            has_tribe_preds INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(campaign, asset_name)
        )
    """)
    
    conn.commit()
    conn.close()


def upsert_asset(campaign: str, data: dict) -> None:
    """
    Insert or update a score record for an asset.
    
    Args:
        campaign: Campaign name
        data: Dictionary with all score fields
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if record exists
    cursor.execute(
        "SELECT id FROM scores WHERE campaign = ? AND asset_name = ?",
        (campaign, data.get("asset_name"))
    )
    existing = cursor.fetchone()
    
    # Prepare columns and values
    columns = ["campaign", "asset_name", "asset_path"]
    values = [campaign, data.get("asset_name"), data.get("asset_path")]
    
    # TRIBE scores
    columns.extend([
        "neural_engagement", "emotional_impact", "face_response",
        "scene_response", "motion_response", "language_engagement",
        "temporal_peak", "n_segments", "tribe_error", "brain_map_path"
    ])
    values.extend([
        data.get("neural_engagement"),
        data.get("emotional_impact"),
        data.get("face_response"),
        data.get("scene_response"),
        data.get("motion_response"),
        data.get("language_engagement"),
        data.get("temporal_peak"),
        data.get("n_segments"),
        data.get("tribe_error"),
        data.get("brain_map_path")
    ])
    
    # Saliency
    columns.extend(["center_bias", "saliency_score"])
    values.extend([data.get("center_bias"), data.get("saliency_score")])
    
    # CLIP
    columns.extend(["brand_match_score", "top_label"])
    values.extend([data.get("brand_match_score"), data.get("top_label")])
    
    # HSEmotion
    columns.extend(["dominant_emotion", "emotional_valence"])
    values.extend([data.get("dominant_emotion"), data.get("emotional_valence")])
    
    # Composite
    columns.extend(["total_score", "grade"])
    values.extend([data.get("total_score"), data.get("grade")])
    
    # Meta
    columns.append("has_tribe_preds")
    values.append(1 if data.get("has_tribe_preds", False) else 0)
    
    # Build column list and placeholders
    column_list = ", ".join(columns)
    placeholders = ", ".join(["?" for _ in columns])
    
    if existing:
        # UPDATE existing record
        set_clause = ", ".join([f"{col} = ?" for col in columns[2:]])  # Skip id, campaign, asset_name
        values.extend(values[2:])  # Add values for SET clause (skip campaign, asset_name)
        sql = f"UPDATE scores SET {set_clause} WHERE campaign = ? AND asset_name = ?"
        cursor.execute(sql, values)
    else:
        # INSERT new record
        sql = f"INSERT INTO scores ({column_list}) VALUES ({placeholders})"
        cursor.execute(sql, values)
    
    conn.commit()
    conn.close()


def get_campaign_scores(campaign: str) -> list[dict]:
    """
    Get all scores for a specific campaign.
    
    Args:
        campaign: Campaign name
        
    Returns:
        List of score records as dictionaries
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM scores WHERE campaign = ? ORDER BY total_score DESC", (campaign,))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_all_campaigns() -> list[str]:
    """
    Get all unique campaign names.
    
    Returns:
        List of campaign names
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT campaign FROM scores ORDER BY campaign")
    rows = cursor.fetchall()
    conn.close()
    
    return [row[0] for row in rows]


def get_asset_by_name(campaign: str, asset_name: str) -> Optional[dict]:
    """
    Get a specific asset's scores.
    
    Args:
        campaign: Campaign name
        asset_name: Asset name
        
    Returns:
        Score record as dictionary or None
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM scores WHERE campaign = ? AND asset_name = ?",
        (campaign, asset_name)
    )
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def delete_campaign(campaign: str) -> None:
    """
    Delete all scores for a campaign.
    
    Args:
        campaign: Campaign name
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM scores WHERE campaign = ?", (campaign,))
    conn.commit()
    conn.close()


def get_last_updated(campaign: str) -> Optional[str]:
    """
    Get the last updated timestamp for a campaign.
    
    Args:
        campaign: Campaign name
        
    Returns:
        Timestamp string or None
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT MAX(created_at) FROM scores WHERE campaign = ?",
        (campaign,)
    )
    row = cursor.fetchone()
    conn.close()
    
    return row[0] if row and row[0] else None


def get_campaign_stats(campaign: str) -> dict:
    """
    Get statistics for a campaign.
    
    Args:
        campaign: Campaign name
        
    Returns:
        Dictionary with stats
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_assets,
            SUM(CASE WHEN has_tribe_preds = 1 THEN 1 ELSE 0 END) as tribe_assets,
            AVG(total_score) as avg_total_score,
            MAX(total_score) as max_total_score,
            AVG(neural_engagement) as avg_neural_engagement,
            AVG(emotional_impact) as avg_emotional_impact
        FROM scores
        WHERE campaign = ?
    """, (campaign,))
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else {
        "total_assets": 0,
        "tribe_assets": 0,
        "avg_total_score": None,
        "max_total_score": None,
        "avg_neural_engagement": None,
        "avg_emotional_impact": None
    }
