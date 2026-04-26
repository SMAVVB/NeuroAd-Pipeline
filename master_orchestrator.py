#!/usr/bin/env python3
import os
import sys
import asyncio
import shutil
import logging
from pathlib import Path

from brand_orchestrator import main as run_brand_research
from pipeline_runner import run_pipeline_a

logging.basicConfig(level=logging.INFO, format="%(asctime)s [MASTER] %(message)s")
logger = logging.getLogger("MasterOrchestrator")

async def run_full_neuro_pipeline(brand: str, campaign_name: str, assets_src_dir: str):
    logger.info(f"🚀 STARTE MASTER-PIPELINE FÜR: {brand} | Kampagne: {campaign_name}")
    
    # 1. Ordnerstruktur für Pipeline A vorbereiten
    campaign_dir = Path(f"./campaigns/{campaign_name}")
    campaign_assets = campaign_dir / "assets"
    campaign_assets.mkdir(parents=True, exist_ok=True)
    
    src_path = Path(assets_src_dir)
    if src_path.absolute() != campaign_assets.absolute():
        logger.info(f"📂 Kopiere Assets von {src_path} nach {campaign_assets}...")
        for file in src_path.iterdir():
            if file.is_file():
                shutil.copy(file, campaign_assets)

    # 2. Brand Research
    logger.info("🔍 PHASE 1: Starte Brand Research Agent...")
    try:
        await run_brand_research(brand)
    except Exception as e:
        logger.error(f"❌ Brand Research gecrasht: {e}")
        raise e

    # 3. Datenbrücke bauen
    raw_data_base = Path("./raw_data")
    brand_dirs = [d for d in raw_data_base.iterdir() if d.is_dir() and brand.replace(' ', '_') in d.name]
    
    if brand_dirs:
        latest_brand_dir = max(brand_dirs, key=os.path.getmtime)
        context_source = latest_brand_dir / "LLM_Summaries_Combined.md"
        if context_source.exists():
            context_dest = campaign_dir / "brand_context.txt"
            shutil.copy(context_source, context_dest)
            logger.info("✅ Brand Context erfolgreich für Pipeline A transferiert.")

    # 4. Pipeline A starten
    logger.info("🧠 PHASE 2: Starte Pipeline A (TRIBE, ViNet, CLIP, Emotion, MiroFish)...")
    try:
        run_pipeline_a(campaign_dir=str(campaign_dir))
        logger.info(f"✅ Pipeline A abgeschlossen! Report generiert.")
    except Exception as e:
        logger.error(f"❌ Pipeline A gecrasht: {e}")
        raise e

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python master_orchestrator.py <BrandName> <CampaignName> <PathToAssets>")
        sys.exit(1)
        
    asyncio.run(run_full_neuro_pipeline(sys.argv[1], sys.argv[2], sys.argv[3]))
