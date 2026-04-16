# Token Usage Tracker

A tool for tracking Lemonade Server token usage.

## Usage

```bash
# Show today's usage (falls back to API stats if no journalctl data)
python3 token_tracker.py --today

# Show this week's usage
python3 token_tracker.py --week

# Show all-time usage
python3 token_tracker.py --all

# Export data to JSON
python3 token_tracker.py --export

# Show only API stats (no journalctl parsing)
python3 token_tracker.py --api-only
```

## Output Format

```
=== NeuroAd Token Usage ===

  HEUTE (15. Apr 2026)

  Input:   1,234,567 tokens
  Output:    456,789 tokens
  Avg TPS:        10.8
  Calls:          15

  GESAMT (alle Zeit)

  Input:   5,234,567 tokens
  Output:  1,456,789 tokens
  Avg TPS:        12.3
  Calls:         150

  TOP MODELLE

  Gemma 4 31B:    800k in / 300k out
  DeepSeek R1:    400k in / 150k out
```

## Journalctl Telemetry Format

The script parses journalctl entries with the following format:
```
Telemetry: Input tokens: 123 Output tokens: 45 TPS: 10.5
```

If no Telemetry lines are found, the script falls back to the current API stats.

## Cron Usage

Add to crontab for automatic tracking:

```
# Hourly token usage log
0 * * * * cd ~/neuro_pipeline_project && source venv_rocm/bin/activate && python3 tools/token_tracker.py --today >> tools/token_usage.log 2>&1
```
