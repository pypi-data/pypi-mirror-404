# Ziqara Python SDK

Enterprise AI with company knowledge. Query your uploaded documents via a simple Python SDK.

## Installation

```bash
pip install ziqara
```

## Quick Start

1. **Get an API key** at [ziqara.com/dashboard/api](https://ziqara.com/dashboard/api)
2. **Install and use**:

```python
from ziqara import Ziqara

client = Ziqara(api_key="sk-ziq-xxx")

response = client.chat.completions.create(
    model="ziqx",
    messages=[{"role": "user", "content": "Summarize the Airtel agreement"}]
)

print(response.choices[0].message.content)
# Or use the convenience property:
print(response.content)
```

## API Reference

### Ziqara(api_key, base_url?)

- `api_key` (required): Your Ziqara API key. Starts with `sk-ziq-`.
- `base_url` (optional): API base URL. Default: `https://ziqara.com`. For local dev: `http://localhost:8000`

### client.chat.completions.create(model?, messages, stream?)

- `model` (optional): Model name. Default: `ziqx` (Ziqara's RAG-powered model)
- `messages` (required): List of `{"role": "user"|"assistant"|"system", "content": "..."}`
- `stream` (optional): Not yet supported. Default: `false`

Returns an OpenAI-compatible response with:
- `response.choices[0].message.content` - the assistant's reply
- `response.content` - shortcut for the above

## Requirements

- Python 3.8+
- `requests`

## Publishing to PyPI

```bash
pip install build twine
python -m build
twine upload dist/*
```

## License

MIT
