"""Ollama Local LLM Client Module for Study Plan Generation.

Problem ID: C20 - Bennett University Prompt Engineering Mini-Project
Engine: Local Ollama with configurable model (default: qwen3:4b).
Separation of Concerns: Independent local API caller with structured JSON enforcement.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen3:4b"

COMMON_OLLAMA_MODELS = [
    "qwen3:4b",
    "qwen2.5:1.5b",
    "qwen2.5:3b",
    "qwen2.5:7b",
    "llama3.2:3b",
    "llama3.2:1b",
    "mistral:7b",
    "gemma2:2b",
]


def resolve_ollama_url(user_provided_url: Optional[str] = None) -> str:
    """Resolves Ollama base URL with priority:

    1. User provided URL in UI
    2. OLLAMA_BASE_URL or OLLAMA_HOST environment variable
    3. Default: http://localhost:11434
    """
    if user_provided_url and user_provided_url.strip():
        url = user_provided_url.strip().rstrip("/")
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"http://{url}"
        return url

    env_url = os.environ.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_HOST")
    if env_url and env_url.strip():
        url = env_url.strip().rstrip("/")
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"http://{url}"
        return url

    return DEFAULT_OLLAMA_URL


def resolve_ollama_model(user_provided_model: Optional[str] = None) -> str:
    """Resolves Ollama model name with fallback to environment or qwen3:4b default."""
    if user_provided_model and user_provided_model.strip():
        return user_provided_model.strip()

    env_model = os.environ.get("OLLAMA_MODEL")
    if env_model and env_model.strip():
        return env_model.strip()

    return DEFAULT_OLLAMA_MODEL


def check_ollama_status(base_url: Optional[str] = None) -> Dict[str, Any]:
    """Pings the Ollama server `/api/tags` endpoint to inspect availability and installed models.

    Returns:
        dict with keys: 'available' (bool), 'models' (list[str]), 'error' (Optional[str])
    """
    url = resolve_ollama_url(base_url)
    endpoint = f"{url}/api/tags"

    try:
        req = urllib.request.Request(endpoint, headers={"User-Agent": "StudyPlanGenerator/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                raw_data = resp.read().decode("utf-8")
                data = json.loads(raw_data)
                models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
                return {
                    "available": True,
                    "models": models,
                    "error": None,
                }
            else:
                return {
                    "available": False,
                    "models": [],
                    "error": f"Ollama server responded with HTTP {resp.status}.",
                }
    except urllib.error.URLError as url_err:
        return {
            "available": False,
            "models": [],
            "error": (
                f"Cannot connect to Ollama at '{url}'. "
                f"Is the Ollama application running? (Error: {url_err.reason})"
            ),
        }
    except Exception as exc:
        return {
            "available": False,
            "models": [],
            "error": f"Ollama check failed: {exc}",
        }


def call_ollama_study_planner(
    prompt: str,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    timeout: int = 300,
) -> Tuple[str, str]:
    """Sends prompt to local Ollama server requesting structured JSON output.

    Uses the `/api/generate` endpoint with `format: "json"`.

    Args:
        prompt: Rendered prompt template.
        base_url: Configurable Ollama host URL.
        model: Configurable model tag (e.g. qwen3:4b).
        timeout: Maximum seconds to wait for local model generation.

    Returns:
        Tuple of (raw_model_response_text, exact_model_used)

    Raises:
        RuntimeError: If server unreachable, model missing, timeout occurs, or output invalid.
    """
    effective_url = resolve_ollama_url(base_url)
    effective_model = resolve_ollama_model(model)
    endpoint = f"{effective_url}/api/generate"

    # Verify if model is available before waiting for long generation
    status = check_ollama_status(effective_url)
    if not status["available"]:
        raise RuntimeError(
            f"Ollama server is unavailable at '{effective_url}'.\n"
            f"Details: {status['error']}\n"
            "How to fix:\n"
            "1. Ensure Ollama is installed on your Windows PC (https://ollama.com).\n"
            "2. Start Ollama from your Start Menu or run `ollama serve` in PowerShell.\n"
            "3. If using a remote/custom port, update the Ollama URL in the sidebar."
        )

    # Check if the requested model is present in tags
    installed_models = status.get("models", [])
    if installed_models:
        model_base = effective_model.split(":")[0].lower()
        exact_matches = [m for m in installed_models if m.lower() == effective_model.lower()]
        base_matches = [m for m in installed_models if m.lower().startswith(model_base)]
        if not exact_matches and not base_matches:
            raise RuntimeError(
                f"Model '{effective_model}' is not installed on local Ollama at '{effective_url}'.\n"
                f"Currently installed models: {installed_models or 'None'}\n"
                f"To install it, run this command in your PowerShell:\n"
                f"    ollama pull {effective_model}\n"
                f"Or switch to an already installed model in the sidebar."
            )

    payload = {
        "model": effective_model,
        "prompt": prompt,
        "format": "json",  # Forces Ollama grammar-constrained JSON mode
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.9,
            "num_predict": 4096,
        },
    }

    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "StudyPlanGenerator/1.0",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                raise RuntimeError(
                    f"Ollama API returned HTTP {response.status} from '{endpoint}'."
                )
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)

            raw_text = res_json.get("response", "").strip()
            if not raw_text:
                raise RuntimeError(
                    f"Ollama model '{effective_model}' returned an empty response. "
                    "The model might need more RAM or context."
                )

            return raw_text, f"Ollama ({effective_model})"

    except urllib.error.HTTPError as http_err:
        if http_err.code == 404:
            raise RuntimeError(
                f"Model '{effective_model}' was not found by Ollama (HTTP 404).\n"
                f"Run: ollama pull {effective_model}"
            ) from http_err
        err_msg = http_err.read().decode("utf-8", errors="ignore")
        raise RuntimeError(
            f"Ollama HTTP {http_err.code} error: {err_msg}"
        ) from http_err

    except urllib.error.URLError as url_err:
        raise RuntimeError(
            f"Connection to Ollama server at '{effective_url}' lost or unreachable: {url_err.reason}.\n"
            "Please ensure Ollama is actively running."
        ) from url_err

    except TimeoutError as timeout_err:
        raise RuntimeError(
            f"Ollama generation timed out after {timeout} seconds on model '{effective_model}'.\n"
            "Local LLMs can take time on CPU. Try closing heavy applications or using a lighter model (e.g. qwen2.5:3b or llama3.2:1b)."
        ) from timeout_err

    except Exception as exc:
        raise RuntimeError(
            f"Unexpected error while communicating with Ollama ({effective_model}): {exc}"
        ) from exc
