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
        diff_lines = diff_text.splitlines()
        added_lines = [l[1:] for l in diff_lines if l.startswith("+") and not l.startswith("+++")]
        deleted_lines = [l[1:] for l in diff_lines if l.startswith("-") and not l.startswith("---")]

        del_target = "\n".join(deleted_lines).replace("\r\n", "\n")
        add_target = "\n".join(added_lines).replace("\r\n", "\n")
        content = original_content.replace("\r\n", "\n")

        if del_target and del_target in content:
            content = content.replace(del_target, add_target, 1)
        elif del_target and del_target.strip() in content:
            content = content.replace(del_target.strip(), add_target.strip(), 1)
        elif deleted_lines:
            for d in deleted_lines:
                d_norm = d.replace("\r\n", "\n").strip()
                if d_norm and d_norm in content:
                    content = content.replace(d_norm, add_target, 1)
                    break
        elif added_lines:
            # Pure addition - anchor to matching context line
            context_candidates = [l[1:].strip() for l in diff_lines if l.startswith(" ") and l[1:].strip()]
            for ctx in context_candidates:
                if ctx in content:
                    content = content.replace(ctx, ctx + "\n" + "\n".join(added_lines), 1)
                    break

        if content != original_content:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Applied fallback patch to {filename}")
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
