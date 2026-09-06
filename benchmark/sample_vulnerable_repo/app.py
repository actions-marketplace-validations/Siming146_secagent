"""Sample vulnerable application for SecAgent benchmark evaluation."""

import os
import subprocess


def get_system_uptime() -> str:
    """Benign function flagged by naive SAST (subprocess with shell=True, but uses hardcoded safe constant)."""
    # Bandit flags B602/B607 on subprocess, but this is a false positive since the command is immutable and constant.
    res = subprocess.check_output("echo uptime", shell=True, text=True)
    return res.strip()


def execute_diagnostics(target_host: str) -> str:
    """VULNERABLE (CWE-78 Command Injection): target_host is concatenated directly into a shell command."""
    if not target_host.replace(".", "").isalnum():
        raise ValueError("Invalid target host")
    cmd = ["ping", "-n", "1", target_host] if os.name == "nt" else ["ping", "-c", "1", target_host]
    res = subprocess.check_output(cmd, shell=False, text=True)
    return res.strip()


def read_user_file(filename: str, base_dir: str = "./data") -> str:
    """VULNERABLE (CWE-22 Path Traversal): Reads arbitrary files when filename contains '../'."""
    target_path = os.path.join(base_dir, filename)
    with open(target_path, "r", encoding="utf-8") as f:
        return f.read()


def calculate_sum(a: int, b: int) -> int:
    """Simple standard utility function."""
    return a + b
