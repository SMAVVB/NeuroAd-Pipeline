import json
import re
import sys
import os
import subprocess
import requests
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from curl_cffi.requests import AsyncSession

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_core import ask_llm, search_searxng, MODEL_WORKHORSE, SEARXNG_URL


# ─── YOUTUBE ────────────────────────────────────────────────────────────────

def find_brand_youtube_channels(brand: str) -> list:
    """Findet YouTube-Kanäle der Marke via SearXNG."""
    results = []
    queries = [
        f"{brand} official youtube channel",
        f"youtube.com/@{brand.lower().replace(' ', '')}",
        f"site:youtube.com/channel {brand} official",
    ]
    for q in queries:
        urls = search_searxng(q)
        for url in urls:
            if "youtube.com/@" in url or "youtube.com/channel/" in url or "youtube.com/user/" in url:
                results.append(url)
    return list(set(results))[:5]

def get_channel_videos(channel_url: str, max_videos: int = 500) -> list:
    """Holt alle Video-URLs eines YouTube-Kanals via yt-dlp."""
    print(f"   📺 Hole Video-Liste von: {channel_url}")
    try:
        cmd = [
            "yt-dlp", "--flat-playlist", "--print", "url",
            "--no-warnings", "--playlist-end", str(max_videos),
            channel_url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        urls = [line.strip() for line in result.stdout.strip().split('\n') if line.strip() and "youtube.com" in line]
        print(f"      → {len(urls)} Videos gefunden")
        return urls
    except Exception as e:
        print(f"      ⚠️ Fehler: {e}")
        return []

def fetch_video_comments_extended(video_url: str, max_comments: int = 10000) -> tuple:
    """
    Holt Kommentare + Metadaten eines Videos.
    Gibt (comments_text, year) zurück.
    """
    import tempfile
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                "yt-dlp", "--write-comments", "--skip-download",
                "--print-json", "--no-warnings",
                "--paths", tmpdir,          # JSON-Dateien ins Temp-Verzeichnis
                "--extractor-args", f"youtube:max_comments={max_comments},max_comment_depth=2",
                video_url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                                   cwd=tmpdir)  # Arbeitsverzeichnis = Temp
            
            comments_text = ""
            year = None
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    # Upload-Jahr extrahieren
                    upload_date = data.get("upload_date", "")
                    if upload_date and len(upload_date) >= 4:
                        year = int(upload_date[:4])
                    
                    # Kommentare extrahieren
                    for comment in data.get("comments", []):
                        text = comment.get("text", "").strip()
                        if text and len(text) > 10:
                            comments_text += f"- {text}\n"
                except:
                    pass
            
            return comments_text[:200000], year
    except:
        return "", None

