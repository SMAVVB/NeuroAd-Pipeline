"""
FastAPI Dashboard Backend for NeuroAd Pipeline
Port: 8080
"""

import base64
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

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


def parse_brand_context(content: str) -> dict[str, Any]:
    """Parse brand_context.txt content and extract structured brand information.

    Extracts:
    - brand name from campaign title
    - founding year (defaults to 2024 if not specified)
    - size (defaults to "Mid-sized")
    - size_reasoning (defaults to "Based on campaign context")
    - primary_markets (defaults to empty list)
    - active_languages (defaults to ["en"])
    - industry (defaults to "Technology")
    - sub_industries (defaults to empty list)
    - key_competitors (defaults to empty list)
    - historical_periods (defaults to empty list)
    """
    lines = content.strip().split('\n')
    result: dict[str, Any] = {
        "brand": "",
        "founding_year": 2024,
        "size": "Mid-sized",
        "size_reasoning": "Based on campaign context",
        "primary_markets": [],
        "active_languages": ["en"],
        "industry": "Technology",
        "sub_industries": [],
        "key_competitors": [],
        "historical_periods": [],
    }

    # Extract brand name from campaign title
    # Format: "Campaign: Apple iPhone 17 vs Samsung Galaxy AI Photo — Ad Creative Comparison"
    campaign_line = next((line for line in lines if line.startswith("Campaign:")), "")
    if campaign_line:
        # Extract brands from "Brand A vs Brand B" pattern
        vs_match = re.search(r'Campaign:\s*(.+?)\s*vs\s*(.+?)(?:\s*—|\s*$)', campaign_line)
        if vs_match:
            brand1 = vs_match.group(1).strip()
            brand2 = vs_match.group(2).strip()
            result["brand"] = f"{brand1} vs {brand2}"
            result["key_competitors"] = [brand1, brand2]
        else:
            result["brand"] = campaign_line.replace("Campaign:", "").strip()

    # Extract target audience (for industry/size hints)
    audience_line = next((line for line in lines if "Target audience:" in line), "")
    if audience_line:
        audience = audience_line.replace("Target audience:", "").strip()
        if "premium" in audience.lower() or "tech-savvy" in audience.lower():
            result["size"] = "Premium/Luxury"
            result["size_reasoning"] = "Target audience indicates premium market position"
        if "tech" in audience.lower() or "smartphone" in audience.lower():
            result["industry"] = "Consumer Electronics"
            result["sub_industries"] = ["Smartphones", "Mobile Technology"]

    # Extract themes (for industry hints)
    theme_line = next((line for line in lines if "- Theme:" in line), "")
    if theme_line:
        if "AI" in theme_line or "artificial intelligence" in theme_line.lower():
            result["industry"] = "Artificial Intelligence"
            result["sub_industries"] = ["AI Software", "Machine Learning"]

    # Extract platforms (for markets hint)
    platform_line = next((line for line in lines if "Platform:" in line), "")
    if platform_line:
        if "TikTok" in platform_line:
            result["active_languages"] = ["en", "es", "pt", "id"]
        if "Instagram" in platform_line or "YouTube" in platform_line:
            result["primary_markets"].append({"country": "United States", "language": "en", "depth": "high"})

    # Extract objective (for industry hints)
    objective_line = next((line for line in lines if "Objective:" in line), "")
    if objective_line:
        if "social media" in objective_line.lower():
            result["primary_markets"].append({"country": "United States", "language": "en", "depth": "high"})
            result["primary_markets"].append({"country": "Germany", "language": "de", "depth": "medium"})

    return result


def get_brand_profile_path(campaign_name: str) -> Path | None:
    """Get path to brand_profile.json for a campaign.

    Also checks brand_context.txt as fallback for campaign metadata.
    """
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

    # Fallback: brand_context.txt contains campaign metadata
    brand_context = CAMPAIGNS_DIR / campaign_name / "brand_context.txt"
    if brand_context.exists():
        return brand_context

    return None



