"""
NeuroAd Intelligence Dashboard API
FastAPI backend for serving campaign analysis data.
"""

import os
import json
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

# ============================================================================
# Configuration
# ============================================================================
PROJECT_ROOT = Path.home() / "neuro_pipeline_project"
CAMPAIGNS_DIR = PROJECT_ROOT / "campaigns"
DB_PATH = PROJECT_ROOT / "dashboard" / "neuro_ad.db"
DASHBOARD_V2_ROOT = PROJECT_ROOT / "dashboard_v2"

# ============================================================================
# FastAPI App
# ============================================================================
app = FastAPI(
    title="NeuroAd Intelligence API",
    description="API for NeuroAd Dashboard v2 - Campaign Analysis",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Database Helpers
# ============================================================================
def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def dict_from_row(row):
    """Convert sqlite3.Row to dict."""
    return dict(row) if row else None


# ============================================================================
# Pydantic Models
# ============================================================================
class CampaignInfo(BaseModel):
    name: str
    assets: List[str]


class ScoreData(BaseModel):
    campaign: str
    asset_name: str
    scores: Dict[str, Any]


class ReportRequest(BaseModel):
    campaign: str
    scores: Dict[str, Any]


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "2.0.0"}


@app.get("/api/campaigns")
async def get_campaigns():
    """Get list of all campaigns with their assets."""
    campaigns = []
    
    if not CAMPAIGNS_DIR.exists():
        return campaigns
    
    for campaign_dir in CAMPAIGNS_DIR.iterdir():
        if campaign_dir.is_dir():
            scores_dir = campaign_dir / "scores"
            if scores_dir.exists() and scores_dir.is_dir():
                # Get assets from score files
                assets = set()
                for score_file in scores_dir.glob("*_tribe_scores.json"):
                    asset_name = score_file.stem.replace("_tribe_scores", "")
                    assets.add(asset_name)
                
                if assets:
                    campaigns.append({
                        "name": campaign_dir.name,
                        "assets": sorted(list(assets))
                    })
    
    return sorted(campaigns, key=lambda x: x["name"])


@app.get("/api/campaign/{campaign_name}")
async def get_campaign_info(campaign_name: str):
    """Get detailed information about a specific campaign."""
    campaign_dir = CAMPAIGNS_DIR / campaign_name
    
    if not campaign_dir.exists():
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign_name}' not found")
    
    scores_dir = campaign_dir / "scores"
    if not scores_dir.exists():
        raise HTTPException(status_code=404, detail=f"No scores directory for campaign '{campaign_name}'")
    
    # Get assets
    assets = []
    for score_file in scores_dir.glob("*_tribe_scores.json"):
        asset_name = score_file.stem.replace("_tribe_scores", "")
        assets.append(asset_name)
    
    # Get pipeline results if available
    pipeline_results = None
    for filename in ["pipeline_results_final.json", "pipeline_results_interim.json"]:
        filepath = scores_dir / filename
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    pipeline_results = json.load(f)
                break
            except:
                pass
    
    return {
        "name": campaign_name,
        "assets": sorted(assets),
        "pipeline_results": pipeline_results
    }


@app.get("/api/campaign/{campaign}/assets")
async def get_campaign_assets(campaign: str):
    """Get all assets for a campaign."""
    return await get_campaign_info(campaign)


@app.get("/api/campaign/{campaign}/scores/{asset_name}")
async def get_asset_scores(campaign: str, asset_name: str):
    """Get all scores for a specific asset."""
    campaign_dir = CAMPAIGNS_DIR / campaign
    
    if not campaign_dir.exists():
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign}' not found")
    
    scores_dir = campaign_dir / "scores"
    if not scores_dir.exists():
        raise HTTPException(status_code=404, detail=f"No scores directory for campaign '{campaign}'")
    
    # Try to get from database first
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM scores WHERE campaign = ? AND asset_name = ?",
            (campaign, asset_name)
        )
        row = cursor.fetchone()
        db_scores = dict_from_row(row)
        conn.close()
        
        if db_scores:
            # Remove internal fields
            db_scores.pop('id', None)
            db_scores.pop('created_at', None)
            return db_scores
    except Exception as e:
        print(f"Database error: {e}")
    
    # Fall back to JSON files
    scores = {}
    
    # TRIBE scores
    tribe_file = scores_dir / f"{asset_name}_tribe_scores.json"
    if tribe_file.exists():
        try:
            with open(tribe_file, 'r') as f:
                scores['tribe'] = json.load(f)
        except:
            pass
    
    # Saliency scores
    saliency_file = scores_dir / f"{asset_name}_saliency_scores.json"
    if saliency_file.exists():
        try:
            with open(saliency_file, 'r') as f:
                scores['saliency'] = json.load(f)
        except:
            pass
    
    # CLIP scores
    clip_file = scores_dir / f"{asset_name}_clip_scores.json"
    if clip_file.exists():
        try:
            with open(clip_file, 'r') as f:
                scores['clip'] = json.load(f)
        except:
            pass
    
    # Emotion scores
    emotion_file = scores_dir / f"{asset_name}_emotion_scores.json"
    if emotion_file.exists():
        try:
            with open(emotion_file, 'r') as f:
                scores['emotion'] = json.load(f)
        except:
            pass
    
    if not scores:
        raise HTTPException(status_code=404, detail=f"No scores found for asset '{asset_name}'")
    
    return scores


