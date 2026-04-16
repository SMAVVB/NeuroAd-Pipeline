"""
FastAPI Dashboard Backend for NeuroAd Pipeline
Port: 8080
"""

import json
import os
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configuration
CAMPAIGNS_DIR = Path("~/neuro_pipeline_project/campaigns").expanduser()
Mirofish_API_URL = "http://localhost:5001"

# Initialize FastAPI app
app = FastAPI(title="NeuroAd Pipeline Dashboard API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_campaigns() -> list[str]:
    """Get list of all campaign folder names."""
    if not CAMPAIGNS_DIR.exists():
        return []
    campaigns = [
        d.name for d in CAMPAIGNS_DIR.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]
    return sorted(campaigns)


def get_scores_path(campaign_name: str) -> Path:
    """Get path to pipeline_results_final.json for a campaign.

    Based on the data structure, pipeline_results_final.json is located in
    campaigns/{name}/scores/ directory.
    """
    scores_path = CAMPAIGNS_DIR / campaign_name / "scores" / "pipeline_results_final.json"

    if scores_path.exists():
        return scores_path

    # Fallback to report/ directory if scores/ doesn't exist
    report_path = CAMPAIGNS_DIR / campaign_name / "report" / "pipeline_results_final.json"
    if report_path.exists():
        return report_path

    raise FileNotFoundError(f"Scores file not found for campaign '{campaign_name}'")


def get_brand_report_path(campaign_name: str) -> Path | None:
    """Get path to STORM markdown report for a campaign.

    First looks in reports/ folder for STORM markdown files.
    Falls back to brand_context.txt if no markdown report exists.
    """
    # Check reports/ folder first (STORM markdown files)
    reports_dir = CAMPAIGNS_DIR / campaign_name / "reports"
    if reports_dir.exists():
        for f in reports_dir.iterdir():
            if f.suffix == ".md" and "storm" in f.name.lower():
                return f
        # If any markdown file exists, return the first one
        md_files = list(reports_dir.glob("*.md"))
        if md_files:
            return md_files[0]

    # Also check root level for markdown files
    for f in CAMPAIGNS_DIR.glob(f"{campaign_name}*.md"):
        return f

    # Fallback: brand_context.txt is used as brand report if no markdown exists
    brand_context = CAMPAIGNS_DIR / campaign_name / "brand_context.txt"
    if brand_context.exists():
        return brand_context

    return None


def get_brand_profile_path(campaign_name: str) -> Path | None:
    """Get path to brand_profile.json for a campaign."""
    # Check reports/ folder first
    reports_dir = CAMPAIGNS_DIR / campaign_name / "reports"
    if reports_dir.exists():
        profile_path = reports_dir / "brand_profile.json"
        if profile_path.exists():
            return profile_path

    # Also check campaign root level
    profile_path = CAMPAIGNS_DIR / campaign_name / "brand_profile.json"
    if profile_path.exists():
        return profile_path

    # Check raw_data directory
    raw_data_dir = Path("~/neuro_pipeline_project/raw_data").expanduser()
    if raw_data_dir.exists():
        for campaign_dir in raw_data_dir.iterdir():
            if campaign_dir.is_dir() and campaign_dir.name.startswith(campaign_name):
                profile_path = campaign_dir / "brand_profile.json"
                if profile_path.exists():
                    return profile_path

    return None


@app.get("/api/campaigns")
async def list_campaigns() -> list[str]:
    """List all campaign folder names."""
    return get_campaigns()


@app.get("/api/campaigns/{campaign_name}/scores")
async def get_campaign_scores(campaign_name: str) -> list[dict[str, Any]]:
    """Get pipeline scores from pipeline_results_final.json (LIST format)."""
    scores_path = get_scores_path(campaign_name)

    if not scores_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Scores file not found for campaign '{campaign_name}' at {scores_path}"
        )

    try:
        with open(scores_path, "r") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse scores file: {str(e)}"
        )


@app.get("/api/campaigns/{campaign_name}/brand")
async def get_brand_report(campaign_name: str) -> dict[str, Any]:
    """Get STORM markdown brand report."""
    report_path = get_brand_report_path(campaign_name)

    if report_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"Brand report not found for campaign '{campaign_name}'"
        )

    try:
        with open(report_path, "r") as f:
            content = f.read()
        return {
            "filename": report_path.name,
            "path": str(report_path),
            "content": content
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read brand report: {str(e)}"
        )


@app.get("/api/campaigns/{campaign_name}/brand-profile")
async def get_brand_profile(campaign_name: str) -> dict[str, Any]:
    """Get brand_profile.json for a campaign."""
    profile_path = get_brand_profile_path(campaign_name)

    if profile_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"Brand profile not found for campaign '{campaign_name}'"
        )

    try:
        with open(profile_path, "r") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse brand profile: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read brand profile: {str(e)}"
        )


@app.get("/api/campaigns/{campaign_name}/mirofish")
async def proxy_mirofish(campaign_name: str, graph_id: str | None = None) -> Any:
    """Proxy request to MiroFish API at localhost:5001.

    If graph_id is provided, fetches specific graph data.
    Otherwise, returns a basic MiroFish status response.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if graph_id:
                # Fetch specific graph data
                response = await client.get(
                    f"{Mirofish_API_URL}/api/graph/data/{graph_id}"
                )
            else:
                # Try to get graph data without project context first
                response = await client.get(f"{Mirofish_API_URL}/api")

            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to connect to MiroFish API: {str(e)}"
        )
    except httpx.HTTPStatusError as e:
        # If the default endpoint fails, return a minimal response
        # This is expected if MiroFish requires project context
        return {
            "status": "ok",
            "mirofish_api_url": Mirofish_API_URL,
            "note": "MiroFish API requires project context. Use /api/campaigns/{name}/mirofish?graph_id=<id> for specific data."
        }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
