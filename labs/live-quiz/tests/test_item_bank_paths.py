# tests/test_item_bank_paths.py
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import resolve_item_bank_paths


def test_uses_defaults_when_env_unset(tmp_path):
    a = tmp_path / "a.md"
    a.write_text("x")
    missing = str(tmp_path / "nope.md")
    resolved = resolve_item_bank_paths(None, [str(a), missing])
    assert resolved == [str(a)]  # only existing default paths survive


def test_env_override_takes_precedence(tmp_path):
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("x")
    b.write_text("y")
    configured = os.pathsep.join([str(a), str(b)])
    resolved = resolve_item_bank_paths(configured, ["/item-banks/default.md"])
    assert resolved == [str(a), str(b)]  # env list replaces the defaults entirely


def test_env_override_drops_nonexistent_paths(tmp_path):
    a = tmp_path / "a.md"
    a.write_text("x")
    configured = os.pathsep.join([str(a), str(tmp_path / "ghost.md")])
    resolved = resolve_item_bank_paths(configured, [])
    assert resolved == [str(a)]
