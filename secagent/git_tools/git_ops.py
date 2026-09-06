"""Git automation utilities for patch application and branch management."""

import logging
import os
import subprocess
from typing import List, Optional

logger = logging.getLogger("secagent.git_tools.ops")


def apply_patch_to_file(
    repo_path: str,
    filename: str,
    diff_text: str,
    original_content: str,
) -> bool:
    """Apply a unified diff to a target file, with fallback to hunk parsing."""
    full_path = os.path.join(repo_path, filename)

    if not diff_text or not diff_text.strip():
        logger.warning("Empty diff provided to apply_patch_to_file")
        return False

    # Attempt 1: Using git apply via stdin
    try:
        proc = subprocess.run(
            ["git", "apply", "--whitespace=nowarn", "-"],
            input=diff_text.encode("utf-8"),
            cwd=repo_path,
            capture_output=True,
        )
        if proc.returncode == 0:
            logger.info(f"Successfully applied git diff to {filename}")
            return True
        else:
            logger.debug(f"git apply exited with {proc.returncode}: {proc.stderr.decode('utf-8', errors='replace')}")
    except Exception as exc:
        logger.debug(f"git apply command failed: {exc}")

    # Attempt 2: Fallback line-based patch application
    try:
        lines = original_content.splitlines(keepends=True)
        # Parse simple single-hunk diff additions and deletions
        diff_lines = diff_text.splitlines()
        added_lines = [l[1:] + "\n" for l in diff_lines if l.startswith("+") and not l.startswith("+++")]
        deleted_lines = [l[1:] + "\n" for l in diff_lines if l.startswith("-") and not l.startswith("---")]

        # If simple modification, attempt heuristic replace
        if added_lines and deleted_lines:
            content = original_content
            for d in deleted_lines:
                if d in content:
                    content = content.replace(d, "".join(added_lines), 1)
                    break
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Applied heuristic patch to {filename}")
            return True

    except Exception as exc:
        logger.error(f"Fallback patch application failed: {exc}")

    return False


def create_and_checkout_branch(repo_path: str, branch_name: str) -> bool:
    """Create and check out a new git branch in the repository."""
    try:
        proc = subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        return proc.returncode == 0
    except Exception as err:
        logger.error(f"Failed to checkout branch {branch_name}: {err}")
        return False


def commit_changes(repo_path: str, commit_message: str, files: Optional[List[str]] = None) -> bool:
    """Stage files and create a git commit."""
    try:
        files_to_add = files or ["."]
        subprocess.run(["git", "add"] + files_to_add, cwd=repo_path, check=True, capture_output=True)
        proc = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        return proc.returncode == 0
    except Exception as err:
        logger.error(f"Failed to commit changes: {err}")
        return False
