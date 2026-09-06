"""GitHub integration for automated Pull Request creation."""

import json
import logging
import urllib.request
import urllib.error
from typing import Optional
from secagent.config import get_settings

logger = logging.getLogger("secagent.git_tools.github_pr")


def create_pull_request(
    title: str,
    body: str,
    head_branch: str,
    base_branch: str = "main",
    repo_name: Optional[str] = None,
    token: Optional[str] = None,
) -> Optional[str]:
    """Create a Pull Request on GitHub via REST API."""
    settings = get_settings()
    gh_token = token or settings.github_token
    repository = repo_name or settings.github_repository

    if not gh_token or not repository:
        logger.info("GitHub Token or Repository not configured. Skipping automated PR creation.")
        return None

    api_url = f"https://api.github.com/repos/{repository}/pulls"
    headers = {
        "Authorization": f"Bearer {gh_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "SecAgent-Bot",
        "Content-Type": "application/json",
    }
    payload = {
        "title": title,
        "body": body,
        "head": head_branch,
        "base": base_branch,
    }

    try:
        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            html_url = data.get("html_url")
            logger.info(f"Successfully created GitHub Pull Request: {html_url}")
            return html_url
    except urllib.error.HTTPError as err:
        err_body = err.read().decode("utf-8", errors="replace")
        logger.error(f"GitHub API error ({err.code}): {err_body}")
        return None
    except Exception as exc:
        logger.error(f"Failed to create Pull Request: {exc}")
        return None
