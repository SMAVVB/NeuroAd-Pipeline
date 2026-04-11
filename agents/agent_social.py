import json
import re
import sys
import os
import subprocess
import requests
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_core import ask_llm, search_searxng, MODEL_WORKHORSE

def fetch_video_comments(video_url: str, max_comments: int = 5000) -> str:
    print(f"   ▶️ yt-dlp: Sauge Kommentare von {video_url}...")
    try:
        cmd = ["yt-dlp", "--get-comments", "--dump-json", "--max-comments", str(max_comments), "--no-warnings", video_url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        comments_text = ""
        for line in result.stdout.strip().split('\n'):
            if not line: continue
            try:
                data = json.loads(line)
                for comment in data.get("comments", []):
                    text = comment.get("text", "")
                    if text: comments_text += f"- {text}\n"
            except: pass
        return comments_text[:100000] 
    except: return ""

def fetch_reddit_mass_data(query: str, pages: int = 10) -> str:
    print(f"   👽 Reddit: Deep-Scan nach '{query}'...")
    headers = {"User-Agent": "Mozilla/5.0"}
    reddit_text, after = "", None
    
    for i in range(pages):
        url = f"https://www.reddit.com/search.json?q={query}&limit=100"
        if after: url += f"&after={after}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            data = res.json()
            posts = data.get("data", {}).get("children", [])
            if not posts: break
            for post in posts:
                p = post.get("data", {})
                reddit_text += f"Titel: {p.get('title', '')}\nInhalt: {p.get('selftext', '')[:1000]}\n---\n"
            after = data.get("data", {}).get("after")
            if not after: break
            time.sleep(1)
        except: break
    return reddit_text

def run_social_agent(brand: str, note: str, baseline: str) -> dict:
    print(f"\n💬 [PHASE 2] Starte OMNI-CHANNEL Social Extraction für '{brand}'...")
    
    # OSINT Dorking Queries generieren
    dork_prompt = f"""Generiere hochspezifische Dorking-Keywords für '{brand}'.
    Gib AUSSCHLIESSLICH dieses JSON zurück:
    {{
      "youtube_tiktok": ["{brand} review", "{brand} exposed"],
      "reddit": ["{brand} marketing", "{brand} employee"],
      "x_twitter": ["{brand} controversy", "{brand} news"],
      "instagram": ["#{brand.replace(' ', '')}", "{brand} event"],
      "linkedin": ["{brand} corporate culture", "{brand} business model"]
    }}"""
    
    response = ask_llm(dork_prompt, "Generiere Dorks.", MODEL_WORKHORSE)
    queries = {}
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try: queries = json.loads(json_match.group())
        except: pass

    social_data = {"video": "", "reddit": "", "osint_urls": []}
    
    # 1. Video (YouTube & TikTok)
    for q in queries.get("youtube_tiktok", [])[:5]:
        v_urls = search_searxng(q)
        valid = [u for u in v_urls if "youtube.com" in u or "tiktok.com" in u]
        for url in valid[:2]:
            social_data["video"] += fetch_video_comments(url)
            
    # 2. Reddit API
    for q in queries.get("reddit", [])[:5]:
        social_data["reddit"] += fetch_reddit_mass_data(q, pages=10)

    # 3. Walled Gardens (X, IG, LinkedIn) via SearXNG-OSINT
    print(f"\n   🌐 Starte OSINT-Dorking für X, Instagram und LinkedIn...")
    
    dork_targets = {
        "x_twitter": "site:x.com OR site:twitter.com",
        "instagram": "site:instagram.com",
        "linkedin": "site:linkedin.com/posts OR site:linkedin.com/pulse"
    }
    
    for platform, dork_base in dork_targets.items():
        for q in queries.get(platform, [])[:5]:
            search_query = f"{dork_base} {q}"
            found_urls = search_searxng(search_query)
            social_data["osint_urls"].extend(found_urls)
            
    return social_data