def scrape_youtube_comprehensive(brand: str, brand_profile: dict = None) -> dict:
    """
    Kompletter YouTube-Sweep: eigene Kanäle + Suche nach Marke.
    Historisch: pro Jahr eigene Queries.
    PARALLEL: ThreadPoolExecutor mit 15 Threads.

    Fallback: Wenn Channel-Discovery < 5 Videos findet, nutze direkte yt-dlp Search.
    """
    print(f"\n   📺 YouTube Comprehensive Sweep für '{brand}'...")

    founding = brand_profile.get("founding_year") if brand_profile else 2015
    all_video_urls = set()
    all_comments = []
    url_meta = {}  # url → year

    # 1. Eigene Kanäle finden
    channels = find_brand_youtube_channels(brand)
    for channel in channels:
        videos = get_channel_videos(channel, max_videos=500)
        all_video_urls.update(videos)

    print(f"   → {len(all_video_urls)} Videos durch Channel-Discovery")

    # 2. Fallback: Wenn < 5 Videos gefunden, nutze direkte yt-dlp Search
    if len(all_video_urls) < 5:
        print(f"   ⚠️ Channel-Discovery ergab nur {len(all_video_urls)} Videos (< 5) → aktiviere yt-dlp Fallback")
        fallback_queries = [
            f"{brand} review",
            f"{brand} erfahrung",
            f"{brand} test",
        ]
        for query in fallback_queries:
            try:
                cmd = [
                    "yt-dlp", f"ytsearch50:{query}", "--get-id"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                video_ids = [line.strip() for line in result.stdout.strip().split('\n') if line.strip() and len(line.strip()) == 11]
                for vid_id in video_ids:
                    all_video_urls.add(f"https://www.youtube.com/watch?v={vid_id}")
                print(f"      → yt-dlp '{query}' fand {len(video_ids)} Videos")
            except Exception as e:
                print(f"      ⚠️ yt-dlp Fallback Fehler für '{query}': {e}")

        print(f"   → {len(all_video_urls)} Videos total nach Fallback")

    # 3. Suche nach Marke auf YouTube - historisch
    search_queries = [
        f"{brand} review",
        f"{brand} test",
        f"{brand} erfahrung",
        f"{brand} vs",
        f"{brand} unboxing",
        f"{brand} honest review",
        f"{brand} kritik",
    ]

    current_year = 2026
    if founding:
        for year in range(founding, current_year + 1):
            year_queries = [f"{brand} {year}", f"{brand} review {year}"]
            for q in year_queries:
                urls = search_searxng(q)
                for url in urls:
                    if "youtube.com/watch" in url:
                        all_video_urls.add(url)

    for q in search_queries:
        urls = search_searxng(q)
        for url in urls:
            if "youtube.com/watch" in url:
                all_video_urls.add(url)

    print(f"   → {len(all_video_urls)} Videos total gefunden")
    
    # 3. Kommentare holen (max 500 Videos, PARALLEL mit 15 Threads)
    video_list = list(all_video_urls)[:500]
    combined_comments = ""
    completed_count = 0
    
    def fetch_with_url(video_url):
        comments, year = fetch_video_comments_extended(video_url, max_comments=2000)
        return video_url, comments, year
    
    print(f"   📥 Hole Kommentare von {len(video_list)} Videos (parallel, 15 threads)...")
    
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(fetch_with_url, url): url for url in video_list}
        for future in as_completed(futures):
            video_url, comments, year = future.result()
            completed_count += 1
            if comments:
                combined_comments += f"\n--- VIDEO {completed_count} ({year or 'unbekannt'}) ---\n{comments}"
                url_meta[video_url] = year
            if completed_count % 50 == 0:
                print(f"      {completed_count}/{len(video_list)} Videos verarbeitet...")
    
    return {
        "comments": combined_comments,
        "video_urls": list(all_video_urls),
        "url_meta": url_meta
    }


# ─── HACKERNEWS ───────────────────────────────────────────────────────────────

def scrape_hackernews(brand: str) -> dict:
    """Scrape HackerNews for brand mentions via Algolia API."""
    urls = []
    text = ""
    base = "https://hn.algolia.com/api/v1"
    for endpoint in [f"/search?query={brand}&tags=story&hitsPerPage=100",
                     f"/search_by_date?query={brand}&tags=story&hitsPerPage=100"]:
        try:
            r = requests.get(f"{base}{endpoint}", timeout=15)
            data = r.json()
            for hit in data.get("hits", []):
                if hit.get("url"):
                    urls.append(hit["url"])
                if hit.get("story_text"):
                    text += hit["story_text"] + "\n"
                if hit.get("comment_text"):
                    text += hit["comment_text"] + "\n"
        except:
            pass
    return {"hn_urls": urls, "hn_text": text}


# ─── REDDIT ─────────────────────────────────────────────────────────────────

