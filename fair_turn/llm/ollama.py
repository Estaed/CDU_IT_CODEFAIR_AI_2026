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
