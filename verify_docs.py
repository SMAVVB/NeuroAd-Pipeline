#!/usr/bin/env python3
"""verify_docs.py — Validates that documentation files exist and contain required keywords."""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
REQUIRED_FILES = ["ARCHITECTURE.md", "README.md"]
REQUIRED_KEYWORDS = {"Ollama", "Checkpoint", "Watchdog"}


def check_file_exists(filename: str) -> bool:
    path = os.path.join(ROOT, filename)
    if not os.path.isfile(path):
        print(f"FAIL: {filename} not found at {path}")
        return False
    print(f"OK:   {filename} exists")
    return True


def check_keywords(filename: str, keywords: set) -> bool:
    path = os.path.join(ROOT, filename)
    content = open(path, encoding="utf-8").read().upper()
    missing = {k for k in keywords if k.upper() not in content}
    if missing:
        print(f"FAIL: {filename} missing keywords: {missing}")
        return False
    print(f"OK:   {filename} contains all required keywords: {keywords}")
    return True


def check_readme_no_api_keys() -> bool:
    """Verify README does not reference legacy cloud API keys."""
    path = os.path.join(ROOT, "README.md")
    content = open(path, encoding="utf-8").read()
    legacy_keys = ["sk-proj-", "sk-", "api_key", "OPENAI_KEY", "ANTHROPIC_KEY"]
    found = [k for k in legacy_keys if k in content]
    if found:
        print(f"FAIL: README.md still references legacy API keys: {found}")
        return False
    print("OK:   README.md has no legacy API key references")
    return True


def check_readme_has_ollama() -> bool:
    """Verify README has Ollama setup instructions."""
    path = os.path.join(ROOT, "README.md")
    content = open(path, encoding="utf-8").read().lower()
    checks = ["ollama", "lemonade", "local", "llm"]
    missing = [c for c in checks if c not in content]
    if missing:
        print(f"FAIL: README.md missing local-LLM setup context: {missing}")
        return False
    print("OK:   README.md has local LLM / Ollama setup instructions")
    return True


def check_architecture_has_phases() -> bool:
    """Verify ARCHITECTURE.md documents the pipeline phases."""
    path = os.path.join(ROOT, "ARCHITECTURE.md")
    content = open(path, encoding="utf-8").read().lower()
    phase_keywords = ["phase 0", "phase 1", "phase 2", "phase 3", "phase 4"]
    missing = [k for k in phase_keywords if k not in content]
    if missing:
        print(f"FAIL: ARCHITECTURE.md missing phases: {missing}")
        return False
    print("OK:   ARCHITECTURE.md documents all pipeline phases")
    return True


def main():
    passed = 0
    failed = 0

    for f in REQUIRED_FILES:
        if check_file_exists(f):
            passed += 1
        else:
            failed += 1
            continue

    if check_keywords("ARCHITECTURE.md", REQUIRED_KEYWORDS):
        passed += 1
    else:
        failed += 1

    if check_keywords("README.md", REQUIRED_KEYWORDS):
        passed += 1
    else:
        failed += 1

    if check_readme_no_api_keys():
        passed += 1
    else:
        failed += 1

    if check_readme_has_ollama():
        passed += 1
    else:
        failed += 1

    if check_architecture_has_phases():
        passed += 1
    else:
        failed += 1

    print(f"\n{'='*40}")
    print(f"Result: {passed} passed, {failed} failed")

    if failed > 0:
        sys.exit(1)
    else:
        print("All documentation checks passed.")


if __name__ == "__main__":
    main()
