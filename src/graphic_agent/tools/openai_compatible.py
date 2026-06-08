"""OpenAI-compatible provider adapters.

These adapters are optional real-provider tracers. Tests use fake transports;
the default pipeline still uses the mock provider.
"""

from __future__ import annotations

import base64
import http.client
import io
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from PIL import Image, ImageOps

from graphic_agent.provider_runtime import resolve_model_role
from graphic_agent.schemas import (
    AssetSpec,
    GeneratedAsset,
    ProviderProfile,
    ProviderUsage,
    StyleGuide,
)


class ImageGenerationTransport(Protocol):
    def generate_image(self, base_url: str, api_key: str, payload: dict) -> dict:
        """Return an OpenAI-compatible image generation response."""


class TextGenerationTransport(Protocol):
    def complete_chat(self, base_url: str, api_key: str, payload: dict) -> dict:
        """Return an OpenAI-compatible chat completion response."""


class UrllibOpenAICompatibleTransport:
    """Shared stdlib transport with small retries for unstable API gateways."""

    retryable_errors = (
        TimeoutError,
        http.client.RemoteDisconnected,
        urllib.error.URLError,
    )

    def post_json(
        self,
        endpoint: str,
        api_key: str,
        payload: dict,
        *,
        timeout: int = 600,
    ) -> dict:
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        last_error: Exception | None = None

        for attempt in range(1, 4):
            request = urllib.request.Request(
                endpoint,
                data=data,
                headers=headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except self.retryable_errors as exc:
                last_error = exc
                if attempt == 3:
                    break
                time.sleep(3 * attempt)

        if last_error:
            raise last_error
        raise RuntimeError("OpenAI-compatible request failed without an error.")


class UrllibImageGenerationTransport:
    """Minimal stdlib transport for OpenAI-compatible image APIs."""

    def __init__(self, transport: UrllibOpenAICompatibleTransport | None = None) -> None:
        self.transport = transport or UrllibOpenAICompatibleTransport()

    def generate_image(self, base_url: str, api_key: str, payload: dict) -> dict:
        endpoint = f"{base_url.rstrip('/')}/images/generations"
        return self.transport.post_json(endpoint, api_key, payload, timeout=600)


class UrllibTextGenerationTransport:
    """Minimal stdlib transport for OpenAI-compatible chat APIs."""

    def __init__(self, transport: UrllibOpenAICompatibleTransport | None = None) -> None:
        self.transport = transport or UrllibOpenAICompatibleTransport()

    def complete_chat(self, base_url: str, api_key: str, payload: dict) -> dict:
        endpoint = f"{base_url.rstrip('/')}/chat/completions"
        return self.transport.post_json(endpoint, api_key, payload, timeout=180)


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower()).strip("-")
    return slug or "asset"


class OpenAICompatibleImageGenerator:
    """Generate images through an OpenAI-compatible image endpoint."""

    def __init__(
        self,
        provider_profile: ProviderProfile,
        *,
        api_key: str,
        base_url: str,
        transport: ImageGenerationTransport | None = None,
    ) -> None:
        self.provider_profile = provider_profile
        self.model_spec = resolve_model_role(provider_profile, "image")
        self.api_key = api_key
        self.base_url = base_url
        self.transport = transport or UrllibImageGenerationTransport()

    def generate(
        self,
        spec: AssetSpec,
        style_guide: StyleGuide,
        output_dir: Path,
        round_index: int = 1,
    ) -> GeneratedAsset:
        output_dir.mkdir(parents=True, exist_ok=True)
        payload = self._build_payload(spec, style_guide)
        response = self.transport.generate_image(self.base_url, self.api_key, payload)
        image_bytes = self._extract_image_bytes(response)
        image_bytes = self._normalize_image_bytes(image_bytes, spec.size)
        path = output_dir / f"{spec.order:03d}_{_slug(spec.id)}_r{round_index}_openai.png"
        path.write_bytes(image_bytes)
        usage = ProviderUsage(
            role="image",
            provider_profile=self.provider_profile.name,
            provider=self.model_spec.provider,
            model=self.model_spec.model,
            image_generations=1,
            estimated_cost_usd=float(
                self.provider_profile.pricing.get("assumptions", {}).get(
                    "image_generation_usd",
                    0.0,
                )
            ),
        )
        return GeneratedAsset(
            spec_id=spec.id,
            path=str(path),
            prompt=spec.prompt,
            seed=0,
            round_index=round_index,
            metadata={
                "provider": self.provider_profile.name,
                "model": self.model_spec.model,
                "size": list(spec.size),
                "provider_usage": usage.model_dump(mode="json"),
            },
        )

    def _build_payload(self, spec: AssetSpec, style_guide: StyleGuide) -> dict:
        parameters = dict(self.model_spec.parameters)
        payload = {
            "model": self.model_spec.model,
            "prompt": f"{spec.prompt}\nStyle: {style_guide.visual_style}",
            "n": 1,
        }
        payload.update(parameters)
        return payload

    def _extract_image_bytes(self, response: dict) -> bytes:
        data = response.get("data") or []
        if not data:
            raise ValueError("OpenAI-compatible image response did not include data.")
        first = data[0]
        encoded = first.get("b64_json")
        if not encoded:
            raise ValueError("OpenAI-compatible image response did not include b64_json.")
        return base64.b64decode(encoded)

    def _normalize_image_bytes(self, image_bytes: bytes, size: tuple[int, int]) -> bytes:
        """Resize provider output to AssetSpec size without cropping visual content."""
        with Image.open(io.BytesIO(image_bytes)) as image:
            contained = ImageOps.contain(
                image.convert("RGB"),
                size,
                method=Image.Resampling.LANCZOS,
            )
            normalized = Image.new("RGB", size, (255, 255, 255))
            left = (size[0] - contained.width) // 2
            top = (size[1] - contained.height) // 2
            normalized.paste(contained, (left, top))
            buffer = io.BytesIO()
            normalized.save(buffer, format="PNG")
            return buffer.getvalue()


