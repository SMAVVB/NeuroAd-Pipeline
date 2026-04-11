import sys
import os
import asyncio
from datetime import datetime
from config_core import RAW_DATA_DIR

from agents.agent_baseline import generate_baseline
from agents.agent_publisher import run_publisher_agent
from agents.agent_social import run_social_agent
from agents.agent_scraper import run_mass_scraper
from agents.agent_storm import build_storm_wikipedia
from agents.agent_council import run_council_review 

async def main(brand: str):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = os.path.join(RAW_DATA_DIR, f"{brand.replace(' ', '_')}_{timestamp}")
    os.makedirs(save_dir, exist_ok=True)
    
    print("="*60)
    print(f"🚀 NEURO-PIPELINE: OMNI-CHANNEL HYDRA ARCHITECTURE")
    print(f"🏢 Marke: {brand}")
    print("="*60 + "\n")

    baseline = generate_baseline(brand, save_dir)
    
    # 1. HYDRA-PUBLISHER (Erntet massive News & Science URLs)
    # Hier kannst du die Skalierung einstellen! (Aktuell: 10 Säulen * 10 Queries = 100 Queries)
    publisher_urls = run_publisher_agent(brand, "", baseline, num_pillars=10, queries_per_pillar=10)
    
    # 2. OMNI-CHANNEL SOCIAL (Reddit, YT, X, IG, LinkedIn)
    social_data = run_social_agent(brand, "", baseline)
    
    print("\n   💾 Speichere strukturierte Social-Daten...")
    if social_data.get("video"):
        with open(os.path.join(save_dir, "url_social_video.txt"), "w", encoding="utf-8") as f:
            f.write(f"URL: Global_Video_Comments\n\n{social_data['video']}")
    if social_data.get("reddit"):
        with open(os.path.join(save_dir, "url_social_reddit.txt"), "w", encoding="utf-8") as f:
            f.write(f"URL: Global_Reddit_Discussions\n\n{social_data['reddit']}")

    # 3. MASS SCRAPING (Führt News/Science URLs und OSINT-Social-URLs zusammen!)
    all_urls_to_scrape = publisher_urls + social_data.get("osint_urls", [])
    print(f"\n🌪️ Führe {len(all_urls_to_scrape)} URLs dem Mass-Scraper zu...")
    
    run_mass_scraper(all_urls_to_scrape, save_dir)
    
    # 4. RAG-Engine & 5. Council Audit
    build_storm_wikipedia(brand, save_dir)
    run_council_review(brand, save_dir)
    
    print(f"\n✅ PIPELINE KOMPLETT ABGESCHLOSSEN! Alle Ergebnisse in: {save_dir}")

if __name__ == "__main__":
    brand_input = sys.argv[1] if len(sys.argv) > 1 else "Red Bull"
    asyncio.run(main(brand_input))
