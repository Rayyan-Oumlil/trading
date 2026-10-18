"""Tests for kill switch module."""
from __future__ import annotations

from pathlib import Path

import pytest

from paper_trading import kill_switch


@pytest.fixture(autouse=True)
def clean_halt(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Redirect HALT_FILE to a temp dir for every test."""
    halt_file = tmp_path / ".HALT"
    monkeypatch.setattr(kill_switch, "HALT_FILE", halt_file)
    yield halt_file


class TestKillSwitch:
    def test_not_halted_by_default(self, clean_halt: Path) -> None:
        assert not kill_switch.is_halted()

    def test_halted_after_create_halt(self, clean_halt: Path) -> None:
        kill_switch.create_halt("test reason")
        assert kill_switch.is_halted()

    def test_not_halted_after_remove_halt(self, clean_halt: Path) -> None:
        kill_switch.create_halt("test")
        kill_switch.remove_halt()
        assert not kill_switch.is_halted()

    def test_halt_file_contains_reason(self, clean_halt: Path) -> None:
        kill_switch.create_halt("drawdown exceeded 25%")
        content = clean_halt.read_text()
        assert "drawdown exceeded 25%" in content
        assert "HALTED at" in content

    def test_halt_reason_returns_content(self, clean_halt: Path) -> None:
        kill_switch.create_halt("oops")
        assert "oops" in (kill_switch.halt_reason() or "")

    def test_halt_reason_none_when_not_halted(self, clean_halt: Path) -> None:
        assert kill_switch.halt_reason() is None

    def test_remove_halt_idempotent(self, clean_halt: Path) -> None:
        kill_switch.remove_halt()
        kill_switch.remove_halt()
