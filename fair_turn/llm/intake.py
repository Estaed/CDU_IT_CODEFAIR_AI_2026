"""Provider seam for one new-report extraction (PRD sections 3.2 and 5)."""

import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from pydantic import ValidationError

from fair_turn.core import verify_spans
from fair_turn.core.verify_spans import VerifiedExtraction
from fair_turn.llm import claude_cli, ollama, prompts, schema

Provider = Literal["claude", "ollama"]
# qwen3:8b is the benchmarked local extractor (Task-36); gemma3:4b is the documented smaller
# fallback, selected with FAIR_TURN_OLLAMA_MODEL=gemma3:4b.
OLLAMA_EXTRACT_MODEL = os.environ.get("FAIR_TURN_OLLAMA_MODEL", "qwen3:8b")
MODEL_FOR = {"claude": "sonnet", "ollama": OLLAMA_EXTRACT_MODEL}


@dataclass(frozen=True)
class IntakeResult:
    extraction: dict | None
    verified: VerifiedExtraction | None
    status: Literal["extracted", "needs_review", "not_extracted"]
    provider: str
    model: str
    prompt_version: str
    latency_s: float
    validation: str
    error: str | None


def configured() -> Provider | None:
    """Return the accepted configured provider, if live intake is enabled."""
    provider = os.environ.get("FAIR_TURN_PROVIDER", "").strip()
    if not provider:
        return None
    if provider == "claude":
        return "claude"
    if provider == "ollama":
        return "ollama"
    raise ValueError(f"unknown FAIR_TURN_PROVIDER value: {provider}")


def extract(
    text: str,
    provider: Provider,
    timeout: float = 120,
    call: Callable[[str, dict], dict] | None = None,
) -> IntakeResult:
    """Extract, schema-validate and ground one report without trusting model evidence."""
    model = MODEL_FOR.get(provider, provider)
    prompt = prompts.intake_prompt(text)

    if call is None and provider == "ollama":

        def call(prompt: str, json_schema: dict) -> dict:
            return ollama.chat(prompt, json_schema, model=model, timeout=timeout)

    elif call is None:

        def call(prompt: str, json_schema: dict) -> dict:
            return claude_cli.generate(prompt, json_schema, model=model, timeout=timeout)

    started = time.monotonic()
    try:
        raw = call(prompt, schema.json_schema())
    except (
        claude_cli.CliError,
        ollama.OllamaUnavailable,
        ollama.OllamaInvalidOutput,
        TimeoutError,
        OSError,
    ) as exc:
        return IntakeResult(
            extraction=None,
            verified=None,
            status="not_extracted",
            provider=provider,
            model=model,
            prompt_version=prompts.INTAKE_PROMPT_VERSION,
            latency_s=time.monotonic() - started,
            validation="provider error",
            error=str(exc),
        )

    latency_s = time.monotonic() - started
    try:
        extraction = schema.Extraction.model_validate(raw).model_dump(mode="json")
    except ValidationError as exc:
        return IntakeResult(
            extraction=None,
            verified=None,
            status="not_extracted",
            provider=provider,
            model=model,
            prompt_version=prompts.INTAKE_PROMPT_VERSION,
            latency_s=latency_s,
            validation="schema invalid",
            error=exc.errors()[0]["msg"],
        )

    verified = verify_spans.verify(text, extraction)
    failed = [field for field in verify_spans.REQUIRED_FIELDS if getattr(verified, field) is None]
    if failed:
        return IntakeResult(
            extraction=extraction,
            verified=verified,
            status="needs_review",
            provider=provider,
            model=model,
            prompt_version=prompts.INTAKE_PROMPT_VERSION,
            latency_s=latency_s,
            validation=f"{', '.join(failed)} evidence not found in the report",
            error=None,
        )
    return IntakeResult(
        extraction=extraction,
        verified=verified,
        status="extracted",
        provider=provider,
        model=model,
        prompt_version=prompts.INTAKE_PROMPT_VERSION,
        latency_s=latency_s,
        validation="verified",
        error=None,
    )