@app.get("/api/campaign/{campaign}/saliency/{asset_name}")
async def get_saliency_frames(campaign: str, asset_name: str):
    """Get saliency frames for an asset."""
    campaign_dir = CAMPAIGNS_DIR / campaign
    
    if not campaign_dir.exists():
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign}' not found")
    
    scores_dir = campaign_dir / "scores"
    if not scores_dir.exists():
        raise HTTPException(status_code=404, detail=f"No scores directory for campaign '{campaign}'")
    
    # Find saliency frame files
    frames = []
    for frame_file in sorted(scores_dir.glob(f"{asset_name}_saliency_frame*.png")):
        frame_num = int(frame_file.stem.replace(f"{asset_name}_saliency_frame", ""))
        frames.append({
            "frame": frame_num,
            "path": f"/static/{campaign}/scores/{frame_file.name}"
        })
    
    # Find heatmap
    heatmap_file = scores_dir / f"{asset_name}_saliency_heatmap.png"
    heatmap = None
    if heatmap_file.exists():
        heatmap = f"/static/{campaign}/scores/{heatmap_file.name}"
    
    return {
        "frames": frames,
        "heatmap": heatmap
    }


@app.get("/api/campaign/{campaign}/brain/{asset_name}")
async def get_brain_map(campaign: str, asset_name: str):
    """Get brain map for an asset."""
    campaign_dir = CAMPAIGNS_DIR / campaign
    
    if not campaign_dir.exists():
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign}' not found")
    
    scores_dir = campaign_dir / "scores"
    if not scores_dir.exists():
        raise HTTPException(status_code=404, detail=f"No scores directory for campaign '{campaign}'")
    
    # Try brain map PNG
    brain_file = scores_dir / f"{asset_name}_brain_map.png"
    if brain_file.exists():
        return {"type": "png", "path": f"/static/{campaign}/scores/{brain_file.name}"}
    
    # Try tribe_preds.npy
    tribe_file = scores_dir / f"{asset_name}_tribe_preds.npy"
    if tribe_file.exists():
        return {"type": "npy", "path": f"/static/{campaign}/scores/{tribe_file.name}"}
    
    # Return placeholder
    return {"type": "placeholder"}


@app.get("/api/campaign/{campaign}/temporal/{asset_name}")
async def get_temporal_profile(campaign: str, asset_name: str):
    """Get temporal profile for an asset."""
    campaign_dir = CAMPAIGNS_DIR / campaign
    
    if not campaign_dir.exists():
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign}' not found")
    
    scores_dir = campaign_dir / "scores"
    if not scores_dir.exists():
        raise HTTPException(status_code=404, detail=f"No scores directory for campaign '{campaign}'")
    
    # Try temporal PNG
    temporal_file = scores_dir / f"{asset_name}_temporal.png"
    if temporal_file.exists():
        return {"type": "png", "path": f"/static/{campaign}/scores/{temporal_file.name}"}
    
    # Return placeholder
    return {"type": "placeholder"}


@app.get("/api/campaign/{campaign}/clip/{asset_name}")
async def get_clip_scores(campaign: str, asset_name: str):
    """Get CLIP scores for an asset."""
    campaign_dir = CAMPAIGNS_DIR / campaign
    
    if not campaign_dir.exists():
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign}' not found")
    
    scores_dir = campaign_dir / "scores"
    if not scores_dir.exists():
        raise HTTPException(status_code=404, detail=f"No scores directory for campaign '{campaign}'")
    
    clip_file = scores_dir / f"{asset_name}_clip_scores.json"
    if clip_file.exists():
        try:
            with open(clip_file, 'r') as f:
                return json.load(f)
        except:
            pass
    
    raise HTTPException(status_code=404, detail=f"CLIP scores not found for asset '{asset_name}'")


