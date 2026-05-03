"""
verify_searxng.py — Verifies that social scrapers handle empty SearXNG results gracefully.

Usage:
    python3 verify_searxng.py

Exit code 0 = all tests passed.
Exit code 1 = one or more tests failed.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import patch
from agents.agent_social import (
    scrape_reddit_comprehensive,
    scrape_tiktok_extended,
    scrape_twitter_alternatives,
    scrape_instagram_extended,
    scrape_linkedin_extended,
    scrape_review_platforms,
    scrape_news_media,
    find_brand_youtube_channels,
    scrape_youtube_comprehensive,
)

# Brand guaranteed to return no results from SearXNG
TEST_BRAND = "ObscureBrandTest99999"

# Collect results
failures = []

def check(name, fn, *args, **kwargs):
    try:
        result = fn(*args, **kwargs)
        if result is None:
            failures.append(f"FAIL: {name} returned None")
        else:
            print(f"  PASS: {name} returned {type(result).__name__} (no crash)")
    except Exception as e:
        failures.append(f"FAIL: {name} raised {type(e).__name__}: {e}")


# Patch search_searxng to always return empty list
with patch("agents.agent_social.search_searxng", return_value=[]):
    print(f"\n--- Testing with search_searxng → [] (brand='{TEST_BRAND}') ---\n")

    check("find_brand_youtube_channels", find_brand_youtube_channels, TEST_BRAND)
    check("scrape_youtube_comprehensive", scrape_youtube_comprehensive, TEST_BRAND)
    check("scrape_reddit_comprehensive", scrape_reddit_comprehensive, TEST_BRAND)
    check("scrape_tiktok_extended", scrape_tiktok_extended, TEST_BRAND)
    check("scrape_twitter_alternatives", scrape_twitter_alternatives, TEST_BRAND)
    check("scrape_instagram_extended", scrape_instagram_extended, TEST_BRAND)
    check("scrape_linkedin_extended", scrape_linkedin_extended, TEST_BRAND)
    check("scrape_review_platforms", scrape_review_platforms, TEST_BRAND)
    check("scrape_news_media", scrape_news_media, TEST_BRAND)

# Patch search_searxng to return None (edge case: malformed JSON response)
with patch("agents.agent_social.search_searxng", return_value=None):
    print(f"\n--- Testing with search_searxng → None (brand='{TEST_BRAND}') ---\n")

    check("find_brand_youtube_channels (None)", find_brand_youtube_channels, TEST_BRAND)
    check("scrape_youtube_comprehensive (None)", scrape_youtube_comprehensive, TEST_BRAND)
    check("scrape_tiktok_extended (None)", scrape_tiktok_extended, TEST_BRAND)
    check("scrape_twitter_alternatives (None)", scrape_twitter_alternatives, TEST_BRAND)
    check("scrape_instagram_extended (None)", scrape_instagram_extended, TEST_BRAND)
    check("scrape_linkedin_extended (None)", scrape_linkedin_extended, TEST_BRAND)
    check("scrape_review_platforms (None)", scrape_review_platforms, TEST_BRAND)
    check("scrape_news_media (None)", scrape_news_media, TEST_BRAND)


print(f"\n{'='*50}")
if failures:
    print(f"\n{len(failures)} failure(s):")
    for f in failures:
        print(f"  {f}")
    sys.exit(1)
else:
    print("\nAll tests passed — scrapers handle empty/None SearXNG results gracefully.")
    sys.exit(0)