def load_campaign_scores_from_files(campaign_name: str) -> list:
    """Load scores by merging individual per-asset JSON files."""
    scores_dir = CAMPAIGNS_DIR / campaign_name / "scores"
    if not scores_dir.exists():
        return []
    assets = {}
    for f in scores_dir.glob("*_tribe_scores.json"):
        name = f.name.replace("_tribe_scores.json", "")
        assets[name] = {"asset_name": name, "asset_path": f"campaigns/{campaign_name}/assets/{name}.mp4"}
    for name in list(assets.keys()):
        t = scores_dir / f"{name}_tribe_scores.json"
        if t.exists():
            assets[name]["tribe"] = json.loads(t.read_text())
        c = scores_dir / f"{name}_clip_scores.json"
        if c.exists():
            assets[name]["clip"] = json.loads(c.read_text())
        s = scores_dir / f"{name}_saliency_scores.json"
        if s.exists():
            assets[name]["vinet"] = json.loads(s.read_text())
        prf = scores_dir / "pipeline_results_final.json"
        if prf.exists():
            pipeline = json.loads(prf.read_text())
            for item in pipeline:
                iname = item.get("asset_name", "").replace(".mp4", "")
                if iname == name:
                    assets[name]["mirofish"] = item.get("mirofish", {})
                    assets[name]["composite"] = item.get("composite", {})
                    break
    return list(assets.values())


@app.get("/api/campaigns")
async def list_campaigns() -> list[str]:
    """List all campaign folder names."""
    return get_campaigns()


@app.get("/api/campaigns/{campaign_name}/scores")
async def get_campaign_scores(campaign_name: str) -> list[dict[str, Any]]:
    """Get merged scores from individual per-asset JSON files."""
    data = load_campaign_scores_from_files(campaign_name)
    if not data:
        raise HTTPException(status_code=404, detail=f"No scores found for campaign '{campaign_name}'")
    return data


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
    """Get brand_profile.json for a campaign.

    Falls back to brand_context.txt if brand_profile.json doesn't exist.
    Parses brand_context.txt and extracts structured brand information.
    """
    profile_path = get_brand_profile_path(campaign_name)

    if profile_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"Brand profile not found for campaign '{campaign_name}'"
        )

    try:
        # Handle brand_context.txt (plain text) vs brand_profile.json (JSON)
        if profile_path.suffix == ".txt":
            with open(profile_path, "r") as f:
                content = f.read()

            # Parse brand_context.txt and extract structured data
            parsed_data = parse_brand_context(content)

            # Add metadata about the file source
            file_stat = profile_path.stat()
            parsed_data["_source_file"] = {
                "filename": profile_path.name,
                "path": str(profile_path),
                "type": "brand_context",
                "last_modified": file_stat.st_mtime,
                "last_modified_iso": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            }

            return parsed_data

        # JSON file
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


@app.get("/api/campaigns/{campaign_name}/assets/{asset_name}/heatmap")
async def get_heatmap(campaign_name: str, asset_name: str, heatmap_type: str = "saliency"):
    """Get heatmap image for a specific asset.

    Returns the saliency heatmap PNG as base64 encoded data.
    Supports: saliency (default), overlay, temporal, brain

    Returns 404 if no heatmap found.
    """
    # Map heatmap types to file suffixes
    heatmap_suffixes = {
        "saliency": "saliency_heatmap.png",
        "overlay": "saliency_frame",
        "temporal": "temporal.png",
        "brain": "brain_mean.png",
    }

    if heatmap_type not in heatmap_suffixes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid heatmap_type. Supported types: {', '.join(heatmap_suffixes.keys())}"
        )

    # Build path to the scores directory
    scores_dir = CAMPAIGNS_DIR / campaign_name / "scores"

    if not scores_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Scores directory not found for campaign '{campaign_name}'"
        )

    # Find the matching file
    heatmap_file = None
    suffix = heatmap_suffixes[heatmap_type]

    if heatmap_type == "saliency":
        # Look for exact match: {asset_name}_saliency_heatmap.png
        heatmap_file = scores_dir / f"{asset_name}_{suffix}"
    elif heatmap_type == "overlay":
        # Look for frame file (e.g., {asset_name}_saliency_frame016.png)
        # Find the highest numbered frame file
        frame_files = list(scores_dir.glob(f"{asset_name}_{suffix}*.png"))
        if frame_files:
            # Sort by number in filename and get the last one
            frame_files.sort(key=lambda f: int(re.search(r'frame(\d+)', f.name).group(1)))
            heatmap_file = frame_files[-1]
    else:
        # Direct match for temporal.png and brain_mean.png
        heatmap_file = scores_dir / f"{asset_name}_{suffix}"

    if heatmap_file is None or not heatmap_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Heatmap file not found: {heatmap_file.name}"
        )

    # Read and return as base64
    try:
        image_data = heatmap_file.read_bytes()
        encoded_image = base64.b64encode(image_data).decode()
        return {
            "image": f"data:image/png;base64,{encoded_image}",
            "filename": heatmap_file.name,
            "path": str(heatmap_file),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read heatmap file: {str(e)}"
        )


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
