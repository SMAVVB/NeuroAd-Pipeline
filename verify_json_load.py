#!/usr/bin/env python3
"""
verify_json_load.py — Verification that corrupt JSON files are handled gracefully.

Writes an invalid JSON string to a dummy file, attempts to load it using the
updated loader functions, and asserts that they safely return a default dictionary
instead of raising json.decoder.JSONDecodeError.
"""

import json
import sys
import tempfile
from pathlib import Path

# Ensure the repo root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from report_agent.brand_context_loader import BrandContextLoader
from report_agent.interpreters.clip_interpreter import ClipInterpreter
from report_agent.interpreters.mirofish_interpreter import MiroFishInterpreter
from report_agent.interpreters.tribe_interpreter import TribeInterpreter
from report_agent.interpreters.vinet_interpreter import ViNetInterpreter
from report_agent.interpreters.base_interpreter import BaseInterpreter


def _write_corrupt_file(tmpdir: Path) -> Path:
    """Write an invalid JSON string to a temp file and return its path."""
    corrupt_path = tmpdir / "corrupt.json"
    corrupt_path.write_text('{ "broken": json ', encoding="utf-8")
    return corrupt_path


def test_brand_context_loader():
    """Test BrandContextLoader.load_brand_profile with corrupt JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        corrupt_path = _write_corrupt_file(tmpdir_path)
        loader = BrandContextLoader(tmpdir_path)
        result = loader.load_brand_profile(corrupt_path)
        assert result == {}, f"Expected empty dict, got {result!r}"
        print("PASS: BrandContextLoader.load_brand_profile returns {} for corrupt JSON")


def test_base_interpreter():
    """Test BaseInterpreter._load_json with corrupt JSON."""
    class _ConcreteInterpreter(BaseInterpreter):
        def load_scores(self, path):
            pass
        def interpret(self, scores, brand_context=None):
            pass
        def compare_creatives(self, scores_list):
            pass

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        corrupt_path = _write_corrupt_file(tmpdir_path)
        base = _ConcreteInterpreter("test")
        result = base._load_json(corrupt_path)
        assert result == {}, f"Expected empty dict, got {result!r}"
        print("PASS: BaseInterpreter._load_json returns {} for corrupt JSON")


def test_clip_interpreter():
    """Test ClipInterpreter.load_scores with corrupt JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        corrupt_path = _write_corrupt_file(tmpdir_path)
        interp = ClipInterpreter()
        result = interp.load_scores(corrupt_path)
        assert result == {}, f"Expected empty dict, got {result!r}"
        print("PASS: ClipInterpreter.load_scores returns {} for corrupt JSON")


def test_mirofish_interpreter():
    """Test MiroFishInterpreter._load_scores_file with corrupt JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        corrupt_path = _write_corrupt_file(tmpdir_path)
        interp = MiroFishInterpreter()
        result = interp._load_scores_file(corrupt_path)
        assert result == {}, f"Expected empty dict, got {result!r}"
        print("PASS: MiroFishInterpreter._load_scores_file returns {} for corrupt JSON")


def test_tribe_interpreter():
    """Test TribeInterpreter.load_scores with corrupt JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        corrupt_path = _write_corrupt_file(tmpdir_path)
        interp = TribeInterpreter()
        result = interp.load_scores(corrupt_path)
        assert result == {}, f"Expected empty dict, got {result!r}"
        print("PASS: TribeInterpreter.load_scores returns {} for corrupt JSON")


def test_vinet_interpreter():
    """Test ViNetInterpreter.load_scores with corrupt JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        corrupt_path = _write_corrupt_file(tmpdir_path)
        interp = ViNetInterpreter()
        result = interp.load_scores(corrupt_path)
        assert result == {}, f"Expected empty dict, got {result!r}"
        print("PASS: ViNetInterpreter.load_scores returns {} for corrupt JSON")


def test_valid_json_still_works():
    """Ensure valid JSON files are still loaded correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        valid_path = tmpdir_path / "valid.json"
        valid_path.write_text('{"brand": "test", "score": 0.95}', encoding="utf-8")
        loader = BrandContextLoader(tmpdir_path)
        result = loader.load_brand_profile(valid_path)
        assert result == {"brand": "test", "score": 0.95}, f"Expected valid data, got {result!r}"
        print("PASS: Valid JSON files are loaded correctly")


if __name__ == "__main__":
    tests = [
        test_brand_context_loader,
        test_base_interpreter,
        test_clip_interpreter,
        test_mirofish_interpreter,
        test_tribe_interpreter,
        test_vinet_interpreter,
        test_valid_json_still_works,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")
            failed += 1
    if failed:
        print(f"\n{failed}/{len(tests)} tests failed.")
        sys.exit(1)
    else:
        print(f"\nAll {len(tests)} tests passed.")
        sys.exit(0)
