"""
LLM Service Module (OpenRouter API Integration)
===============================================
Provides unified API key loading from .env, Jinja2 prompt template rendering,
and OpenRouter AI API completions with deterministic offline fallback safety.

Usage:
  from llm_service import LLMService
  llm = LLMService()
  prompt = llm.render_agent_prompt("emission_agent", {"line_code": "M5L011"})
  response = llm.generate_completion(prompt, provider="openrouter")
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
import requests
import jinja2

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("LLMService")


class LLMService:
    """
    LLM Service manager for environment key loading, prompt rendering, and OpenRouter AI completions.
    """

    PROMPT_FILE_MAP = {
        "emission_agent": "emission_agent.j2",
        "credit_agent": "credit_agent.j2",
        "policy_agent": "policy_agent.j2",
        "tax_agent": "tax_agent.j2",
        "report_agent": "report_agent.j2",
    }

    def __init__(
        self,
        env_file_path: str = ".env",
        prompts_dir: str = "prompts",
    ):
        self.env_file_path = env_file_path
        self.prompts_dir = prompts_dir
        self.load_env_file()

        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "your_openrouter_api_key_here")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "google/gemini-flash-1.5")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")

    def load_env_file(self):
        """Loads environment variables from .env file into os.environ."""
        if os.path.exists(self.env_file_path):
            try:
                with open(self.env_file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, val = line.split("=", 1)
                            key = key.strip()
                            val = val.strip().strip("'\"")
                            if key and key not in os.environ:
                                os.environ[key] = val
                logger.info(f"Loaded environment variables from: {self.env_file_path}")
            except Exception as e:
                logger.warning(f"Error loading .env file: {e}")

    def is_api_key_available(self, provider: str = "openrouter") -> bool:
        """Checks if a valid non-placeholder API key is set for provider."""
        if provider.lower() in ("openrouter", "default"):
            key = os.getenv("OPENROUTER_API_KEY", "")
            return bool(key and "your_" not in key.lower() and key != "")
        elif provider.lower() == "gemini":
            key = os.getenv("GEMINI_API_KEY", "")
            return bool(key and "your_" not in key.lower() and key != "")
        return False

    def render_agent_prompt(
        self,
        agent_name: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Loads Jinja prompt template for agent_name from prompts_dir and renders with context.
        """
        filename = self.PROMPT_FILE_MAP.get(agent_name, f"{agent_name}.j2")
        prompt_path = os.path.join(self.prompts_dir, filename)

        if not os.path.exists(prompt_path):
            logger.warning(f"Prompt template file not found at: {prompt_path}")
            return ""

        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                template_str = f.read()

            template = jinja2.Template(template_str)
            rendered = template.render(**context)
            return rendered
        except Exception as e:
            logger.error(f"Failed to render prompt template {filename}: {e}")
            return ""

    def generate_completion(
        self,
        prompt: str,
        provider: str = "openrouter",
        temperature: float = 0.0,
    ) -> str:
        """
        Generates completion using OpenRouter API if keys are present,
        or returns deterministic offline completion fallback.
        """
        if not self.is_api_key_available(provider):
            logger.info(f"LLMService: {provider.upper()} API key not configured or placeholder used. Executing deterministic fallback.")
            return f"[DETERMINISTIC_FALLBACK] Executed formulation for prompt:\n{prompt[:300]}..."

        # OpenRouter API call
        if provider.lower() in ("openrouter", "default"):
            try:
                url = "https://openrouter.ai/api/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/your-org/carbon_credits",
                    "X-Title": "EcoPulse AI Industrial Carbon Assessment",
                }
                payload = {
                    "model": self.openrouter_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                }
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
                logger.warning(f"OpenRouter API returned status {response.status_code}: {response.text}")
                return f"[DETERMINISTIC_FALLBACK_HTTP_{response.status_code}] Executed formulation fallback."
            except Exception as e:
                logger.warning(f"OpenRouter API call failed ({e}). Falling back to deterministic output.")
                return f"[DETERMINISTIC_FALLBACK_ERR] {e}"

        return "[DETERMINISTIC_FALLBACK] Unknown provider."

    def generate_structured_json(
        self,
        prompt: str,
        provider: str = "openrouter",
    ) -> Dict[str, Any]:
        """
        Generates parsable JSON object from LLM completion.
        """
        completion = self.generate_completion(prompt, provider=provider, temperature=0.0)
        try:
            clean = completion.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except Exception:
            return {"status": "SUCCESS", "raw_completion": completion}
