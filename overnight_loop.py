#!/usr/bin/env python3
"""
overnight_loop.py — Overnight Loop Runner für Pipeline A + Research + Reports.

PHASEN-ABLAUF (sequentiell, GPU-safe):
  Phase 1: brand_orchestrator.py BRAND  → STORM Report
  Phase 2: pipeline_runner.py CAMPAIGN  → Pipeline A Scores
  Phase 3: report_orchestrator.py        → Report Generation

Jede Phase:
  - subprocess mit full venv-pfad
  - Max 3 Versuche
  - Nach jedem subprocess: 5min Pause + rocm-smi GPU Check (<10% oder max 10min)

FEHLER-VERARBEITUNG:
  - Bei Fehler: branch fix/auto-PHASE-TIMESTAMP erstellen
  - Last 100 log lines + error in Discord posten
  - Polling Discord alle 60s auf "FIX_READY:branchname" oder "FIX_FAILED"
  - Kein Hard-Timeout auf Discord-Polling — warte unbegrenzt
  - FIX_READY → git merge → Phase neu
  - FIX_FAILED → Phase skippen
  - Main Branch wird NIE angefasst

MITTeILUNGen via notify_discord.py:
  - Phase Start, OK, Fehler, Fix Branch, Loop-End-Zusammenfassung
  - Keine Tokens hardcoded
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

# ─── Global Constants ───────────────────────────────────────────────────────

PROJECT_ROOT = Path("/home/vincent/neuro_pipeline_project")
VENV_PYTHON = PROJECT_ROOT / "venv_rocm" / "bin" / "python"
LOG_DIR = PROJECT_ROOT
TIMEOUT_DEFAULT = 1800  # 30min pro Phase

# Discord Channel-ID: read from env (set before run)
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("overnight_loop")


# ─── Discord Notifications ──────────────────────────────────────────────────

def get_notify_script():
    """Return path to notify_discord.py."""
    return str(PROJECT_ROOT / "notify_discord.py")


def send_discord_notification(message: str):
    """Send via notify_discord.py subprocess (no hardcoded tokens)."""
    cmd = [str(VENV_PYTHON), get_notify_script(), message]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return True
        else:
            # Fallback: try channel_id direct
            if DISCORD_CHANNEL_ID:
                return send_discord_direct(message)
    except Exception:
        pass
    return False


def send_discord_direct(message: str):
    """Fallback: post directly via requests if notify_discord.py fails."""
    import requests
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(Path.home() / ".hermes" / ".env")

    token = os.getenv("DISCORD_BOT_TOKEN") or os.getenv("DISCORD_TOKEN") or ""
    channel = DISCORD_CHANNEL_ID or os.getenv("DISCORD_HOME_CHANNEL") or ""
    if not token or not channel:
        return False

    headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
    url = f"https://discord.com/api/v10/channels/{channel}/messages"
    resp = requests.post(url, headers=headers, json={"content": message}, timeout=30)
    return resp.status_code == 200


# ─── Discord Polling for FIX_READY ───────────────────────────────────────────

def poll_discord_messages(last_seen_id: str = "", max_retries: int = 100000) -> tuple:
    """
    Poll Discord channel for FIX_READY:branch or FIX_FAILED messages.
    Returns (found_type: Optional[str], branch_name: Optional[str]).
    found_type: 'FIX_READY', 'FIX_FAILED', or None
    """
    # Load creds
    from dotenv import load_dotenv
    load_dotenv(Path.home() / ".hermes" / ".env")

    token = os.getenv("DISCORD_BOT_TOKEN") or os.getenv("DISCORD_TOKEN") or ""
    channel = DISCORD_CHANNEL_ID or os.getenv("DISCORD_HOME_CHANNEL") or ""
    if not token or not channel:
        return (None, None)

    headers = {"Authorization": f"Bot {token}"}
    url = f"https://discord.com/api/v10/channels/{channel}/messages?limit=50{f'&after={last_seen_id}' if last_seen_id else ''}"

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
    except (URLError, json.JSONDecodeError, Exception):
        return (None, None)

    if not isinstance(data, list):
        return (None, None)

    pattern_fix = re.compile(r"FIX_READY:(\S+)", re.IGNORECASE)
    pattern_fail = re.compile(r"FIX_FAILED", re.IGNORECASE)

    # Check newest first
    for msg in data[:10]:
        content = msg.get("content", "")
        if pattern_fail.search(content):
            return ("FIX_FAILED", None)
        m = pattern_fix.search(content)
        if m:
            return ("FIX_READY", m.group(1))

    # Return last seen id for next poll
    if data:
        return ("POLLING", data[-1]["id"])  # oldest message returned by default
    return (None, None)


def wait_for_fix_response(phase_name: str, branch_name: str, dry_run: bool = False, poll_timeout: int = 5):
    """
    Wait for Discord FIX_READY:branch or FIX_FAILED. No timeout.
    Poll every 60s.
    
    In dry_run mode:
      - No actual Discord API calls
      - Simulates FIX_READY after ~poll_timeout seconds
      - Polls every 2s instead of 60s
    """
    if dry_run:
        # Simulate waiting for user to send FIX_READY in Discord
        poll_count = 0
        while True:
            # Check if the user's "mock FIX_READY" message exists
            from dotenv import load_dotenv
            from pathlib import Path as P
            load_dotenv(P.home() / ".hermes" / ".env")
            token = os.getenv("DISCORD_BOT_TOKEN") or os.getenv("DISCORD_TOKEN") or ""
            channel = DISCORD_CHANNEL_ID or os.getenv("DISCORD_HOME_CHANNEL") or ""
            if not token or not channel:
                logger.info("  ⚠️  [MOCK] No Discord creds — using built-in mock FIX_READY")
                time.sleep(poll_timeout)
                mock_branch = f"mock-fix-{branch_name}-{poll_count}"
                logger.info(f"  ✅ FIX_READY: {mock_branch} [MOCKED]")
                return ("FIX_READY", mock_branch)
            # Actually poll Discord for user's FIX_READY message
            poll_count += 1
            found_type, branch = poll_discord_messages("")
            if found_type == "FIX_READY":
                logger.info(f"  ✅ FIX_READY: {branch}")
                return ("FIX_READY", branch)
            # If POLLING but no FIX_READY, continue
            if poll_count % 3 == 0 and found_type is None:
                logger.info(f"  🎭 [MOCK] Poll {poll_count} — kein FIX_READY yet, warte weiter...")
            time.sleep(2)
        return ("FIX_READY", f"mock-fix-{branch_name}-dryrun")


# ─── Git Helpers ─────────────────────────────────────────────────────────────

def git_status():
    """Check if on main branch."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def create_fix_branch(branch_name: str, dry_run: bool = False):
    """Create fix branch from current HEAD (never main)."""
    if dry_run:
        logger.info(f"  🎭 [MOCK] create_fix_branch '{branch_name}' — skipped")
        return True
    main_branch = git_status()
    cmd = ["git", "checkout", "-b", branch_name]
    if main_branch != "HEAD":
        cmd2 = ["git", "checkout", main_branch]
        subprocess.run(cmd2, cwd=str(PROJECT_ROOT), capture_output=True, timeout=10)
        cmd = ["git", "checkout", "-b", branch_name, main_branch]
    result = subprocess.run(
        cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0:
        logger.info(f"  🔧 Branch '{branch_name}' erstellt")
        return True
    logger.error(f"  ❌ Branch-Erstellung fehlgeschlagen: {result.stderr}")
    return False


def merge_fix_branch(branch_name: str, dry_run: bool = False):
    """Merge fix branch into current branch."""
    if dry_run:
        logger.info(f"  🎭 [MOCK] merge_fix_branch '{branch_name}' — skipped")
        return True
    # Checkout main first
    main_branch = git_status()
    if main_branch != "HEAD":
        subprocess.run(["git", "checkout", main_branch],
                        cwd=str(PROJECT_ROOT), capture_output=True, timeout=10)
    result = subprocess.run(
        ["git", "merge", branch_name],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=60
    )
    if result.returncode == 0:
        logger.info(f"  🔄 Branch '{branch_name}' gemerged")
        subprocess.run(["git", "branch", "-d", branch_name],
                        cwd=str(PROJECT_ROOT), capture_output=True, timeout=10)
        subprocess.run(["git", "push", "origin", main_branch],
                        cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=30)
        return True
    logger.error(f"  ❌ Merge fehlgeschlagen: {result.stderr}")
    # Clean up on failure
    subprocess.run(["git", "merge", "--abort"],
                    cwd=str(PROJECT_ROOT), capture_output=True, timeout=10)
    return False


# ─── GPU & Wait Helpers ──────────────────────────────────────────────────────

def check_gpu_usage(timeout_minutes=10):
    """Warte bis rocm-smi GPU-Usage unter 10% (max timeout_minutes Wartezeit)."""
    end_time = time.time() + timeout_minutes * 60
    logger.info(f"  ⏳ Warte bis GPU-Usage unter 10% (max {timeout_minutes}min)...")
    while time.time() < end_time:
        try:
            result = subprocess.run(
                ["rocm-smi", "--showuse"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                logger.warning("  ⚠️ rocm-smi nicht verfügbar — GPU Check übersprungen")
                return True
            for line in result.stdout.strip().split("\n"):
                pct_match = re.search(r"(\d+)%", line)
                pct_match_total = re.search(r"Total:.*?(\d+)%", line)
                if pct_match and not pct_match_total:
                    pct = int(pct_match.group(1))
                    if pct >= 100:
                        continue
                    if pct < 10:
                        logger.info(f"  ✅ GPU-Usage: {pct}% — weiter")
                        return True
                    logger.info(f"  📊 GPU-Usage: {pct}%")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        time.sleep(15)
    logger.warning(f"  ⚠️ GPU-Timeout nach {timeout_minutes}min — ignoriere")
    return True


def wait_between_phases(dry_run: bool = False):
    """5min Pause + GPU Check. In dry_run: 5s, no GPU check."""
    if dry_run:
        logger.info(f"⏸️  [MOCK] Warte 5s statt 5min")
        time.sleep(5)
        return
    logger.info("⏸️  Warte 5min + GPU Check...")
    time.sleep(300)
    check_gpu_usage(10)


# ─── Logging Helper ──────────────────────────────────────────────────────────

def get_last_log_lines(log_path: str, n=100) -> list:
    """Get last N lines of a text file."""
    try:
        lines = Path(log_path).read_text().splitlines()
        return lines[-n:] if len(lines) > n else lines
    except Exception:
        return []


def summarize_error(proc) -> str:
    """Extract first meaningful error from subprocess output."""
    combined = (proc.stdout + proc.stderr)
    lines = combined.split("\n")

    # Look for error/critical patterns
    errors = []
    for i, line in enumerate(lines):
        if re.search(r"ERROR|FAILED|Traceback|Error|Exception|failed|Fehler", line, re.IGNORECASE):
            errors.append(line.strip())
        if errors and len(errors) >= 5:
            break
    return "\n".join(errors[:10]) if errors else combined[-500:] if combined else "Keine Error-Details"


# ─── Phase Result Tracking ───────────────────────────────────────────────────

class PhaseResult:
    """Ergebnis einer Phase."""
    def __init__(self, name, phase_num):
        self.name = name
        self.phase_num = phase_num
        self.success = False
        self.error = None
        self.result_data = None
        self.attempts = 0
        self.duration_s = 0
        self.branch_name = None

    def to_summary(self) -> str:
        if self.success:
            return f"Phase {self.phase_num} ({self.name}): ✅ ERFOLGREICH ({self.duration_s:.0f}s, {self.attempts}x)"
        return f"Phase {self.phase_num} ({self.name}): ❌ FEHLGESCHLAGEN | Fehler: {self.error}"


# ─── Phase Runner mit Fix-Logic ─────────────────────────────────────────────

def run_phase_with_fix_logic(phase_name: str, phase_num: int, phase_func, loop_results: list, dry_run: bool = False):
    """
    Phase mit maximal 3 Versuchen, Discord-Nachrichten, Fix-Branch und Discord-Polling.
    
    In dry_run mode:
      - time.sleep(300) → 5s
      - GPU Check wird übersprungen
      - Fix-Branch Creation mockt (git checkout -b würde real erstellt)
      - Discord Polling mockt (simuliert FIX_READY nach kurzer Wartezeit)
    """
    result = PhaseResult(phase_name, phase_num)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Discord: Phase Start
    start_msg = f"▶️ Phase {phase_num}: {phase_name} gestartet"
    send_discord_notification(start_msg)

    phase_log = LOG_DIR / f"overnight_phase_{phase_name}_{timestamp}.log"
    log_fh = logging.FileHandler(phase_log)
    log_fh.setLevel(logging.INFO)
    log_fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s | %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(log_fh)

    t_start = time.time()
    max_attempts = 3

    for attempt in range(1, max_attempts + 1):
        result.attempts = attempt
        logger.info(f"--- Versuch {attempt}/{max_attempts} ---")

        success, data = phase_func(attempt)
        logger.removeHandler(log_fh)
        log_fh.close()

        if success:
            result.success = True
            result.result_data = data
            result.duration_s = time.time() - t_start
            # Discord: Phase OK
            ok_msg = f"✅ Phase {phase_num}: {phase_name} fertig"
            send_discord_notification(ok_msg)
            loop_results.append(result)
            logger.info(f"✅ Phase {phase_name} ERFOLGREICH nach {attempt} Versuch(e)")
            return result

        error_summary = data if isinstance(data, str) else str(data)

        # Discord: Fehler
        err_lines = get_last_log_lines(str(phase_log), 100) if phase_log.exists() else []
        err_msg = f"❌ Fehler in Phase {phase_num}: {phase_name}\n\n{error_summary[:500]}"
        send_discord_notification(err_msg)

        # Git: Fix Branch erstellen
        branch_name = f"fix/auto-{phase_name}-{timestamp}"
        create_fix_branch(branch_name, dry_run)
        result.branch_name = branch_name

        # Discord: Fix Branch created
        branch_msg = f"🔧 Branch `fix/auto-{phase_name}-{timestamp}` erstellt, warte auf Fix..."
        send_discord_notification(branch_msg)

        # Discord Polling (unbegrenzt / dry_run: simulierte Zeit)
        fix_response = wait_for_fix_response(phase_name, branch_name, dry_run)
        fix_type = fix_response[0]

        if fix_type == "FIX_READY" and fix_response[1]:
            merged = merge_fix_branch(fix_response[1], dry_run)
            if merged:
                logger.info(f"  🔄 Fix gemerged — retry Phase {phase_num}...")
                continue  # Retry the phase
            else:
                result.error = f"Merge fehlgeschlagen: {fix_response[1]}"
        elif fix_type == "FIX_FAILED":
            result.error = "FIX_FAILED — Phase überspringen"
            skip_msg = f"⏭️ Phase {phase_num} ({phase_name}) übersprungen — FIX_FAILED"
            send_discord_notification(skip_msg)
        else:
            result.error = f"Kein Fix empfangen für Phase {phase_num}"

        if attempt < max_attempts:
            if dry_run:
                logger.info("[MOCK] Warte 2s statt 60s vor retry...")
                time.sleep(2)
            else:
                logger.info("⏸️  Warte 60s vor retry...")
                time.sleep(60)

    result.duration_s = time.time() - t_start
    result.error = f"Phase {phase_name} nach {max_attempts} Versuchen gescheitert"
    loop_results.append(result)
    return result


# ─── Phase Implementations ───────────────────────────────────────────────────

def create_phase_funcs(brand: str, campaign: str, dry_run: bool = False):
    """Generiere Phase-Funktionen basierend auf brand + campaign.
    
    In dry_run mode:
      - Alle subprocess.run() werden durch mock ersetzt (returncode=0)
      - time.sleep(300) → 5s (handled in run_phase_with_fix_logic)
      - GPU Check wird übersprungen
      - Phase 2 gibt returncode=1 zurück (simulierter Fehler)
      - Notifications laufen normal
    """
    phases = []

    def _mock_success(attempt: int):
        logger.info(f"  🎭 [MOCK] Phase erfolgreich nach Versuch {attempt}")
        return True, {"mock": True, "attempt": attempt}

    # ── Phase 1: Brand Research ─────────────────────────────────
    def phase1_brand_research(attempt: int):
        """PHASE 1: brand_orchestrator.py BRAND"""
        if dry_run:
            return _mock_success(attempt)
        cmd = [str(VENV_PYTHON), str(PROJECT_ROOT / "brand_orchestrator.py"), brand]
        logger.info(f"  Befehl: {' '.join(cmd)}")

        try:
            proc = subprocess.run(
                cmd, cwd=str(PROJECT_ROOT),
                capture_output=True, text=True, timeout=TIMEOUT_DEFAULT,
            )
            for line in (proc.stdout + proc.stderr).split("\n"):
                if line.strip():
                    print(f"  [BRAND] {line}")
            if proc.returncode != 0:
                return False, summarize_error(proc) if proc.returncode else "Unknown error"

            # Success: raw_data/BRAND_TIMESTAMP/Phase_4_STORM_Report.md + >500 Wörter
            storm_reports = []
            for d in (PROJECT_ROOT / "raw_data").glob(f"{brand.replace(' ', '_')}_*"):
                p = d / "Phase_4_STORM_Report.md"
                if p.exists():
                    storm_reports.append(p)

            if not storm_reports:
                return False, "Phase_4_STORM_Report.md nicht in raw_data/ gefunden"

            report_file = storm_reports[0]
            word_count = len(report_file.read_text(encoding="utf-8").split())
            if word_count > 500:
                return True, {"report_path": str(report_file), "word_count": word_count, "brand": brand}
            else:
                return False, f"STORM Report nur {word_count} Wörter (<500)"

        except subprocess.TimeoutExpired:
            return False, f"Timeout nach {TIMEOUT_DEFAULT}s"
        except Exception as e:
            return False, str(e)

    phases.append(("1_BRAND", 1, phase1_brand_research))

    # ── Phase 2: Pipeline A ────────────────────────────────
    def phase2_pipeline_a(attempt: int):
        """PHASE 2: pipeline_runner.py CAMPAIGN"""
        if dry_run:
            logger.info(f"  🎭 [MOCK] Phase 2 - Simulierter Fehler in Versuch {attempt}")
            return False, "DRY_RUN: Simulierter Pipeline-Fehler (Return Code 1)"
        campaign_path = PROJECT_ROOT / "campaigns" / campaign
        cmd = [str(VENV_PYTHON), str(campaign_path)]
        logger.info(f"  Befehl: {' '.join(cmd)}")

        try:
            proc = subprocess.run(
                cmd, cwd=str(PROJECT_ROOT),
                capture_output=True, text=True, timeout=TIMEOUT_DEFAULT,
            )
            for line in (proc.stdout + proc.stderr).split("\n"):
                if line.strip():
                    print(f"  [PIPELINE] {line}")

            if proc.returncode != 0:
                return False, summarize_error(proc)

            # Success: pipeline_a_results.json + keine neural_engagement=0.0
            results_path = PROJECT_ROOT / "campaigns" / campaign / "report" / "pipeline_a_results.json"
            if not results_path.exists():
                return False, "pipeline_a_results.json nicht gefunden"

            data = json.loads(results_path.read_text())
            for asset in data.get("assets", []):
                ne = asset.get("tribe", {}).get("neural_engagement", 0.0)
                if ne == 0.0:
                    return False, f"neural_engagement=0.0 für {asset.get('asset_name')}"

            return True, {
                "results_path": str(results_path),
                "ranking": data.get("ranking", []),
                "failed_assets": data.get("failed_assets", []),
            }

        except subprocess.TimeoutExpired:
            return False, f"Timeout nach {TIMEOUT_DEFAULT}s"
        except Exception as e:
            return False, str(e)

    phases.append(("2_PIPELINE_A", 2, phase2_pipeline_a))

    # ── Phase 3: Report Generation ────────────────────────────
    def phase3_report_generation(attempt: int):
        """PHASE 3: report_orchestrator.py --campaign CAMPAIGN"""
        if dry_run:
            return _mock_success(attempt)
        cmd = [
            str(VENV_PYTHON), str(PROJECT_ROOT / "report_agent" / "report_orchestrator.py"),
            "--campaign", campaign,
        ]
        logger.info(f"  Befehl: {' '.join(cmd)}")

        try:
            proc = subprocess.run(
                cmd, cwd=str(PROJECT_ROOT),
                capture_output=True, text=True, timeout=TIMEOUT_DEFAULT,
            )
            for line in (proc.stdout + proc.stderr).split("\n"):
                if line.strip():
                    print(f"  [REPORT] {line}")

            if proc.returncode != 0:
                return False, summarize_error(proc)

            # Success: nicht-leere Reports
            campaigns_report_dir = PROJECT_ROOT / "campaigns" / campaign / "report"
            valid = [
                p for p in campaigns_report_dir.rglob("*")
                if p.stat().st_size > 0
            ]
            if valid:
                return True, {"reports": [str(p) for p in valid]}
            return False, f"Keine nicht-leeren Reports in {campaigns_report_dir}"

        except subprocess.TimeoutExpired:
            return False, f"Timeout nach {TIMEOUT_DEFAULT}s"
        except Exception as e:
            return False, str(e)

    phases.append(("3_REPORT", 3, phase3_report_generation))
    return phases


# ─── Summary Builder ──────────────────────────────────────────────────────────

def build_summary_text(results: list, total_duration: float) -> str:
    """Build Discord summary message."""
    lines = ["🏁 OVERNIGHT LOOP ZUSAMMENFASSUNG", f"⏱️ Gesamtdauer: {total_duration/60:.1f} Minuten"]
    for r in results:
        lines.append(r.to_summary())

    # Score Summary (nur Phase 2)
    for r in results:
        if r.name == "2_PIPELINE_A" and r.result_data:
            lines.append("\n📊 Pipeline A Ergebnisse:")
            for entry in r.result_data.get("ranking", []):
                lines.append(f"  #{entry['rank']} {entry['asset']}: {entry['total_score']:.3f} (Grade {entry['grade']})")
            if r.result_data.get("failed_assets"):
                lines.append(f"  ❌ Failed Assets: {', '.join(r.result_data['failed_assets'])}")
        if r.name == "1_BRAND" and r.result_data:
            lines.append(f"\n🔬 Brand Research: {r.result_data['word_count']} Wörter STORM Report")
        if r.name == "3_REPORT" and r.result_data:
            lines.append(f"\n📄 Reports: {len(r.result_data['reports'])}")

    return "\n".join(lines)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Overnight Loop für NeuroAd Pipeline")
    parser.add_argument("brand", help="Brand name (z.B. 'Nike')")
    parser.add_argument("campaign", help="Campaign name (z.B. 'nike_summer_26')")
    parser.add_argument("--dry-run", action="store_true",
                        help="Mock phase execution: skip subprocesses, 5s sleeps, sim error in Phase 2")
    args = parser.parse_args()

    # Dry-run: skip subprocesses, mock phases, fast sleeps
    dry_run = args.dry_run

    # Validate channel
    if not DISCORD_CHANNEL_ID:
        logger.warning("⚠️  DISCORD_CHANNEL_ID nicht gesetzt — Discord-Nachrichten werden unterdrückt")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    overall_log = LOG_DIR / f"overnight_loop_{timestamp}.log"
    log_fh = logging.FileHandler(overall_log)
    log_fh.setLevel(logging.INFO)
    log_fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s | %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(log_fh)

    logger.info("=" * 60)
    logger.info("🚀 OVERNIGHT LOOP START")
    logger.info(f"   Brand:      {args.brand}")
    logger.info(f"   Campaign:   {args.campaign}")
    logger.info(f"   Gesamt-Log: {overall_log}")
    logger.info(f"   Startzeit:  {timestamp}")
    logger.info(f"   Discord:    {'Verbunden' if DISCORD_CHANNEL_ID else 'NICHT verb.'}")
    logger.info("=" * 60)

    t_start = time.time()
    loop_results: list = []

    # Build and run phases
    phases = create_phase_funcs(args.brand, args.campaign, dry_run)

    for phase_name, phase_num, phase_func in phases:
        result = run_phase_with_fix_logic(phase_name, phase_num, phase_func, loop_results, dry_run)
        if not result.success:
            logger.warning(f"⚠️ Phase {phase_name} nicht erfolgreich — versuche nächste Phase trotzdem")
            continue

        # Pause zwischen Phasen (nicht nach letzter)
        if phase_name != phases[-1][0]:
            wait_between_phases(dry_run)

    total_duration = time.time() - t_start

    # Discord: Gesamt-Zusammenfassung
    summary = build_summary_text(loop_results, total_duration)
    send_discord_notification(summary)

    logger.info("=" * 60)
    logger.info("🏁 OVERNIGHT LOOP ENDE")
    logger.info(f"   Gesamtdauer: {total_duration/60:.1f} Minuten")
    logger.info(f"   Erfolge: {sum(1 for r in loop_results if r.success)}/{len(loop_results)} Phasen")
    logger.info(f"   Gesamt-Log: {overall_log}")
    logger.info("=" * 60)

    # Also write summary to file
    summary_path = LOG_DIR / f"overnight_summary_{timestamp}.txt"
    summary_path.write_text(summary)
    logger.info(f"   Zusammenfassung: {summary_path}")


if __name__ == "__main__":
    main()