def scrape_reddit_comprehensive(brand: str, brand_profile: dict = None) -> dict:
    """
    Kompletter Reddit-Sweep: Search + Subreddits + historisch.
    """
    print(f"\n   👽 Reddit Comprehensive Sweep für '{brand}'...")
    
    headers = {"User-Agent": "BrandResearch/1.0 (Research Project)"}
    founding = brand_profile.get("founding_year") if brand_profile else 2015
    all_text = ""
    post_urls = []
    
    # 1. Direkte Suche nach Marke
    search_queries = [
        brand,
        f"{brand} review",
        f"{brand} experience",
        f"{brand} problem",
        f"{brand} employee",
        f"{brand} ingredient",
    ]
    
    # Competitors ebenfalls suchen
    if brand_profile:
        for comp in brand_profile.get("key_competitors", [])[:3]:
            search_queries.append(f"{brand} vs {comp}")
    
    sort_modes = ["hot", "new", "top", "controversial", "rising"]
    for query in search_queries:
        for sort in sort_modes:
            url = f"https://www.reddit.com/search.json?q={query}&sort={sort}&limit=100&t=all"
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                posts = data.get("data", {}).get("children", [])
                for post in posts:
                    p = post.get("data", {})
                    title = p.get("title", "")
                    body = p.get("selftext", "")[:2000]
                    permalink = p.get("permalink", "")
                    created = p.get("created_utc", 0)
                    
                    if title:
                        all_text += f"[{query}/{sort}] {title}\n{body}\n---\n"
                    if permalink:
                        post_urls.append(f"https://reddit.com{permalink}.json")
                
                time.sleep(0.5)
            except:
                pass
    
    # 2. Historisch: pro Jahr suchen (mit allen sort_modes)
    current_year = 2026
    sort_modes = ["hot", "new", "top", "controversial", "rising"]
    if founding:
        for year in range(founding, current_year + 1):
            for sort in sort_modes:
                url = f"https://www.reddit.com/search.json?q={brand}&sort={sort}&limit=50&t=year"
                try:
                    resp = requests.get(url, headers=headers, timeout=10)
                    data = resp.json()
                    posts = data.get("data", {}).get("children", [])
                    for post in posts:
                        p = post.get("data", {})
                        all_text += f"[{year}/{sort}] {p.get('title', '')}\n{p.get('selftext', '')[:1000]}\n---\n"
                    time.sleep(0.3)
                except:
                    pass
    
    # 3. Kommentare aus Top-Posts holen
    for post_url in post_urls[:50]:
        try:
            resp = requests.get(post_url, headers=headers, timeout=10)
            data = resp.json()
            if isinstance(data, list) and len(data) > 1:
                comments_data = data[1].get("data", {}).get("children", [])
                for comment in comments_data[:20]:
                    c = comment.get("data", {})
                    body = c.get("body", "")
                    if body and body != "[deleted]":
                        all_text += f"KOMMENTAR: {body[:500]}\n"
            time.sleep(0.3)
        except:
            pass
    
    print(f"   → Reddit: {len(all_text)} Zeichen gesammelt")
    return {"text": all_text, "post_urls": post_urls}


