import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class HarnessFailure(RuntimeError):
    pass


class ModelEnvelopeRejected(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class HarnessResult:
    text: str
    route: str


class Harness(Protocol):
    def run(self, prompt: str) -> HarnessResult: ...


_ALLOWED_TOP_LEVEL = {
    "schema_version",
    "intent",
    "channel",
    "features",
    "knowledge",
    "constraints",
}
_FORBIDDEN_KEYS = {
    "fitcrew_user_id",
    "user_id",
    "open_id",
    "chat_id",
    "message_id",
    "raw_samples",
    "raw_value",
    "question",
    "message",
    "prompt",
}


def validate_model_envelope(envelope: dict) -> None:
    if set(envelope) != _ALLOWED_TOP_LEVEL:
        raise ModelEnvelopeRejected("model envelope keys are not allowlisted")
    if envelope.get("schema_version") != "bodyos-model.v1":
        raise ModelEnvelopeRejected("unsupported model envelope")
    if envelope.get("channel") != "dm":
        raise ModelEnvelopeRejected("only de-identified DM envelopes may use a model")

    def walk(value) -> None:
        if isinstance(value, dict):
            if _FORBIDDEN_KEYS.intersection(value):
                raise ModelEnvelopeRejected("identifying or raw fields are forbidden")
            for nested in value.values():
                walk(nested)
        elif isinstance(value, list):
            for nested in value:
                walk(nested)

    walk(envelope)


def render_model_prompt(envelope: dict) -> str:
    validate_model_envelope(envelope)
    context = json.dumps(envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (
        "You are BodyOS, FitCrew's private health coach. Use only the supplied "
        "de-identified aggregate features and cited knowledge excerpts. Do not diagnose, "
        "invent measurements, infer identity, or request raw health data. Answer in concise "
        "Chinese and preserve page citations.\nBODYOS_ENVELOPE="
        + context
    )


class RoutedModelGateway:
    def __init__(self, primary: Harness, fallback: Harness, *, primary_attempts: int = 2):
        self._primary = primary
        self._fallback = fallback
        self._primary_attempts = max(1, primary_attempts)

    def respond(self, envelope: dict) -> HarnessResult:
        prompt = render_model_prompt(envelope)
        for _ in range(self._primary_attempts):
            try:
                result = self._primary.run(prompt)
                if result.text.strip():
                    return result
            except HarnessFailure:
                pass
        try:
            result = self._fallback.run(prompt)
            if result.text.strip():
                return result
        except HarnessFailure as error:
            raise HarnessFailure("all model harnesses failed") from error
        raise HarnessFailure("all model harnesses failed")


class CodexCLIHarness:
    def __init__(self, command: str = "codex", *, timeout_seconds: int = 120):
        self._command = command
        self._timeout_seconds = timeout_seconds

    def run(self, prompt: str) -> HarnessResult:
        with tempfile.TemporaryDirectory(prefix="bodyos-codex-") as directory:
            output_path = Path(directory) / "response.txt"
            command = [
                self._command,
                "exec",
                "--ephemeral",
                "--ignore-user-config",
                "--ignore-rules",
                "--sandbox",
                "read-only",
                "--skip-git-repo-check",
                "--cd",
                directory,
                "--output-last-message",
                str(output_path),
                "-",
            ]
            try:
                completed = subprocess.run(
                    command,
                    input=prompt,
                    text=True,
                    capture_output=True,
                    timeout=self._timeout_seconds,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as error:
                raise HarnessFailure("codex harness unavailable") from error
            if completed.returncode != 0 or not output_path.exists():
                raise HarnessFailure("codex harness failed")
            text = output_path.read_text(encoding="utf-8").strip()
            if not text:
                raise HarnessFailure("codex harness returned no response")
            return HarnessResult(text=text, route="codex")


class HermesCLIHarness:
    def __init__(
        self,
        command: str = "hermes",
        *,
        model: str = "gpt-5.3-codex",
        timeout_seconds: int = 120,
    ):
        self._command = command
        self._model = model
        self._timeout_seconds = timeout_seconds

    def run(self, prompt: str) -> HarnessResult:
        command = [
            self._command,
            "--oneshot",
            prompt,
            "--provider",
            "openai-codex",
            "--model",
            self._model,
            "--safe-mode",
        ]
        try:
            completed = subprocess.run(
                command,
                text=True,
                capture_output=True,
                timeout=self._timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise HarnessFailure("hermes harness unavailable") from error
        text = completed.stdout.strip()
        if completed.returncode != 0 or not text:
            raise HarnessFailure("hermes harness failed")
        return HarnessResult(text=text, route="hermes")
