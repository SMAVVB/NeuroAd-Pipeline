#!/usr/bin/env python3
"""
Token Usage Tracker for Lemonade Server
Analyzes Lemonade logs and provides token usage statistics.

Primary data source: ~/.lemonade_token_log.jsonl (Lemonade middleware logging)
Fallback: /api/v1/stats (current API stats)
"""

import argparse
import json
import os
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


# Paths
CACHE_DIR = Path("/home/vincent/neuro_pipeline_project/tools")
USAGE_FILE = CACHE_DIR / "token_usage.json"
TOKEN_LOG_FILE = Path.home() / ".lemonade_token_log.jsonl"

# Regex patterns for parsing journalctl Telemetry lines (fallback)
TELEMETRY_PATTERN = re.compile(
    r'.*Input tokens:\s*(\d+).*Output tokens:\s*(\d+).*TPS:\s*([\d.]+).*',
    re.IGNORECASE
)

# Model name patterns for classification
MODEL_PATTERNS = {
    "Gemma 4 31B": [r"gemma.*4.*31b", r"gemma-4-31b"],
    "DeepSeek R1": [r"deepseek.*r\d", r"deepseek-r\d"],
    "Kimi": [r"kimi"],
    "Qwen": [r"qwen", r"Qwen"],
    "Llama": [r"llama", r"llamacpp"],
}

# Approximate costs per 1M tokens (USD) for cost estimation
# Source: https://openai.com/pricing, https://deepseek.com/pricing
MODEL_COSTS = {
    "Gemma 4 31B": {"input": 0.60, "output": 0.60},   # Estimate based on similar models
    "DeepSeek R1": {"input": 0.14, "output": 0.28},    # DeepSeek R1 pricing
    "Kimi": {"input": 0.40, "output": 1.20},           # Kimi 14B pricing estimate
    "Qwen": {"input": 0.20, "output": 0.20},           # Qwen pricing estimate
    "Llama": {"input": 0.30, "output": 0.30},          # Llama pricing estimate
    "Unknown": {"input": 0.00, "output": 0.00},
}


def parse_jsonl_log_file() -> list[dict]:
    """Parse the .lemonade_token_log.jsonl file for all logged calls."""
    results = []

    if not TOKEN_LOG_FILE.exists():
        return results

    try:
        with open(TOKEN_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        # Validate required fields
                        if "timestamp" in entry and "input_tokens" in entry and "output_tokens" in entry:
                            results.append(entry)
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"Warning: Could not parse token log file: {e}")

    return results


def parse_journalctl_line(line: str) -> dict | None:
    """Parse a single journalctl JSON line for telemetry data (fallback)."""
    try:
        entry = json.loads(line)

        # Check if this is a Telemetry entry
        msg = entry.get("MESSAGE", "") or ""
        if "Telemetry" not in msg and "Input tokens" not in msg:
            return None

        # Extract timestamp
        ts_str = entry.get("_SOURCE_REALTIME_TIMESTAMP", entry.get("__REALTIME_TIMESTAMP", 0))
        if isinstance(ts_str, str):
            ts_str = ts_str.split(".")[0]
        timestamp = datetime.fromtimestamp(int(ts_str))

        # Try to extract tokens from message
        input_match = re.search(r'Input tokens?:\s*(\d+)', msg, re.IGNORECASE)
        output_match = re.search(r'Output tokens?:\s*(\d+)', msg, re.IGNORECASE)
        tps_match = re.search(r'TPS:?\s*([\d.]+)', msg, re.IGNORECASE)

        if input_match and output_match:
            return {
                "timestamp": timestamp,
                "input_tokens": int(input_match.group(1)),
                "output_tokens": int(output_match.group(1)),
                "tps": float(tps_match.group(1)) if tps_match else None,
            }
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    return None


def get_model_from_path(path: str) -> str:
    """Determine model name from file path."""
    path_lower = path.lower()
    for model_name, patterns in MODEL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, path_lower):
                return model_name
    return "Unknown"


