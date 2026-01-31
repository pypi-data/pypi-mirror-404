"""
Ziqara Python SDK - Enterprise AI with company knowledge.

Usage:
    pip install ziqara

    from ziqara import Ziqara

    client = Ziqara(api_key="sk-ziq-xxx")
    response = client.chat.completions.create(
        model="ziqx",
        messages=[{"role": "user", "content": "Your question"}]
    )
    print(response.choices[0].message.content)
"""

from ziqara.client import Ziqara

__all__ = ["Ziqara"]
__version__ = "0.1.0"
