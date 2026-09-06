"""Regression test suite for sample vulnerable application."""

import pytest
from app import calculate_sum, get_system_uptime, read_user_file, execute_diagnostics


def test_calculate_sum():
    assert calculate_sum(2, 3) == 5
    assert calculate_sum(-1, 1) == 0


def test_get_system_uptime():
    assert "uptime" in get_system_uptime()


def test_execute_diagnostics_normal():
    # Tests standard localhost ping
    output = execute_diagnostics("127.0.0.1")
    assert len(output) > 0


def test_read_user_file_normal(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    sample_file = data_dir / "hello.txt"
    sample_file.write_text("hello world", encoding="utf-8")

    content = read_user_file("hello.txt", base_dir=str(data_dir))
    assert content == "hello world"