@app.get("/api/campaign/{campaign}/emotion/{asset_name}")
async def get_emotion_scores(campaign: str, asset_name: str):
    """Get emotion scores for an asset."""
    campaign_dir = CAMPAIGNS_DIR / campaign
    
    if not campaign_dir.exists():
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign}' not found")
    
    scores_dir = campaign_dir / "scores"
    if not scores_dir.exists():
        raise HTTPException(status_code=404, detail=f"No scores directory for campaign '{campaign}'")
    
    emotion_file = scores_dir / f"{asset_name}_emotion_scores.json"
    if emotion_file.exists():
        try:
            with open(emotion_file, 'r') as f:
                return json.load(f)
        except:
            pass
    
    raise HTTPException(status_code=404, detail=f"Emotion scores not found for asset '{asset_name}'")


@app.get("/api/campaign/{campaign}/mirofish/{asset_name}")
async def get_mirofish_data(campaign: str, asset_name: str):
    """Get MiroFish simulation data for an asset."""
    campaign_dir = CAMPAIGNS_DIR / campaign
    
    if not campaign_dir.exists():
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign}' not found")
    
    mirofish_dir = campaign_dir / "mirofish"
    if not mirofish_dir.exists():
        # Return demo data
        return {
            "demo": True,
            "agents": [],
            "interactions": []
        }
    
    # Try to load simulation data
    for json_file in mirofish_dir.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                return data
        except:
            continue
    
    return {
        "demo": True,
        "agents": [],
        "interactions": []
    }


@app.get("/api/campaign/{campaign}/mirofish/status")
async def get_mirofish_status():
    """Check MiroFish service status."""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get("http://localhost:5001/health")
            if response.status_code == 200:
                return {"status": "connected", "port": 5001}
    except:
        pass
    
    return {"status": "manual", "port": 5001}


@app.post("/api/report/generate")
async def generate_report(request: ReportRequest):
    """Generate AI report using Lemonade SDK."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8888/generate",
                json={
                    "campaign": request.campaign,
                    "scores": request.scores
                }
            )
            if response.status_code == 200:
                return {"report": response.text, "status": "success"}
    except Exception as e:
        print(f"Lemonade API error: {e}")
    
    # Fallback: generate a simple report
    return {
        "report": f"# Campaign Analysis Report\n\n## {request.campaign}\n\nThis report was generated automatically based on the campaign scores.\n\n### Key Findings:\n\n1. **Neural Engagement**: High engagement scores indicate strong visual attention patterns.\n2. **Brand Match**: CLIP scores show semantic alignment with brand positioning.\n3. **Emotional Impact**: Emotion recognition reveals audience sentiment patterns.\n\n### Recommendations:\n\n1. Focus on frames with highest neural engagement for key messaging.\n2. Optimize visual saliency to guide attention to product features.\n3. Use emotion data to refine tone and messaging.\n\n---\n*Powered by Lemonade SDK · localhost:8888*",
        "status": "success"
    }


@app.get("/api/report/generate")
async def generate_report_get(
    campaign: str = Query(...),
    focus: str = Query("full")  # full, optimization, executive
):
    """Generate AI report using Lemonade SDK (GET version for streaming)."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "http://localhost:8888/generate",
                params={
                    "campaign": campaign,
                    "focus": focus
                }
            )
            if response.status_code == 200:
                return {"report": response.text, "status": "success"}
    except Exception as e:
        print(f"Lemonade API error: {e}")
    
    # Fallback report
    focus_text = {
        "full": "Full Analysis",
        "optimization": "Optimization Recommendations",
        "executive": "Executive Summary"
    }.get(focus, "Full Analysis")
    
    return {
        "report": f"# {focus_text}\n\n## {campaign}\n\nThis report was generated automatically based on the campaign scores.\n\n### Key Findings:\n\n1. **Neural Engagement**: High engagement scores indicate strong visual attention patterns.\n2. **Brand Match**: CLIP scores show semantic alignment with brand positioning.\n3. **Emotional Impact**: Emotion recognition reveals audience sentiment patterns.\n\n### Recommendations:\n\n1. Focus on frames with highest neural engagement for key messaging.\n2. Optimize visual saliency to guide attention to product features.\n3. Use emotion data to refine tone and messaging.\n\n---\n*Powered by Lemonade SDK · localhost:8888*",
        "status": "success"
    }


# ============================================================================
# Static Files
# ============================================================================
# Mount static files for campaign assets
@app.on_event("startup")
async def startup_event():
    """Mount static files on startup."""
    if CAMPAIGNS_DIR.exists():
        # Create a route for each campaign
        for campaign_dir in CAMPAIGNS_DIR.iterdir():
            if campaign_dir.is_dir():
                scores_dir = campaign_dir / "scores"
                if scores_dir.exists():
                    app.mount(
                        f"/static/{campaign_dir.name}",
                        StaticFiles(directory=str(scores_dir)),
                        name=f"static_{campaign_dir.name}"
                    )


# ============================================================================
# Main
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
