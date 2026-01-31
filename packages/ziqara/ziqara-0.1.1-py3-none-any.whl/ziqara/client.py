"""
Ziqara API client.
"""

from ziqara.resources.chat import ChatCompletions


class Ziqara:
    """
    Ziqara API client for enterprise AI with company knowledge.

    Args:
        api_key: Your Ziqara API key (sk-ziq-xxx). Get one at https://ziqara.com/dashboard/api
        base_url: API base URL (default: https://ziqara.com)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://ziqara.com",
    ):
        if not api_key or not api_key.strip():
            raise ValueError("api_key is required")
        if not api_key.startswith("sk-ziq-"):
            raise ValueError("api_key must start with sk-ziq-")
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")

        self.chat = _ChatResource(self)


class _ChatResource:
    """Wrapper so client.chat.completions.create() matches OpenAI-style API."""

    def __init__(self, client: Ziqara):
        self.completions = ChatCompletions(client)
