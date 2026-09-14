"""Ollama embedding access for build-time artefact generation (Part 2 stack table)."""

import json
import urllib.error
import urllib.request


class OllamaUnavailable(RuntimeError):  # noqa: N818 - required public API name
    """Raised when the local Ollama embedding endpoint cannot answer a request."""


def embed(
    texts: list[str],
    model: str = "bge-m3",
    base_url: str = "http://localhost:11434",
    timeout: float = 120,
) -> list[list[float]]:
    """Embed one batch through Ollama's ``/api/embed`` endpoint."""
    url = f"{base_url.rstrip('/')}/api/embed"
    payload = json.dumps({"model": model, "input": texts}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.getcode() != 200:
                raise OllamaUnavailable(f"Ollama unavailable at {url}: HTTP {response.getcode()}")
            result = json.loads(response.read().decode("utf-8"))
    except OllamaUnavailable:
        raise
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise OllamaUnavailable(f"Ollama unavailable at {url}: {exc}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError, OSError) as exc:
        raise OllamaUnavailable(f"Ollama unavailable at {url}: invalid response ({exc})") from exc

    embeddings = result.get("embeddings") if isinstance(result, dict) else None
    if not isinstance(embeddings, list):
        raise OllamaUnavailable(f"Ollama unavailable at {url}: response has no embeddings")
    return embeddings


class OllamaInvalidOutput(RuntimeError):  # noqa: N818 - required public API name
    """Raised when Ollama answered but its message is not one JSON object."""


def chat(
    prompt: str,
    schema: dict,
    model: str,
    base_url: str = "http://localhost:11434",
    timeout: float = 300,
) -> dict:
    """One schema-constrained extraction through Ollama's ``/api/chat`` endpoint (Task-36)."""
    url = f"{base_url.rstrip('/')}/api/chat"
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "format": schema,
            "stream": False,
            "think": False,
            "options": {"temperature": 0},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.getcode() != 200:
                raise OllamaUnavailable(f"Ollama unavailable at {url}: HTTP {response.getcode()}")
            raw = response.read().decode("utf-8", errors="replace")
    except OllamaUnavailable:
        raise
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise OllamaUnavailable(f"Ollama unavailable at {url}: {exc}") from exc

    try:
        envelope = json.loads(raw)
        content = envelope["message"]["content"]
        result = json.loads(content)
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise OllamaInvalidOutput(f"Ollama returned no JSON object: {raw[:200]}") from exc
    if not isinstance(result, dict):
        raise OllamaInvalidOutput(f"Ollama returned no JSON object: {content[:200]}")
    return result
