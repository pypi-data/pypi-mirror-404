from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable

from .config import Settings


class LLMError(RuntimeError):
    pass


@dataclass
class LLMResponse:
    content: str
    raw: dict
    raw_text: str
    status: int | None = None


def _chat_url(base_url: str) -> str:
    trimmed = base_url.rstrip("/")
    if trimmed.endswith("/chat/completions"):
        return trimmed
    return trimmed + "/chat/completions"


def _system_prompt(shell: str) -> str:
    return (
        "You are a shell command generator. "
        f"Target shell: {shell}. "
        "Return ONLY the command text. "
        "No explanations, no markdown, no code fences. "
    )


def _system_prompt_answer() -> str:
    return (
        "You are a helpful assistant. "
        "Answer clearly and concisely. "
        "Do NOT output shell commands unless the user explicitly asks for them. "
        "If you do include shell code, do so plainly without markdown fences."
    )


def _user_prompt(prompt: str) -> str:
    cwd = os.getcwd()
    return f"Task: {prompt}\nWorking directory: {cwd}"


def _request_chat(
    *,
    payload: dict,
    settings: Settings,
    log: Callable[[str], None] | None = None,
) -> LLMResponse:
    url = _chat_url(settings.endpoint or "")
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.api_key}",
        "User-Agent": "clanker/0.1.0",
    }

    if log:
        log(f"LLM request URL: {url}")
        log("LLM request payload:")
        log(json.dumps(payload, indent=2, sort_keys=True))

    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw_body = response.read()
            status = getattr(response, "status", None)
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", "replace")
        if log:
            log(f"HTTP error {exc.code} response body:")
            log(error_body)
        raise LLMError(f"HTTP {exc.code} from LLM endpoint: {error_body}") from exc
    except urllib.error.URLError as exc:
        if log:
            log(f"Failed to reach LLM endpoint: {exc}")
        raise LLMError(f"Failed to reach LLM endpoint: {exc}") from exc

    raw_text = raw_body.decode("utf-8", "replace")
    if log:
        log(f"LLM response status: {status}")
        log("LLM response body:")
        log(raw_text)

    try:
        parsed = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise LLMError("LLM response was not valid JSON") from exc

    try:
        content = parsed["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError("LLM response missing message content") from exc

    if not isinstance(content, str) or not content.strip():
        raise LLMError("LLM response content was empty")

    return LLMResponse(content=content, raw=parsed, raw_text=raw_text, status=status)


def generate_command(
    *,
    prompt: str,
    settings: Settings,
    temperature: float | None = None,
    max_tokens: int | None = None,
    log: Callable[[str], None] | None = None,
) -> str:
    payload = {
        "model": settings.model,
        "messages": [
            {"role": "system", "content": _system_prompt(settings.shell or "fish")},
            {"role": "user", "content": _user_prompt(prompt)},
        ],
        "temperature": 0.2 if temperature is None else temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    response = _request_chat(payload=payload, settings=settings, log=log)
    return response.content


def generate_answer(
    *,
    prompt: str,
    settings: Settings,
    temperature: float | None = None,
    max_tokens: int | None = None,
    log: Callable[[str], None] | None = None,
) -> str:
    payload = {
        "model": settings.model,
        "messages": [
            {"role": "system", "content": _system_prompt_answer()},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2 if temperature is None else temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    response = _request_chat(payload=payload, settings=settings, log=log)
    return response.content


def normalize_command(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return cleaned

    fenced = re.search(r"```(?:\w+)?\n(.*?)```", cleaned, flags=re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()

    lower = cleaned.lower()
    if lower.startswith("command:"):
        cleaned = cleaned.split(":", 1)[1].strip()

    return cleaned
