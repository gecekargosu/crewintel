"""CREWINTEL LLM Client — Groq / OpenAI-uyumlu API istemcisi.

Groq ücretsiz tier: https://console.groq.com
Desteklenen modeller: llama-3.3-70b-versatile, mixtral-8x7b-32768, gemma2-9b-it
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class LLMConfig:
    """LLM yapılandırması."""
    api_key: str = ""
    base_url: str = "https://api.groq.com/openai/v1"
    model: str = "llama-3.3-70b-versatile"
    max_tokens: int = 4096
    temperature: float = 0.3
    timeout: float = 60.0

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Ortam değişkenlerinden yapılandırma oluştur."""
        return cls(
            api_key=os.environ.get("GROQ_API_KEY", ""),
            base_url=os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            model=os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
            max_tokens=int(os.environ.get("GROQ_MAX_TOKENS", "4096")),
            temperature=float(os.environ.get("GROQ_TEMPERATURE", "0.3")),
        )


@dataclass
class LLMResponse:
    """LLM yanıt yapısı."""
    content: str
    model: str
    tokens_used: int = 0
    finish_reason: str = ""
    raw: dict = field(default_factory=dict)


class LLMClient:
    """Groq / OpenAI-uyumlu LLM istemcisi."""

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig.from_env()
        if not self.config.api_key:
            raise ValueError(
                "GROQ_API_KEY ayarlanmamış. "
                "https://console.groq.com adresinden ücretsiz key alıp "
                "ortam değişkenine veya .env dosyasına ekleyin."
            )

    def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Tek mesaj gönder ve yanıt al."""
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        payload = {
            "model": self.config.model,
            "messages": full_messages,
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature if temperature is not None else self.config.temperature,
        }

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=self.config.timeout) as client:
            resp = client.post(
                f"{self.config.base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]
        usage = data.get("usage", {})

        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", self.config.model),
            tokens_used=usage.get("total_tokens", 0),
            finish_reason=choice.get("finish_reason", ""),
            raw=data,
        )

    def analyze(
        self,
        text: str,
        task: str,
        system_prompt: str | None = None,
    ) -> str:
        """Metni analiz et ve sonuç döndür."""
        default_prompt = (
            "Sen CREWINTEL için bir yapay zeka asistanısın. "
            "Gemi personeli yönetimi, belge analizi ve iş eşleştirme konularında uzmanlaşmışsın. "
            "Her zaman Türkçe ve profesyonelce yanıt ver."
        )
        response = self.chat(
            messages=[{"role": "user", "content": f"{task}\n\n---\n{text}"}],
            system_prompt=system_prompt or default_prompt,
        )
        return response.content

    def is_available(self) -> bool:
        """LLM erişilebilir mi kontrol et."""
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(
                    f"{self.config.base_url}/models",
                    headers={"Authorization": f"Bearer {self.config.api_key}"},
                )
                return resp.status_code == 200
        except Exception:
            return False
