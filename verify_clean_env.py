"""Verify that legacy API keys are removed from the codebase."""

import ast
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent
LEGACY_KEYS = [
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "TOGETHER_API_KEY",
    "LEPTON_API_KEY",
]

FAILURES = []


SELF = Path(__file__).resolve()


def check_file(filepath: Path) -> None:
    if filepath.resolve() == SELF:
        return
    text = filepath.read_text(errors="ignore")

    # Check for legacy key names in source
    for key in LEGACY_KEYS:
        if re.search(rf"\b{key}\b", text):
            FAILURES.append(f"{filepath}: contains '{key}'")

    # Check for legacy imports
    if re.search(r"^\s*import\s+openai\s*$", text, re.MULTILINE):
        FAILURES.append(f"{filepath}: imports 'openai' directly")
    if re.search(r"^\s*import\s+anthropic\s*$", text, re.MULTILINE):
        FAILURES.append(f"{filepath}: imports 'anthropic' directly")


def check_config_core() -> None:
    """Assert config_core.py uses OLLAMA_URL, not LLM_URL or legacy keys."""
    config_path = REPO_ROOT / "config_core.py"
    if not config_path.exists():
        FAILURES.append("config_core.py not found")
        return

    source = config_path.read_text()
    if "LLM_URL" in source:
        FAILURES.append("config_core.py still uses LLM_URL (should be OLLAMA_URL)")
    if "OLLAMA_URL" not in source:
        FAILURES.append("config_core.py is missing OLLAMA_URL")

    # Parse AST to verify no openai/anthropic imports
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in ("openai", "anthropic"):
                    FAILURES.append(f"{config_path}: imports '{alias.name}'")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in ("openai", "anthropic"):
                FAILURES.append(f"{config_path}: imports from '{node.module}'")


def main() -> int:
    py_files = list(REPO_ROOT.rglob("*.py"))
    for f in py_files:
        check_file(f)

    # Also check .env
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        check_file(env_file)

    check_config_core()

    if FAILURES:
        for msg in FAILURES:
            print(f"FAIL: {msg}")
        print("\nVerification FAILED.")
        return 1
    else:
        print("All checks passed. Codebase is clean of legacy API keys.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
