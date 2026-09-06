"""LLM client wrapper supporting DeepSeek-Chat and DeepSeek-Reasoner (R1)."""

import json
import logging
import os
import re
from typing import Any, Dict, Optional, Tuple
from openai import OpenAI
from secagent.config import get_settings

logger = logging.getLogger("secagent.llm")


class DeepSeekClient:
    """Client for DeepSeek API with reasoning extraction and mock support."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        mock_mode: bool = False,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.deepseek_api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url or settings.deepseek_base_url
        self.chat_model = settings.deepseek_chat_model
        self.reasoner_model = settings.deepseek_reasoner_model
        self.mock_mode = mock_mode or not bool(self.api_key)

        if not self.mock_mode and self.api_key:
            self.client: Optional[OpenAI] = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        else:
            self.client = None
            logger.info("DeepSeekClient initialized in mock / offline mode.")

    def chat_completion(
        self,
        messages: list,
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        """Standard chat completion using DeepSeek-Chat."""
        model = model or self.chat_model

        if self.mock_mode or not self.client:
            return self._get_mock_response(messages)

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.error(f"DeepSeek API call failed: {exc}")
            raise

    def reasoning_completion(
        self,
        messages: list,
        model: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Call DeepSeek-Reasoner (R1), returning (reasoning_content, final_answer)."""
        model = model or self.reasoner_model

        if self.mock_mode or not self.client:
            mock_text = self._get_mock_response(messages)
            return ("Mock reasoning trace analyzing root cause and code context...", mock_text)

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
            )
            choice = response.choices[0]
            reasoning = getattr(choice.message, "reasoning_content", "") or ""
            content = choice.message.content or ""
            return reasoning, content
        except Exception as exc:
            logger.error(f"DeepSeek-Reasoner API call failed: {exc}")
            raise

    def extract_json(self, text: str) -> Dict[str, Any]:
        """Extract and parse JSON object from LLM response text."""
        # Try raw parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Match markdown ```json ... ``` code block
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Match between first '{' and last '}'
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not parse valid JSON from LLM output:\n{text}")

    def _get_mock_response(self, messages: list) -> str:
        """Deterministic mock response for tests and offline benchmark runs."""
        content = " ".join(m.get("content", "") for m in messages).lower()

        # Mock Triage
        if "triage" in content or "candidate" in content:
            return json.dumps({
                "candidate_id": "BANDIT-001",
                "is_real_vulnerability": True,
                "confidence_score": 0.95,
                "cwe_id": "CWE-22",
                "reasoning": "Unvalidated user input is passed directly to file path constructor allowing path traversal.",
                "attack_vector": "HTTP parameter 'file' in download_file() without os.path.abspath boundary check",
                "reproduction_strategy": "Request with '../../etc/passwd' or similar relative path expecting traversal"
            })

        # Mock Verifier
        if "reproduction" in content or "pytest" in content or "verifier" in content:
            return (
                "```python\n"
                "import pytest\n"
                "from app import read_user_file\n\n"
                "def test_path_traversal_reproduction(tmp_path):\n"
                "    secret = tmp_path / 'secret.txt'\n"
                "    secret.write_text('super_secret_data')\n"
                "    with pytest.raises(PermissionError):\n"
                "        read_user_file('../../secret.txt', base_dir=str(tmp_path))\n"
                "```"
            )

        # Mock Fixer
        if "patch" in content or "diff" in content or "fix" in content:
            return json.dumps({
                "diff": (
                    "--- a/app.py\n"
                    "+++ b/app.py\n"
                    "@@ -10,6 +10,10 @@\n"
                    " def read_user_file(filename, base_dir):\n"
                    "+    safe_base = os.path.abspath(base_dir)\n"
                    "+    target = os.path.abspath(os.path.join(safe_base, filename))\n"
                    "+    if not target.startswith(safe_base):\n"
                    "+        raise PermissionError('Path traversal detected')\n"
                    "     return open(target, 'r').read()\n"
                ),
                "explanation": "Added os.path.abspath boundary validation to prevent directory traversal outside base_dir.",
                "affected_files": ["app.py"],
                "side_effect_assessment": "Safe change, only blocks directory traversal while allowing legitimate paths within base_dir."
            })

        # Default fallback
        return json.dumps({"status": "ok", "message": "SecAgent Mock Response"})
