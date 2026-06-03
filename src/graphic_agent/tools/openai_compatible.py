"""OpenAI-compatible provider adapters.

These adapters are optional real-provider tracers. Tests use fake transports;
the default pipeline still uses the mock provider.
"""

from __future__ import annotations

import base64
import json
import os
import re
import urllib.request
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from graphic_agent.provider_runtime import resolve_model_role, validate_provider_environment
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


class UrllibImageGenerationTransport:
    """Minimal stdlib transport for OpenAI-compatible image APIs."""

    def generate_image(self, base_url: str, api_key: str, payload: dict) -> dict:
        endpoint = f"{base_url.rstrip('/')}/images/generations"
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            endpoint,
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))


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


def build_openai_compatible_image_generator(
    provider_profile: ProviderProfile,
    *,
    environ: Mapping[str, str] | None = None,
    transport: ImageGenerationTransport | None = None,
) -> OpenAICompatibleImageGenerator:
    """Build an OpenAI-compatible image generator from environment variables."""

    source = os.environ if environ is None else environ
    status = validate_provider_environment(provider_profile, source)
    if not status.ready:
        missing = ", ".join(status.missing_env)
        raise RuntimeError(f"Missing environment variables for provider profile: {missing}")
    api_key_env = provider_profile.env["api_key"]
    base_url_env = provider_profile.env.get("base_url")
    base_url = source.get(base_url_env or "", "https://api.openai.com/v1")
    return OpenAICompatibleImageGenerator(
        provider_profile,
        api_key=source[api_key_env],
        base_url=base_url,
        transport=transport,
    )
