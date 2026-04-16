import os
import sys
import time
import re
import sqlite3
import asyncio
from curl_cffi import requests as curl_requests
from curl_cffi.requests import AsyncSession
from lxml import html as lxml_html

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def extract_clean_text(html_bytes: bytes) -> str:
    """
    Extrahiert sauberen Text aus HTML.
    Entfernt script, style, noscript, header, footer, nav.
    PDF-Dateien werden erkannt und ignoriert.
    """
    if html_bytes.startswith(b'%PDF'):
        return ""
    try:
        tree = lxml_html.fromstring(html_bytes)
        for bad in tree.xpath('//script | //style | //noscript | //header | //footer | //nav'):
            bad.getparent().remove(bad)
        clean_text = tree.text_content()
        return re.sub(r'\s+', ' ', clean_text).strip()
    except:
        return ""


def init_url_queue(db_path: str) -> sqlite3.Connection:
    """
    TASK 2a: SQLite URL-Queue initialisieren.
    Erstellt SQLite DB mit zwei Tabellen:
    - urls(id, url UNIQUE, status DEFAULT 'pending', scraped_at, chunk_count, error, source_type, year, language, priority, paywall_bypassed)
    - chunks(id, url, content, char_count, source_type, year, language)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # URLs-Tabelle
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'pending',
            scraped_at TEXT,
            chunk_count INTEGER DEFAULT 0,
            error TEXT,
            source_type TEXT DEFAULT 'web',
            year INTEGER,
            language TEXT DEFAULT 'de',
            priority INTEGER DEFAULT 5,
            paywall_bypassed INTEGER DEFAULT 0
        )
    ''')
    
    # Chunks-Tabelle
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            content TEXT NOT NULL,
            char_count INTEGER NOT NULL,
            source_type TEXT DEFAULT 'web',
            year INTEGER,
            language TEXT DEFAULT 'de'
        )
    ''')
    
    conn.commit()
    return conn


def add_urls_to_queue(conn: sqlite3.Connection, urls: list, source_type: str = 'web', year: int = None, language: str = 'de', priority: int = 5):
    """
    TASK 2a: URLs zur Queue hinzufügen.
    INSERT OR IGNORE um Doppelte zu vermeiden.
    """
    cursor = conn.cursor()
    for url in urls:
        try:
            cursor.execute(
                'INSERT OR IGNORE INTO urls (url, status, source_type, year, language, priority) VALUES (?, ?, ?, ?, ?, ?)',
                (url, 'pending', source_type, year, language, priority)
            )
        except Exception:
            pass
    conn.commit()


def get_pending_urls(conn: sqlite3.Connection) -> list:
    """
    TASK 2a: Hole alle ausstehenden URLs.
    SELECT WHERE status='pending'
    """
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM urls WHERE status='pending'")
    return [row[0] for row in cursor.fetchall()]


async def scrape_url(session: AsyncSession, url: str, semaphore: asyncio.Semaphore) -> tuple:
    """
    TASK 2b: Async Scraper.
    scrape_url(session, url, semaphore) als async def:
    - async with semaphore
    - await session.get(url, timeout=25)
    - PDF check: if content.startswith(b'%PDF') → return url, "", "PDF skipped"
    - lxml cleanup wie bisher (script/style/nav/header/footer entfernen)
    - text_content() extrahieren, whitespace normalisieren
    - Wenn len < 200 → return url, "", "too short"
    - return url, clean_text[:60000], ""
    - Retry bei Timeout mit 5s Pause
    """
    async with semaphore:
        for attempt in range(2):
            try:
                response = await session.get(url, timeout=25)
                
                # PDF check
                if response.content.startswith(b'%PDF'):
                    return url, "", "PDF skipped"
                
                # lxml cleanup
                clean_text = extract_clean_text(response.content)
                
                # Wenn len < 200
                if len(clean_text) < 200:
                    return url, "", "too short"
                
                return url, clean_text[:60000], ""
                
            except Exception as e:
                if attempt == 0 and "timeout" in str(e).lower():
                    await asyncio.sleep(5)
                    continue
                return url, "", str(e)
        return url, "", "max retries"


def chunk_text(text: str, chunk_size: int = 1500, min_chunk: int = 200) -> list:
    """
    TASK 2b: Text in Chunks aufteilen.
    Chunk-Size: 1500 Zeichen, min. 200 Zeichen pro Chunk
    """
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size].strip()
        if len(chunk) >= min_chunk:
            chunks.append(chunk)
    return chunks


async def run_mass_scraper_async(urls: list, save_dir: str, concurrent: int = 30):
    """
    TASK 2b: Async Mass-Scraper.
    run_mass_scraper_async(urls, save_dir, concurrent=30):
    - init_url_queue in save_dir/url_queue.sqlite
    - add_urls_to_queue mit allen URLs
    - pending URLs holen
    - asyncio.Semaphore(concurrent)
    - async with AsyncSession(impersonate="chrome110") as session
    - alle Tasks mit asyncio.as_completed abarbeiten
    - Ergebnisse nach je 50 URLs in DB committen
    - Bei done: Chunks in DB speichern UND als url_*.txt Datei speichern (für STORM-Kompatibilität mit glob)
    - Chunk-Size: 1500 Zeichen, min. 200 Zeichen pro Chunk
    - Am Ende Stats ausgeben: done/failed/skipped counts + total chunks
    """
    print(f"\n🕷️ [PHASE 3] Starte Mass-Scraping (Data Lake Building, ASYNC)...")
    
    db_path = os.path.join(save_dir, "url_queue.sqlite")
    os.makedirs(save_dir, exist_ok=True)
    
    # Init DB
    conn = init_url_queue(db_path)
    add_urls_to_queue(conn, urls)
    
    # Hole pending URLs
    pending_urls = get_pending_urls(conn)
    
    if not pending_urls:
        print("   ⚠️ Keine URLs in der Queue.")
        return
    
    print(f"   📋 {len(pending_urls)} URLs in der Queue.")
    
    semaphore = asyncio.Semaphore(concurrent)
    stats = {"done": 0, "failed": 0, "skipped": 0}
    total_chunks = 0
    processed_count = 0
    completed = 0
    
    async with AsyncSession(impersonate="chrome110") as session:
        tasks = [scrape_url(session, url, semaphore) for url in pending_urls]
        
        for task in asyncio.as_completed(tasks):
            url, content, error = await task
            
            # DB Update
            cursor = conn.cursor()
            if error:
                if "PDF skipped" in error:
                    stats["skipped"] += 1
                    cursor.execute("UPDATE urls SET status='skipped', error=? WHERE url=?", (error, url))
                elif "too short" in error:
                    stats["skipped"] += 1
                    cursor.execute("UPDATE urls SET status='skipped', error=? WHERE url=?", (error, url))
                else:
                    stats["failed"] += 1
                    cursor.execute("UPDATE urls SET status='failed', error=? WHERE url=?", (error, url))
            else:
                stats["done"] += 1
                cursor.execute("UPDATE urls SET status='done', scraped_at=datetime('now') WHERE url=?", (url,))
            
            # Chunks speichern
            if content:
                # source_type und year aus urls-Tabelle holen
                url_meta = conn.execute("SELECT source_type, year, language FROM urls WHERE url=?", (url,)).fetchone()
                src_type = url_meta[0] if url_meta else 'web'
                src_year = url_meta[1] if url_meta else None
                src_lang = url_meta[2] if url_meta else 'de'
                
                chunks = chunk_text(content)
                for chunk in chunks:
                    cursor.execute("INSERT INTO chunks (url, content, char_count, source_type, year, language) VALUES (?, ?, ?, ?, ?, ?)",
                                   (url, chunk, len(chunk), src_type, src_year, src_lang))
                    total_chunks += 1
                
                # url_*.txt Datei speichern (für STORM-Kompatibilität)
                safe_name = re.sub(r'[^a-zA-Z0-9]', '_', url)[-30:]
                txt_path = os.path.join(save_dir, f"url_{processed_count+1}_{safe_name}.txt")
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(f"URL: {url}\n\n{content}")
                
                processed_count += 1
            
            # Nach je 50 URLs in DB committen
            completed += 1
            if completed % 50 == 0:
                conn.commit()
        
        conn.commit()
    
    conn.close()
    
    print(f"\n✅ Mass-Scraping abgeschlossen!")
    print(f"   📊 Stats: done={stats['done']}, failed={stats['failed']}, skipped={stats['skipped']}")
    print(f"   📦 Total Chunks: {total_chunks}")


async def run_mass_scraper(urls: list, save_dir: str):
    """
    FIX: run_mass_scraper auf async def umgestellt.
    asyncio.run() ersetzt durch await.
    """
    return await run_mass_scraper_async(urls, save_dir, concurrent=30)


def run_mass_scraper_sync(urls: list, save_dir: str):
    """
    TASK 2b: Alte sync Funktion als Fallback.
    Behält die alte Funktion als run_mass_scraper_sync für Fallback.
    """
    print(f"\n🕷️ [PHASE 3] Starte Mass-Scraping (Data Lake Building, SYNC)...")
    
    urls_to_crawl = list(set(urls))
    
    for idx, url in enumerate(urls_to_crawl):
        print(f"   ⬇️ [{idx+1}/{len(urls_to_crawl)}] Lade Text von: {url}")
        try:
            response = curl_requests.get(url, impersonate="chrome110", timeout=10)
            text_content = extract_clean_text(response.content)[:60000]
            
            if len(text_content) < 200:
                continue
            
            safe_name = re.sub(r'[^a-zA-Z0-9]', '_', url)[-30:]
            with open(os.path.join(save_dir, f"url_{idx+1}_{safe_name}.txt"), "w", encoding="utf-8") as f:
                f.write(f"URL: {url}\n\n{text_content}")
                
        except Exception:
            pass
        time.sleep(1)  # Kurze Anti-Ban Pause
