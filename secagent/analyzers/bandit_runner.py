"""Bandit SAST runner for Python codebases."""

import json
import logging
import os
import shutil
import subprocess
from typing import List
from secagent.analyzers.base import BaseAnalyzer
from secagent.state import VulnerabilityCandidate

logger = logging.getLogger("secagent.analyzers.bandit")


class BanditAnalyzer(BaseAnalyzer):
    """Integrates Bandit to gather initial candidate vulnerabilities in Python repos."""

    name: str = "bandit"

    def scan(self, repo_path: str) -> List[VulnerabilityCandidate]:
        """Run Bandit on repo_path with JSON formatter and return candidates."""
        candidates: List[VulnerabilityCandidate] = []
        repo_abs = os.path.abspath(repo_path)

        if not os.path.exists(repo_abs):
            logger.error(f"Repository path does not exist: {repo_abs}")
            return candidates

        # Check if bandit is executable
        bandit_bin = shutil.which("bandit")
        cmd = [
            bandit_bin or "bandit",
            "-r",
            repo_abs,
            "-f",
            "json",
            "-q",
            "--exclude",
            "*/tests/*,*/venv/*,*/.venv/*,*/build/*,*/dist/*",
        ]

        try:
            # Bandit returns exit code 1 if issues are found, 0 if clean
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            raw_json = proc.stdout.strip()
            if not raw_json and proc.stderr:
                logger.warning(f"Bandit stderr output: {proc.stderr}")
                return candidates

            if raw_json:
                data = json.loads(raw_json)
                results = data.get("results", [])
                for item in results:
                    cwe_info = item.get("issue_cwe", {})
                    cwe_str = f"CWE-{cwe_info.get('id')}" if cwe_info and cwe_info.get("id") else None
                    rel_file = os.path.relpath(item.get("filename", ""), repo_abs)
                    norm_path = rel_file.replace("\\", "/").lower()
                    test_id = item.get("test_id", "UNKNOWN")

                    # Exclude test files and assertion checks
                    if test_id == "B101" or "/tests/" in norm_path or norm_path.startswith("tests/") or "test_" in os.path.basename(norm_path):
                        continue

                    candidates.append(
                        VulnerabilityCandidate(
                            id=f"BANDIT-{len(candidates) + 1:03d}",
                            tool="bandit",
                            test_id=test_id,
                            cwe=cwe_str,
                            severity=item.get("issue_severity", "MEDIUM").upper(),
                            confidence=item.get("issue_confidence", "MEDIUM").upper(),
                            filename=rel_file,
                            line_number=item.get("line_number", 0),
                            line_range=item.get("line_range", []),
                            code=item.get("code", "").strip(),
                            issue_text=item.get("issue_text", ""),
                        )
                    )
        except subprocess.TimeoutExpired:
            logger.error("Bandit execution timed out after 120 seconds")
        except FileNotFoundError:
            logger.warning("Bandit CLI not found in PATH. Please install bandit: pip install bandit")
        except json.JSONDecodeError as err:
            logger.error(f"Failed to parse Bandit JSON output: {err}")
        except Exception as exc:
            logger.error(f"Unexpected error running Bandit: {exc}")

        return candidates