def fetch_api_stats() -> dict:
    """Fetch current stats from Lemonade API."""
    try:
        response = subprocess.run(
            ["curl", "-s", "http://localhost:8888/api/v1/stats"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if response.returncode == 0:
            return json.loads(response.stdout)
    except Exception:
        pass
    return {}


def parse_journalctl_data() -> list[dict]:
    """Parse all journalctl data for Lemonade (fallback)."""
    results = []

    try:
        result = subprocess.run(
            ["journalctl", "-u", "lemonade-server", "-o", "json", "--since", "today"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if line:
                    parsed = parse_journalctl_line(line)
                    if parsed:
                        results.append(parsed)

    except subprocess.TimeoutExpired:
        print("Warning: journalctl command timed out")
    except Exception as e:
        print(f"Warning: Could not parse journalctl: {e}")

    return results


def load_cached_usage() -> dict:
    """Load previously cached usage data."""
    if USAGE_FILE.exists():
        try:
            with open(USAGE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_cached_usage(data: dict):
    """Save usage data to cache."""
    try:
        USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(USAGE_FILE, "w") as f:
            json.dump(data, f, indent=2, default=str)
    except IOError as e:
        print(f"Warning: Could not save cache: {e}")


def get_model_display_name(model_name: str) -> str:
    """Extract model display name from model filename or path."""
    model_lower = model_name.lower()

    # Check against known patterns
    for model_display, patterns in MODEL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, model_lower):
                return model_display

    # Try to extract from path
    if "/" in model_name:
        model_lower = model_name.lower()
        for model_display, patterns in MODEL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, model_lower):
                    return model_display

    return "Unknown"


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate estimated cost in USD based on model and tokens."""
    costs = MODEL_COSTS.get(model, MODEL_COSTS["Unknown"])
    input_cost = (input_tokens / 1_000_000) * costs["input"]
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    return input_cost + output_cost


def classify_call(entry: dict) -> dict:
    """Classify a call and determine model from entry."""
    model_name = entry.get("model", "")

    # Extract model name for display
    model_display = get_model_display_name(model_name)

    # Calculate estimated cost
    input_tokens = entry.get("input_tokens", 0)
    output_tokens = entry.get("output_tokens", 0)
    estimated_cost = calculate_cost(model_display, input_tokens, output_tokens)

    return {
        **entry,
        "model": model_display,
        "estimated_cost": estimated_cost,
    }


def calculate_stats(entries: list[dict]) -> dict:
    """Calculate aggregated statistics from entries."""
    if not entries:
        return {
            "today": {"input": 0, "output": 0, "tps": [], "calls": 0, "cost": 0.0},
            "week": {"input": 0, "output": 0, "tps": [], "calls": 0, "cost": 0.0},
            "total": {"input": 0, "output": 0, "tps": [], "calls": 0, "cost": 0.0},
            "by_model": defaultdict(lambda: {"input": 0, "output": 0, "cost": 0.0}),
            "by_project": defaultdict(lambda: {"input": 0, "output": 0, "cost": 0.0}),
        }

    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())

    stats = {
        "today": {"input": 0, "output": 0, "tps": [], "calls": 0, "cost": 0.0},
        "week": {"input": 0, "output": 0, "tps": [], "calls": 0, "cost": 0.0},
        "total": {"input": 0, "output": 0, "tps": [], "calls": len(entries), "cost": 0.0},
        "by_model": defaultdict(lambda: {"input": 0, "output": 0, "cost": 0.0}),
        "by_project": defaultdict(lambda: {"input": 0, "output": 0, "cost": 0.0}),
        "top_calls": [],
    }

    for entry in entries:
        # Parse timestamp
        ts_str = entry.get("timestamp", "")
        try:
            timestamp = datetime.fromisoformat(ts_str.replace('Z', '+00:00')).replace(tzinfo=None)
        except (ValueError, TypeError):
            timestamp = today

        date = timestamp.date() if hasattr(timestamp, "date") else today

        input_tokens = entry.get("input_tokens", 0)
        output_tokens = entry.get("output_tokens", 0)
        tps = entry.get("tps")
        project = entry.get("project", "unknown")
        model = entry.get("model", "Unknown")

        # Calculate estimated cost
        estimated_cost = calculate_cost(model, input_tokens, output_tokens)

        # Total
        stats["total"]["input"] += input_tokens
        stats["total"]["output"] += output_tokens
        stats["total"]["cost"] += estimated_cost
        if tps:
            stats["total"]["tps"].append(tps)

        # Today
        if date == today:
            stats["today"]["input"] += input_tokens
            stats["today"]["output"] += output_tokens
            stats["today"]["cost"] += estimated_cost
            if tps:
                stats["today"]["tps"].append(tps)
            stats["today"]["calls"] += 1

        # This week
        if date >= week_start:
            stats["week"]["input"] += input_tokens
            stats["week"]["output"] += output_tokens
            stats["week"]["cost"] += estimated_cost
            if tps:
                stats["week"]["tps"].append(tps)
            stats["week"]["calls"] += 1

        # By model
        stats["by_model"][model]["input"] += input_tokens
        stats["by_model"][model]["output"] += output_tokens
        stats["by_model"][model]["cost"] += estimated_cost

        # By project
        stats["by_project"][project]["input"] += input_tokens
        stats["by_project"][project]["output"] += output_tokens
        stats["by_project"][project]["cost"] += estimated_cost

        # Track top calls
        total_tokens = input_tokens + output_tokens
        stats["top_calls"].append({
            "timestamp": timestamp,
            "input": input_tokens,
            "output": output_tokens,
            "total": total_tokens,
            "model": model,
            "project": project,
            "cost": estimated_cost,
        })

    # Sort top calls and keep top 10
    stats["top_calls"].sort(key=lambda x: x["total"], reverse=True)
    stats["top_calls"] = stats["top_calls"][:10]

    # Calculate averages
    for period in ["today", "week", "total"]:
        if stats[period]["tps"]:
            stats[period]["avg_tps"] = sum(stats[period]["tps"]) / len(stats[period]["tps"])
        else:
            stats[period]["avg_tps"] = 0.0

    return stats


def format_number(n: int) -> str:
    """Format number with thousands separators."""
    return f"{n:,}"


def format_cost(c: float) -> str:
    """Format cost with 4 decimal places."""
    return f"${c:.4f}"


def print_stats(stats: dict):
    """Print formatted statistics to terminal."""
    today_date = datetime.now().strftime("%d. %b %Y")

    print()
    print("=== NeuroAd Token Usage ===")
    print()

    # Today
    print(f"  HEUTE ({today_date})")
    print()
    print(f"  Input:   {format_number(stats['today']['input'])} tokens")
    print(f"  Output:  {format_number(stats['today']['output'])} tokens")
    print(f"  Avg TPS: {stats['today']['avg_tps']:.1f}")
    print(f"  Calls:   {stats['today']['calls']}")
    print(f"  Cost:    {format_cost(stats['today']['cost'])}")
    print()

    # This week
    print(f"  DIESE WOCHE")
    print()
    print(f"  Input:   {format_number(stats['week']['input'])} tokens")
    print(f"  Output:  {format_number(stats['week']['output'])} tokens")
    print(f"  Avg TPS: {stats['week']['avg_tps']:.1f}")
    print(f"  Calls:   {stats['week']['calls']}")
    print(f"  Cost:    {format_cost(stats['week']['cost'])}")
    print()

    # Total
    print("  GESAMT (alle Zeit)")
    print()
    print(f"  Input:   {format_number(stats['total']['input'])} tokens")
    print(f"  Output:  {format_number(stats['total']['output'])} tokens")
    print(f"  Avg TPS: {stats['total']['avg_tps']:.1f}")
    print(f"  Calls:   {stats['total']['calls']}")
    print(f"  Cost:    {format_cost(stats['total']['cost'])}")
    print()

    # Top models
    print("  TOP MODELLE")
    print()

    # Sort models by total cost
    sorted_models = sorted(
        stats["by_model"].items(),
        key=lambda x: x[1]["cost"],
        reverse=True
    )

    for model, data in sorted_models:
        if data["input"] > 0 or data["output"] > 0:
            print(f"  {model}: {format_number(data['input'])} in / {format_number(data['output'])} out / {format_cost(data['cost'])}")

    # Top projects
    print()
    print("  TOP PROJECTS")
    print()

    sorted_projects = sorted(
        stats["by_project"].items(),
        key=lambda x: x[1]["cost"],
        reverse=True
    )

    for project, data in sorted_projects:
        if data["input"] > 0 or data["output"] > 0:
            print(f"  {project}: {format_number(data['input'])} in / {format_number(data['output'])} out / {format_cost(data['cost'])}")

    # Top calls
    if stats["top_calls"]:
        print()
        print("  TEUERSTE CALLS (Top 10)")
        print()
        for call in stats["top_calls"]:
            ts = call["timestamp"].strftime("%d. %b %H:%M") if hasattr(call["timestamp"], "strftime") else str(call["timestamp"])
            print(f"  {ts} - {format_number(call['total'])} tokens ({call['model']}) [{call['project']}] - {format_cost(call['cost'])}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Token Usage Tracker for Lemonade Server"
    )
    parser.add_argument(
        "--today",
        action="store_true",
        help="Show only today's usage"
    )
    parser.add_argument(
        "--week",
        action="store_true",
        help="Show only this week's usage"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all-time usage"
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export data to JSON file"
    )
    parser.add_argument(
        "--api-only",
        action="store_true",
        help="Use only API stats (no log file parsing)"
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Show raw log file contents for debugging"
    )

    args = parser.parse_args()

    # Fetch API stats for reference
    api_stats = fetch_api_stats()

    if args.api_only or args.export:
        # Just show current API stats
        print()
        print("=== NeuroAd Token Usage (API Stats) ===")
        print()
        if api_stats:
            print(f"  Input tokens:  {api_stats.get('input_tokens', 0)}")
            print(f"  Output tokens: {api_stats.get('output_tokens', 0)}")
            print(f"  TPS:           {api_stats.get('tokens_per_second', 0):.1f}")
        else:
            print("  Could not fetch API stats - is Lemonade running?")
        print()
        return

    # Show raw log file if requested
    if args.raw:
        print()
        print("=== Raw Token Log ===")
        print()
        if not TOKEN_LOG_FILE.exists():
            print("  No token log file found.")
        else:
            try:
                with open(TOKEN_LOG_FILE, "r", encoding="utf-8") as f:
                    lines = f.readlines()[-20:]  # Last 20 lines
                    for line in lines:
                        print(line.strip())
            except Exception as e:
                print(f"  Error reading log file: {e}")
        print()
        return

    # Parse log file (primary data source)
    entries = parse_jsonl_log_file()

    if not entries:
        print()
        print("=== NeuroAd Token Usage ===")
        print()
        print("  No token log data found in ~/.lemonade_token_log.jsonl")
        print("  Lemonade middleware logging might not be active.")

        # Show API stats as fallback
        if api_stats:
            print()
            print("  Current API Stats (fallback):")
            print(f"    Input tokens:  {api_stats.get('input_tokens', 0)}")
            print(f"    Output tokens: {api_stats.get('output_tokens', 0)}")
            print(f"    TPS:           {api_stats.get('tokens_per_second', 0):.1f}")

        # Check for journalctl fallback
        journal_entries = parse_journalctl_data()
        if journal_entries:
            print()
            print(f"  Found {len(journal_entries)} entries via journalctl fallback.")

        print()
        return

    # Classify entries by model and project
    for entry in entries:
        classify_call(entry)

    # Calculate statistics
    stats = calculate_stats(entries)

    # Save to cache if requested or if we have data
    if args.export:
        save_cached_usage({"last_updated": datetime.now().isoformat(), "stats": stats})
        print(f"Data exported to {USAGE_FILE}")
        print()

    # Print statistics
    print_stats(stats)


if __name__ == "__main__":
    main()
