"""Sample vulnerable application for SecAgent benchmark evaluation."""

import os
import subprocess


def get_system_uptime():
    """Benign function flagged by naive SAST (subprocess without shell=False, but uses hardcoded safe constant)."""
    # Bandit flags B602/B607 on subprocess, but this is a false positive since the command is immutable and constant.
    res = subprocess.check_output("echo uptime", shell=True, text=True)
    return res.strip()


def read_user_file(filename: str, base_dir: str = "./data") -> str:
    """VULNERABLE (CWE-22 Path Traversal): Reads arbitrary files when filename contains '../'."""
    # Flaw: Does not validate whether resolved target_path resides within base_dir.
    target_path = os.path.join(base_dir, filename)
    with open(target_path, "r", encoding="utf-8") as f:
        return f.read()


def calculate_sum(a: int, b: int) -> int:
    """Simple standard utility function."""
    return a + b
