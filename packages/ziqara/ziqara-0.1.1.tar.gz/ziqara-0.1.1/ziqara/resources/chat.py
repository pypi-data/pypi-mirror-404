"""
Chat completions resource - OpenAI-compatible interface.
"""

from typing import Any, Dict, List, Optional

import requests

from ziqara._response import ChatCompletionResponse


class ChatCompletions:
    """Chat completions API - same interface as OpenAI."""

    def __init__(self, client: "Ziqara"):  # noqa: F821
        self._client = client

    def create(
        self,
        messages: List[Dict[str, str]],
        model: str = "ziqx",
        stream: bool = False,
    ) -> ChatCompletionResponse:
        """
        Create a chat completion.

        Args:
            model: Model name (default: ziqx). Use ziqx for Ziqara's RAG-powered model.
            messages: List of message dicts, e.g. [{"role": "user", "content": "Your question"}]
            stream: If True, return streaming response (not yet implemented).

        Returns:
            ChatCompletionResponse with choices[0].message.content
        """
        if stream:
            raise NotImplementedError("Streaming is not yet supported in the SDK")
        if not messages:
            raise ValueError("messages is required")
        url = f"{self._client.base_url}/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._client.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return ChatCompletionResponse(**data)