class OpenAICompatibleTextGenerator:
    """Generate text through an OpenAI-compatible chat endpoint."""

    def __init__(
        self,
        provider_profile: ProviderProfile,
        role: str,
        *,
        api_key: str,
        base_url: str,
        transport: TextGenerationTransport | None = None,
    ) -> None:
        self.provider_profile = provider_profile
        self.role = role
        self.model_spec = resolve_model_role(provider_profile, role)
        self.api_key = api_key
        self.base_url = base_url
        self.transport = transport or UrllibTextGenerationTransport()

    def complete(self, system_prompt: str, user_prompt: str) -> tuple[str, ProviderUsage]:
        return self.complete_messages(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )

    def complete_messages(self, messages: list[dict]) -> tuple[str, ProviderUsage]:
        payload = {
            "model": self.model_spec.model,
            "messages": messages,
        }
        payload.update(dict(self.model_spec.parameters))
        response = self.transport.complete_chat(self.base_url, self.api_key, payload)
        content = self._extract_content(response)
        usage_payload = response.get("usage") or {}
        usage = ProviderUsage(
            role=self.role,
            provider_profile=self.provider_profile.name,
            provider=self.model_spec.provider,
            model=self.model_spec.model,
            prompt_tokens=int(usage_payload.get("prompt_tokens", 0) or 0),
            completion_tokens=int(usage_payload.get("completion_tokens", 0) or 0),
            estimated_cost_usd=float(
                self.provider_profile.pricing.get("assumptions", {}).get(
                    f"{self.role}_call_usd",
                    0.0,
                )
            ),
        )
        return content, usage

    def _extract_content(self, response: dict) -> str:
        choices = response.get("choices") or []
        if not choices:
            raise ValueError("OpenAI-compatible chat response did not include choices.")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("OpenAI-compatible chat response did not include message content.")
        return content.strip()


def build_openai_compatible_image_generator(
    provider_profile: ProviderProfile,
    *,
    environ: Mapping[str, str] | None = None,
    transport: ImageGenerationTransport | None = None,
) -> OpenAICompatibleImageGenerator:
    """Build an OpenAI-compatible image generator from environment variables."""

    source = os.environ if environ is None else environ
    api_key_env = provider_profile.env.get("image_api_key") or provider_profile.env["api_key"]
    base_url_env = provider_profile.env.get("image_base_url") or provider_profile.env.get(
        "base_url"
    )
    missing = [name for name in [api_key_env, base_url_env] if name and not source.get(name)]
    if missing:
        raise RuntimeError(
            "Missing environment variables for image provider: " + ", ".join(missing)
        )
    base_url = source.get(base_url_env or "", "https://api.openai.com/v1")
    return OpenAICompatibleImageGenerator(
        provider_profile,
        api_key=source[api_key_env],
        base_url=base_url,
        transport=transport,
    )


def build_openai_compatible_text_generator(
    provider_profile: ProviderProfile,
    role: str,
    *,
    environ: Mapping[str, str] | None = None,
    transport: TextGenerationTransport | None = None,
) -> OpenAICompatibleTextGenerator:
    """Build an OpenAI-compatible text generator from text environment variables."""

    source = os.environ if environ is None else environ
    api_key_env = provider_profile.env.get("text_api_key") or provider_profile.env["api_key"]
    base_url_env = provider_profile.env.get("text_base_url") or provider_profile.env.get(
        "base_url"
    )
    missing = [name for name in [api_key_env, base_url_env] if name and not source.get(name)]
    if missing:
        raise RuntimeError(
            "Missing environment variables for text provider: " + ", ".join(missing)
        )
    base_url = source.get(base_url_env or "", "https://api.openai.com/v1")
    return OpenAICompatibleTextGenerator(
        provider_profile,
        role,
        api_key=source[api_key_env],
        base_url=base_url,
        transport=transport,
    )
