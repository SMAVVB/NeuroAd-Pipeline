import sys
import os
import asyncio
import subprocess
from datetime import datetime
from config_core import RAW_DATA_DIR

# ChromaDB Installation check (VOR allem anderen!)
try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    print("   ⚠️ ChromaDB nicht installiert. Installiere jetzt...")
    #subprocess.run([sys.executable, "-m", "pip", "install", "chromadb", "--break-system-packages", "-q"], check=False)

from agents.agent_archive import get_wayback_urls, get_semantic_scholar_urls
from agents.agent_baseline import generate_baseline
from agents.agent_publisher import run_publisher_agent
from agents.agent_science import run_science_agent
from agents.agent_social import run_social_agent
from agents.agent_scraper import run_mass_scraper
from agents.agent_storm import build_storm_wikipedia
from agents.agent_council import run_council_review
from brand_profile import build_brand_profile

async def main(brand: str):
    """
    TASK 4: brand_orchestrator.py — Seed übergeben.
    
    In der main() Funktion, nach generate_baseline():
    seed_path = os.path.join(save_dir, "Phase_0_Verified_Seed.md")
    seed_content = open(seed_path, encoding="utf-8").read() if os.path.exists(seed_path) else ""
    
    build_storm_wikipedia(brand, save_dir, seed_content=seed_content) aufrufen statt build_storm_wikipedia(brand, save_dir).
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = os.path.join(RAW_DATA_DIR, f"{brand.replace(' ', '_')}_{timestamp}")
    os.makedirs(save_dir, exist_ok=True)
    
    print("="*60)
    print(f"🚀 NEURO-PIPELINE: OMNI-CHANNEL HYDRA ARCHITECTURE")
    print(f"🏢 Marke: {brand}")
    print("="*60 + "\n")

    baseline = generate_baseline(brand, save_dir)
    
    # Brand-Profil erstellen (NEU)
    seed_path = os.path.join(save_dir, "Phase_0_Verified_Seed.md")
    seed_content = open(seed_path, encoding="utf-8").read() if os.path.exists(seed_path) else ""
    brand_profile = build_brand_profile(brand, seed_content, save_dir)
    
    # 1. HYDRA-PUBLISHER (Erntet massive News & Science URLs)
    # Hier kannst du die Skalierung einstellen! (Aktuell: 10 Säulen * 10 Queries = 100 Queries)
    publisher_result = await run_publisher_agent(brand, "", baseline, brand_profile=brand_profile)
    if isinstance(publisher_result, tuple):
        publisher_urls, url_meta = publisher_result
    else:
        publisher_urls, url_meta = publisher_result, {}
    
    # 2. OMNI-CHANNEL SOCIAL (Reddit, YT, X, IG, LinkedIn) - PARALLEL mit Science
    social_task = asyncio.create_task(
        asyncio.to_thread(run_social_agent, brand, "", baseline, brand_profile=brand_profile)
    )
    science_task = asyncio.create_task(
        asyncio.to_thread(run_science_agent, brand, brand_profile, max_depth=3)
    )
    social_data, science_result = await asyncio.gather(social_task, science_task)
    science_urls = science_result["paper_urls"]
    
    print("\n   💾 Speichere strukturierte Social-Daten...")
    if social_data.get("youtube_comments"):
        with open(os.path.join(save_dir, "url_social_youtube.txt"), "w", encoding="utf-8") as f:
            f.write(f"URL: YouTube_Comments\n\n{social_data['youtube_comments']}")
    if social_data.get("reddit_text"):
        with open(os.path.join(save_dir, "url_social_reddit.txt"), "w", encoding="utf-8") as f:
            f.write(f"URL: Reddit_Discussions\n\n{social_data['reddit_text']}")
    if social_data.get("twitter_text"):
        with open(os.path.join(save_dir, "url_social_twitter.txt"), "w", encoding="utf-8") as f:
            f.write(f"URL: Twitter_X_Posts\n\n{social_data['twitter_text']}")
    if social_data.get("tiktok_comments"):
        with open(os.path.join(save_dir, "url_social_tiktok.txt"), "w", encoding="utf-8") as f:
            f.write(f"URL: TikTok_Comments\n\n{social_data['tiktok_comments']}")
    if social_data.get("hn_text"):
        with open(os.path.join(save_dir, "url_social_hackernews.txt"), "w", encoding="utf-8") as f:
            f.write(f"URL: HackerNews\n\n{social_data['hn_text']}")
    
    print(f"\n📚 Wissenschafts-Sweep: {len(science_urls)} Paper-URLs")
    
    # Alle URLs zusammenführen
    all_urls_to_scrape = (publisher_urls +
        social_data.get("youtube_urls", []) +
        social_data.get("tiktok_urls", []) +
        social_data.get("instagram_urls", []) +
        social_data.get("linkedin_urls", []) +
        social_data.get("review_urls", []) +
        social_data.get("news_urls", []) +
        social_data.get("osint_urls", []) +
        science_urls)
    print(f"\n🌪️ Führe {len(all_urls_to_scrape)} URLs dem Mass-Scraper zu...")
    
    # 4. MASS SCRAPING (Führt News/Science URLs und OSINT-Social-URLs zusammen!)
    await run_mass_scraper(all_urls_to_scrape, save_dir)
    
    # 4. RAG-Engine & 5. Council Audit
    build_storm_wikipedia(brand, save_dir, seed_content=seed_content, brand_profile=brand_profile)
    run_council_review(brand, save_dir)
    
    print(f"\n✅ PIPELINE KOMPLETT ABGESCHLOSSEN! Alle Ergebnisse in: {save_dir}")

if __name__ == "__main__":
    brand_input = sys.argv[1] if len(sys.argv) > 1 else "Red Bull"
    asyncio.run(main(brand_input))
