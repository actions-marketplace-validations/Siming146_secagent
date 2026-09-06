"""LLM client wrapper supporting DeepSeek-V4 (Flash & Pro Reasoning)."""

import json
import logging
import os
import re
from typing import Any, Dict, Optional, Tuple
from openai import OpenAI
from secagent.config import get_settings

logger = logging.getLogger("secagent.llm")


class DeepSeekClient:
    """Client for DeepSeek API with native reasoning extraction and mock support."""

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

        # Determine mock mode
        is_mock_env = os.getenv("DEEPSEEK_MOCK", "").lower() in ("1", "true", "yes")
        is_mock_key = not self.api_key or self.api_key.startswith("mock")
        self.mock_mode = mock_mode or is_mock_env or is_mock_key

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
        """Standard chat completion using DeepSeek-V4-Flash."""
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
        """Call DeepSeek reasoning model (DeepSeek-V4-Pro), returning (reasoning_content, final_answer)."""
        model = model or self.reasoner_model

        if self.mock_mode or not self.client:
            mock_text = self._get_mock_response(messages)
            return ("Mock reasoning trace analyzing root cause and code context...", mock_text)

        try:
            create_kwargs: Dict[str, Any] = {
                "model": model,
                "messages": messages,
            }
            # DeepSeek-V4 models support thinking configuration
            if any(k in model.lower() for k in ("v4", "pro", "flash")):
                create_kwargs["extra_body"] = {"thinking": {"type": "enabled"}}

            try:
                response = self.client.chat.completions.create(**create_kwargs)
            except Exception:
                # Fallback for standard or legacy endpoints without extra_body
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                )

            choice = response.choices[0]
            reasoning = getattr(choice.message, "reasoning_content", "") or ""
            content = choice.message.content or ""

            # Fallback: extract <think>...</think> tags if reasoning was embedded in content
            if not reasoning and "<think>" in content and "</think>" in content:
                think_match = re.search(r"<think>([\s\S]*?)</think>", content)
                if think_match:
                    reasoning = think_match.group(1).strip()
                    content = re.sub(r"<think>[\s\S]*?</think>", "", content).strip()

            return reasoning, content
        except Exception as exc:
            logger.error(f"DeepSeek-V4 reasoning API call failed: {exc}")
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

        # 1. Fixer Agent Prompt
        if "automated code repair specialist" in content or "minimal, secure patch" in content:
            return json.dumps({
                "diff": (
                    "--- a/app.py\n"
                    "+++ b/app.py\n"
                    "@@ -15,4 +15,6 @@\n"
                    " def execute_diagnostics(target_host: str) -> str:\n"
                    "     \"\"\"VULNERABLE (CWE-78 Command Injection): target_host is concatenated directly into a shell command.\"\"\"\n"
                    "+    if not target_host.replace(\".\", \"\").isalnum():\n"
                    "+        raise ValueError(\"Invalid target host\")\n"
                    "+    cmd = [\"ping\", \"-n\", \"1\", target_host] if os.name == \"nt\" else [\"ping\", \"-c\", \"1\", target_host]\n"
                    "-    cmd = f\"ping -n 1 {target_host}\" if os.name == \"nt\" else f\"ping -c 1 {target_host}\"\n"
                    "-    res = subprocess.check_output(cmd, shell=True, text=True)\n"
                    "+    res = subprocess.check_output(cmd, shell=False, text=True)\n"
                    "     return res.strip()\n"
                ),
                "explanation": "Sanitized target_host and replaced shell=True string concatenation with a safe argument list passed to subprocess.",
                "affected_files": ["app.py"],
                "side_effect_assessment": "Safe patch. Rejects shell metacharacters with ValueError while allowing valid IP addresses."
            })

        # 2. Verifier Agent Prompt
        if "verification specialist" in content or "reproduction test function" in content:
            return (
                "```python\n"
                "import pytest\n"
                "from app import execute_diagnostics\n\n"
                "def test_command_injection_reproduction():\n"
                "    # Verifies that execute_diagnostics executes without timing out\n"
                "    try:\n"
                "        res = execute_diagnostics('127.0.0.1; echo injected')\n"
                "        assert 'injected' in res or len(res) > 0\n"
                "    except ValueError:\n"
                "        pass\n"
                "```"
            )

        # 3. Triage Agent Prompt
        if "expert application security" in content or "true positive or false positive" in content:
            trigger = ""
            if "trigger snippet:" in content:
                trigger = content.split("trigger snippet:")[1].split("surrounding code context:")[0].lower()
            else:
                trigger = content

            if "import " in trigger or "b404" in content:
                return json.dumps({
                    "candidate_id": "BANDIT-IMPORT",
                    "is_real_vulnerability": False,
                    "confidence_score": 0.05,
                    "cwe_id": "CWE-78",
                    "reasoning": "Informational: Standard module import statement is not an exploitable vulnerability.",
                    "attack_vector": None,
                    "reproduction_strategy": None
                })
            elif "echo uptime" in trigger or "uptime" in trigger:
                return json.dumps({
                    "candidate_id": "BANDIT-UPTIME",
                    "is_real_vulnerability": False,
                    "confidence_score": 0.1,
                    "cwe_id": "CWE-78",
                    "reasoning": "False positive: 'echo uptime' is an immutable hardcoded constant string. No external or untrusted user input is reachable.",
                    "attack_vector": None,
                    "reproduction_strategy": None
                })
            else:
                return json.dumps({
                    "candidate_id": "BANDIT-CMD-INJECT",
                    "is_real_vulnerability": True,
                    "confidence_score": 0.96,
                    "cwe_id": "CWE-78",
                    "reasoning": "True positive: Untrusted parameter 'target_host' is directly formatted into a shell string executed via subprocess with shell=True, leading to OS command injection.",
                    "attack_vector": "Function parameter 'target_host' in execute_diagnostics()",
                    "reproduction_strategy": "Pass command separator metacharacters to verify arbitrary command execution"
                })

        # Default fallback
        return json.dumps({"status": "ok", "message": "SecAgent Mock Response"})
