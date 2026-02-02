# ambientmeta

Python SDK for the AmbientMeta Privacy Gateway — strip PII before sending text to any LLM, restore it after.

## Install

```bash
pip install ambientmeta
```

## Usage

```python
from ambientmeta import AmbientMeta

client = AmbientMeta(api_key="your-api-key")

# 1. Sanitize — strip PII before the LLM call
result = client.sanitize("Email John Smith at john@acme.com about the merger")

print(result.sanitized)
# "Email [PERSON_1] at [EMAIL_1] about the merger"

# 2. Send sanitized text to any LLM
llm_response = your_llm.complete(result.sanitized)

# 3. Rehydrate — restore PII after the LLM responds
restored = client.rehydrate(text=llm_response, session_id=result.session_id)
print(restored.text)
# Original PII restored in the LLM's response
```

## Async

```python
from ambientmeta import AsyncAmbientMeta

async with AsyncAmbientMeta(api_key="your-api-key") as client:
    result = await client.sanitize("Email John Smith at john@acme.com")
    restored = await client.rehydrate(text=llm_response, session_id=result.session_id)
```

## Error handling

```python
from ambientmeta import AmbientMetaError, AuthenticationError, RateLimitError

try:
    result = client.sanitize("text")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Too many requests — wait and retry")
except AmbientMetaError as e:
    print(f"API error: {e.code} — {e.message}")
```

## Links

- [Quickstart guide](https://github.com/AmbientMeta/ambientmeta-api/blob/main/docs/quickstart.md)
- [API reference](https://github.com/AmbientMeta/ambientmeta-api/blob/main/docs/api-reference.md)
