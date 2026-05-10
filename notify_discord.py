#!/usr/bin/env python3
import sys
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path.home() / ".hermes" / ".env")

DISCORD_TOKEN=os.getenv("DISCORD_BOT_TOKEN") or os.getenv("DISCORD_TOKEN") or ""
CHANNEL_ID = os.getenv("DISCORD_HOME_CHANNEL") or os.getenv("DISCORD_CHANNEL_ID") or ""

def notify(message: str):
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }
    r = requests.post(
        f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages",
        headers=headers,
        json={"content": message}
    )
    return r.status_code

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "Pipeline run completed."
    status = notify(msg)
    print(f"Discord notification sent (HTTP {status})")
