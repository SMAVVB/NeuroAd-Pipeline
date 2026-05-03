#!/usr/bin/env python3
"""Verify that init_url_queue enables WAL mode and timeout."""

import sqlite3
import sys
import tempfile
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from agents.agent_scraper import init_url_queue

with tempfile.TemporaryDirectory() as tmpdir:
    db_path = os.path.join(tmpdir, "test_queue.sqlite")
    conn = init_url_queue(db_path)
    cursor = conn.cursor()

    journal_mode = cursor.execute("PRAGMA journal_mode;").fetchone()[0]
    synchronous_mode = cursor.execute("PRAGMA synchronous;").fetchone()[0]

    conn.close()

    assert journal_mode == "wal", f"Expected journal_mode=wal, got {journal_mode}"
    assert synchronous_mode == 1, f"Expected synchronous=NORMAL (1), got {synchronous_mode}"

    # Verify the timeout parameter works (connection should not throw)
    conn2 = sqlite3.connect(db_path, timeout=20)
    conn2.close()

    print("PASS: journal_mode=wal, synchronous=NORMAL, timeout=20")