def scrape_reddit_pushshift(brand: str, brand_profile: dict = None) -> str:
    """
    Historische Reddit-Daten via PullPush (Pushshift-Nachfolger).
    Findet auch gelöschte Posts und sehr alte Beiträge.
    """
    print(f"\n   👽 Reddit PullPush (historisch) für '{brand}'...")
    
    all_text = ""
    base_url = "https://api.pullpush.io/reddit"
    headers = {"User-Agent": "BrandResearch/1.0"}
    
    search_terms = [brand, f"{brand} review", f"{brand} experience"]
    if brand_profile:
        for comp in brand_profile.get("key_competitors", [])[:2]:
            search_terms.append(f"{brand} {comp}")
    
    for term in search_terms:
        for content_type in ["search/submission", "search/comment"]:
            try:
                params = {
                    "q": term,
                    "size": 100,
                    "sort": "desc",
                    "sort_type": "score"
                }
                resp = requests.get(
                    f"{base_url}/{content_type}/",
                    params=params,
                    headers=headers,
                    timeout=15
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    for item in data:
                        title = item.get("title", "")
                        body = item.get("selftext", item.get("body", ""))[:1000]
                        if title or body:
                            all_text += f"[{term}] {title}\n{body}\n---\n"
                time.sleep(0.3)
            except Exception as e:
                pass
    
    print(f"   → PullPush: {len(all_text)} Zeichen gesammelt")
    return all_text


# ─── TWITTER / X via NITTER ──────────────────────────────────────────────────

def scrape_twitter_via_nitter(brand: str, brand_profile: dict = None) -> tuple:
    """
    Scrapt Twitter/X via Nitter-Mirror (öffentliche Instanz).
    """
    print(f"\n   🐦 Twitter/X via Nitter für '{brand}'...")
    
    nitter_instances = [
        "https://nitter.net",
        "https://nitter.privacydev.net",
        "https://nitter.poast.org",
    ]
    
    all_text = ""
    founding = brand_profile.get("founding_year") if brand_profile else 2015
    
    search_terms = [
        brand,
        f"#{brand.replace(' ', '')}",
        f"@{brand.lower().replace(' ', '')}",
    ]
    
    for instance in nitter_instances[:2]:
        for term in search_terms:
            try:
                url = f"{instance}/search?q={term}&f=tweets"
                resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    from lxml import html as lxml_html
                    tree = lxml_html.fromstring(resp.content)
                    tweets = tree.xpath('//div[@class="tweet-content media-body"]//text()')
                    for tweet in tweets:
                        if tweet.strip():
                            all_text += f"TWEET: {tweet.strip()}\n"
                time.sleep(1)
            except:
                pass
    
    # Zusätzlich via SearXNG OSINT
    osint_queries = [
        f"site:x.com {brand}",
        f"site:twitter.com {brand}",
        f"site:x.com #{brand.replace(' ', '')}",
    ]
    
    osint_urls = []
    for q in osint_queries:
        urls = search_searxng(q)
        osint_urls.extend(urls)
    
    print(f"   → Twitter: {len(all_text)} Zeichen + {len(osint_urls)} OSINT-URLs")
    return all_text, osint_urls


def scrape_twitter_alternatives(brand: str, brand_profile: dict = None) -> tuple:
    """
    Twitter/X Daten via alle verfügbaren öffentlichen Quellen:
    1. Nitter-Mirror-Instanzen (mehrere)
    2. SearXNG OSINT mit vielen Query-Varianten
    3. Tweet-Archiv-Seiten (threader.app, threadreaderapp)
    4. Social-Monitoring-Seiten die Twitter indexieren
    """
    print(f"\n   🐦 Twitter/X Comprehensive für '{brand}'...")
    
    all_text = ""
    all_urls = []
    
    # 1. Nitter — viele Instanzen versuchen
    nitter_instances = [
        "https://nitter.net",
        "https://nitter.privacydev.net",
        "https://nitter.poast.org",
        "https://nitter.1d4.us",
        "https://nitter.kavin.rocks",
        "https://nitter.unixfox.eu",
        "https://nitter.moomoo.me",
        "https://bird.trom.tf",
        "https://nitter.it",
        "https://nitter.nl",
    ]
    
    brand_handle = brand.lower().replace(' ', '')
    search_terms = [
        brand,
        f"#{brand_handle}",
        f"@{brand_handle}",
    ]
    if brand_profile:
        for comp in brand_profile.get("key_competitors", [])[:2]:
            search_terms.append(f"{brand} {comp}")
    
    for instance in nitter_instances:
        success = False
        for term in search_terms[:2]:
            try:
                url = f"{instance}/search?q={term}&f=tweets"
                resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200 and len(resp.content) > 1000:
                    from lxml import html as lxml_html
                    tree = lxml_html.fromstring(resp.content)
                    tweets = tree.xpath('//div[contains(@class,"tweet-content")]//text()')
                    for tweet in tweets:
                        if tweet.strip() and len(tweet.strip()) > 10:
                            all_text += f"TWEET: {tweet.strip()}\n"
                    success = True
                time.sleep(0.5)
            except:
                pass
        if success:
            break  # Funktionierenden Instance gefunden → reicht
    
    # 2. Threadreaderapp — archiviert Twitter-Threads öffentlich
    thread_queries = [
        f"site:threadreaderapp.com {brand}",
        f"site:threadreaderapp.com #{brand_handle}",
    ]
    for q in thread_queries:
        urls = search_searxng(q)
        all_urls.extend(urls)
    
    # 3. Social Searcher und ähnliche Monitoring-Tools
    social_search_queries = [
        f"site:socialsearcher.com {brand}",
        f"site:mentionmapp.com {brand}",
        f'"@{brand_handle}" twitter',
        f'"{brand}" site:twitter.com OR site:x.com',
        f'"{brand}" tweet lang:de',
        f'"{brand}" tweet lang:en',
        f'"{brand}" twitter bewertung',
        f'"{brand}" twitter kritik',
        f'"{brand}" twitter erfahrung',
    ]
    
    for q in social_search_queries:
        urls = search_searxng(q)
        all_urls.extend(urls)
    
    # 4. Wayback Machine für alte Tweets (Twitter wurde archiviert!)
    try:
        params = {
            "url": f"twitter.com/search?q={brand}",
            "output": "json",
            "limit": 20,
            "fl": "original,timestamp",
            "filter": "statuscode:200",
        }
        resp = requests.get("http://web.archive.org/cdx/search/cdx", params=params, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            for row in data[1:]:
                orig_url = row[0]
                timestamp = row[1]
                wb_url = f"https://web.archive.org/web/{timestamp}/{orig_url}"
                all_urls.append(wb_url)
    except:
        pass
    
    print(f"   → Twitter: {len(all_text)} Zeichen direkt + {len(all_urls)} URLs zum Scrapen")
    return all_text, list(set(all_urls))


# ─── TIKTOK ──────────────────────────────────────────────────────────────────

def scrape_tiktok(brand: str) -> tuple:
    """
    TikTok via yt-dlp + SearXNG.
    """
    print(f"\n   🎵 TikTok für '{brand}'...")
    
    tiktok_urls = set()
    all_comments = ""
    
    # URLs via SearXNG finden
    queries = [
        f"site:tiktok.com {brand}",
        f"site:tiktok.com #{brand.replace(' ', '')}",
        f"tiktok {brand} review",
    ]
    
    for q in queries:
        urls = search_searxng(q)
        for url in urls:
            if "tiktok.com" in url:
                tiktok_urls.add(url)
    
    # Kommentare via yt-dlp
    for url in list(tiktok_urls)[:30]:
        try:
            cmd = ["yt-dlp", "--get-comments", "--dump-json", "--no-warnings",
                   "--max-comments", "500", url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    for comment in data.get("comments", []):
                        text = comment.get("text", "").strip()
                        if text:
                            all_comments += f"- {text}\n"
                except:
                    pass
        except:
            pass
    
    print(f"   → TikTok: {len(tiktok_urls)} Videos, {len(all_comments)} Zeichen Kommentare")
    return all_comments, list(tiktok_urls)


def scrape_tiktok_extended(brand: str) -> tuple:
    """
    TikTok via alle verfügbaren öffentlichen Quellen:
    1. yt-dlp für Video-Kommentare (wo möglich)
    2. TikTok-Mirror-Seiten
    3. SearXNG OSINT mit erweiterten Queries
    4. Drittanbieter-Analyse-Seiten die TikTok indexieren
    """
    print(f"\n   🎵 TikTok Extended für '{brand}'...")
    
    tiktok_urls = set()
    all_comments = ""
    brand_handle = brand.lower().replace(' ', '')
    
    # 1. Direkte TikTok URLs via SearXNG
    tiktok_queries = [
        f"site:tiktok.com {brand}",
        f"site:tiktok.com #{brand_handle}",
        f"site:tiktok.com @{brand_handle}",
        f"tiktok {brand} review",
        f"tiktok {brand} erfahrung",
        f"tiktok {brand} test",
        f'"{brand}" tiktok viral',
    ]
    
    for q in tiktok_queries:
        urls = search_searxng(q)
        for url in urls:
            if "tiktok.com" in url:
                tiktok_urls.add(url)
    
    # 2. TikTok Mirror / Analyse-Seiten
    mirror_queries = [
        f"site:tiktokviral.io {brand}",
        f"site:tokcount.com {brand_handle}",
        f"site:exolyt.com {brand_handle}",
        f"site:socialcounts.org tiktok {brand}",
        f"site:analisa.io {brand}",
    ]
    
    mirror_urls = []
    for q in mirror_queries:
        urls = search_searxng(q)
        mirror_urls.extend(urls)
    
    # 3. yt-dlp Kommentare für gefundene Videos
    for url in list(tiktok_urls)[:50]:
        try:
            cmd = ["yt-dlp", "--get-comments", "--dump-json", "--no-warnings",
                   "--max-comments", "200", url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    for comment in data.get("comments", []):
                        text = comment.get("text", "").strip()
                        if text and len(text) > 5:
                            all_comments += f"- {text}\n"
                except:
                    pass
        except:
            pass
    
    all_tiktok_urls = list(tiktok_urls) + mirror_urls
    print(f"   → TikTok: {len(tiktok_urls)} direkte Videos, {len(all_comments)} Zeichen Kommentare, {len(mirror_urls)} Mirror-URLs")
    return all_comments, list(set(all_tiktok_urls))


# ─── INSTAGRAM via öffentliche Alternativen ───────────────────────────────────

def scrape_instagram_osint(brand: str) -> list:
    """
    Instagram via SearXNG OSINT + Picnob/Imginn Mirror.
    """
    print(f"\n   📸 Instagram OSINT für '{brand}'...")
    
    ig_urls = []
    
    # SearXNG OSINT
    queries = [
        f"site:instagram.com {brand}",
        f"site:instagram.com #{brand.replace(' ', '')}",
        f"site:picnob.com {brand}",
        f"site:imginn.com {brand}",
    ]
    
    for q in queries:
        urls = search_searxng(q)
        ig_urls.extend(urls)
    
    # Picnob als öffentlicher Instagram-Mirror
    mirrors = ["https://www.picnob.com", "https://imginn.com"]
    brand_handle = brand.lower().replace(' ', '')
    
    for mirror in mirrors:
        try:
            resp = requests.get(f"{mirror}/{brand_handle}", timeout=10,
                               headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                ig_urls.append(f"{mirror}/{brand_handle}")
        except:
            pass
    
    print(f"   → Instagram: {len(ig_urls)} URLs gefunden")
    return list(set(ig_urls))


def scrape_instagram_extended(brand: str) -> list:
    """
    Instagram via alle verfügbaren öffentlichen Alternativen:
    1. Mehrere Mirror-Seiten
    2. Analyse-Tools die IG indexieren
    3. SearXNG OSINT mit erweiterten Queries
    4. Google-Cache über SearXNG
    """
    print(f"\n   📸 Instagram Extended für '{brand}'...")
    
    ig_urls = []
    brand_handle = brand.lower().replace(' ', '')
    
    # 1. Direkte SearXNG OSINT Queries
    queries = [
        f"site:instagram.com {brand}",
        f"site:instagram.com #{brand_handle}",
        f"site:instagram.com @{brand_handle}",
        f'"{brand}" instagram post',
        f'"{brand}" instagram bewertung',
        f'"{brand}" instagram influencer',
        f'"{brand}" instagram story',
        f'"{brand}" instagram reel',
    ]
    
    for q in queries:
        urls = search_searxng(q)
        ig_urls.extend(urls)
    
    # 2. Öffentliche Mirror und Analyse-Seiten
    mirror_sites = [
        f"https://www.picnob.com/{brand_handle}/",
        f"https://imginn.com/{brand_handle}/",
        f"https://www.instagrammernews.com/search/{brand}",
        f"https://www.instagram-analyzer.com/{brand_handle}",
    ]
    
    mirror_queries = [
        f"site:picnob.com {brand}",
        f"site:imginn.com {brand}",
        f"site:pixwox.com {brand}",
        f"site:storiesig.com {brand}",
        f"site:gramhir.com {brand}",
        f"site:ingramer.com {brand}",
        f"site:analisa.io instagram {brand}",
        f"site:socialblade.com instagram {brand_handle}",
    ]
    
    for q in mirror_queries:
        urls = search_searxng(q)
        ig_urls.extend(urls)
    
    for mirror_url in mirror_sites:
        try:
            resp = requests.get(mirror_url, timeout=8,
                               headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                ig_urls.append(mirror_url)
        except:
            pass
    
    print(f"   → Instagram: {len(set(ig_urls))} URLs gefunden")
    return list(set(ig_urls))


# ─── LINKEDIN ─────────────────────────────────────────────────────────────────

def scrape_linkedin_extended(brand: str) -> list:
    """
    LinkedIn via SearXNG OSINT + öffentliche Analyse-Tools.
    LinkedIn ist stark geblockt — wir nutzen indirekte Quellen.
    """
    print(f"\n   💼 LinkedIn Extended für '{brand}'...")
    
    li_urls = []
    
    queries = [
        f"site:linkedin.com/company {brand}",
        f"site:linkedin.com/posts {brand}",
        f"site:linkedin.com/pulse {brand}",
        f'"{brand}" linkedin employees',
        f'"{brand}" linkedin company culture',
        f'"{brand}" linkedin job review',
        f'"{brand}" linkedin funding',
        f'"{brand}" linkedin CEO',
        f"site:glassdoor.com {brand}",        # Mitarbeiterbewertungen
        f"site:kununu.com {brand}",            # DACH Mitarbeiterbewertungen
        f"site:indeed.com {brand} reviews",
        f"site:trustpilot.com {brand}",        # Kundenbewertungen
        f"site:g2.com {brand}",
    ]
    
    for q in queries:
        urls = search_searxng(q)
        li_urls.extend(urls)
    
    print(f"   → LinkedIn+Reviews: {len(set(li_urls))} URLs gefunden")
    return list(set(li_urls))


# ─── REVIEW PLATFORMS ─────────────────────────────────────────────────────────

def scrape_review_platforms(brand: str) -> list:
    """
    Alle großen Bewertungsplattformen — oft mehr Insights als Social Media.
    """
    print(f"\n   ⭐ Bewertungsplattformen für '{brand}'...")
    
    review_urls = []
    brand_lower = brand.lower().replace(' ', '-')
    
    queries = [
        f"site:trustpilot.com {brand}",
        f"site:trustpilot.com/review {brand}",
        f"site:google.com/maps {brand} bewertung",
        f"site:yelp.com {brand}",
        f"site:amazon.de {brand} bewertung",
        f"site:amazon.com {brand} review",
        f"site:reddit.com {brand} honest review",
        f"site:producthunt.com {brand}",
        f'"{brand}" erfahrungen bewertung test',
        f'"{brand}" customer review negative',
        f'"{brand}" Erfahrungsbericht',
        f'"{brand}" complaint problem',
        f'"{brand}" Kundenservice Kritik',
    ]
    
    for q in queries:
        urls = search_searxng(q)
        review_urls.extend(urls)
    
    print(f"   → Reviews: {len(set(review_urls))} URLs gefunden")
    return list(set(review_urls))


# ─── NEWS & MEDIA ─────────────────────────────────────────────────────────────

def scrape_news_media(brand: str, brand_profile: dict = None) -> list:
    """
    Systematisches News-Crawling: Wirtschaftsmedien, Fachpresse, Blogs.
    """
    print(f"\n   📰 News & Medien Deep-Crawl für '{brand}'...")
    
    news_urls = []
    founding = brand_profile.get("founding_year", 2015) if brand_profile else 2015
    current_year = 2026
    
    # Basis-Queries
    base_queries = [
        f'"{brand}" news',
        f'"{brand}" Pressemitteilung',
        f'"{brand}" interview CEO',
        f'"{brand}" Finanzierung investment',
        f'"{brand}" Marktanteil',
        f'"{brand}" Expansion',
        f'"{brand}" Partnerschaft',
        f'"{brand}" Kritik',
    ]
    
    # Jahres-basierte Queries
    for year in range(founding, current_year + 1):
        base_queries.append(f'"{brand}" {year}')
        base_queries.append(f'"{brand}" news {year}')
    
    # Fachmedien
    media_queries = [
        f"site:lebensmittelzeitung.de {brand}",
        f"site:handelsblatt.com {brand}",
        f"site:manager-magazin.de {brand}",
        f"site:gruenderszene.de {brand}",
        f"site:t3n.de {brand}",
        f"site:wired.com {brand}",
        f"site:businessinsider.com {brand}",
        f"site:techcrunch.com {brand}",
    ]
    
    for q in base_queries + media_queries:
        urls = search_searxng(q)
        news_urls.extend(urls)
    
    print(f"   → News: {len(set(news_urls))} URLs gefunden")
    return list(set(news_urls))


# ─── HAUPTFUNKTION ───────────────────────────────────────────────────────────

def run_social_agent(brand: str, note: str, baseline: str, brand_profile: dict = None) -> dict:
    """
    Kompletter Social Media + Web Sweep — alle verfügbaren Quellen.
    """
    print(f"\n💬 [PHASE 2] Starte OMNI-CHANNEL Social Extraction für '{brand}'...")
    
    social_data = {
        "youtube_comments": "",
        "youtube_urls": [],
        "reddit_text": "",
        "reddit_urls": [],
        "twitter_text": "",
        "tiktok_comments": "",
        "tiktok_urls": [],
        "instagram_urls": [],
        "linkedin_urls": [],
        "review_urls": [],
        "news_urls": [],
        "osint_urls": [],
        "url_meta": {},
        "hn_text": ""
    }
    
    # 1. YouTube (parallel)
    yt_result = scrape_youtube_comprehensive(brand, brand_profile)
    social_data["youtube_comments"] = yt_result["comments"]
    social_data["youtube_urls"] = yt_result["video_urls"]
    social_data["url_meta"].update(yt_result["url_meta"])
    
    # 2. Reddit (API + PullPush historisch)
    reddit_result = scrape_reddit_comprehensive(brand, brand_profile)
    social_data["reddit_text"] = reddit_result["text"]
    social_data["reddit_urls"] = reddit_result["post_urls"]
    
    pushshift_text = scrape_reddit_pushshift(brand, brand_profile)
    social_data["reddit_text"] += pushshift_text
    
    # 3. Twitter/X (alle Alternativen)
    twitter_text, twitter_urls = scrape_twitter_alternatives(brand, brand_profile)
    social_data["twitter_text"] = twitter_text
    social_data["osint_urls"].extend(twitter_urls)
    
    # 4. TikTok (extended)
    tiktok_comments, tiktok_urls = scrape_tiktok_extended(brand)
    social_data["tiktok_comments"] = tiktok_comments
    social_data["tiktok_urls"] = tiktok_urls
    
    # 5. Instagram (extended)
    ig_urls = scrape_instagram_extended(brand)
    social_data["instagram_urls"] = ig_urls
    social_data["osint_urls"].extend(ig_urls)
    
    # 6. LinkedIn + Bewertungsplattformen (NEU)
    li_urls = scrape_linkedin_extended(brand)
    social_data["linkedin_urls"] = li_urls
    social_data["osint_urls"].extend(li_urls)
    
    # 7. Bewertungsplattformen (NEU)
    review_urls = scrape_review_platforms(brand)
    social_data["review_urls"] = review_urls
    social_data["osint_urls"].extend(review_urls)
    
    # 8. News & Medien (NEU)
    news_urls = scrape_news_media(brand, brand_profile)
    social_data["news_urls"] = news_urls
    social_data["osint_urls"].extend(news_urls)
    
    # 9. HackerNews (NEU)
    hn_data = scrape_hackernews(brand)
    social_data["hn_text"] = hn_data.get("hn_text", "")
    
    # Stats
    total_text = (len(social_data["youtube_comments"]) + 
                  len(social_data["reddit_text"]) + 
                  len(social_data["twitter_text"]) +
                  len(social_data["tiktok_comments"]))
    total_urls = (len(social_data["youtube_urls"]) + 
                  len(social_data["reddit_urls"]) + 
                  len(social_data["tiktok_urls"]) + 
                  len(social_data["instagram_urls"]) +
                  len(social_data["linkedin_urls"]) +
                  len(social_data["review_urls"]) +
                  len(social_data["news_urls"]))
    print(f"\n✅ Social Sweep komplett: {total_text:,} Zeichen Text, {total_urls:,} URLs")
    
    return social_data
