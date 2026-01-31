# Nemati AI Python SDK

[![PyPI version](https://badge.fury.io/py/nemati-ai.svg)](https://badge.fury.io/py/nemati-ai)
[![Python Versions](https://img.shields.io/pypi/pyversions/nemati-ai.svg)](https://pypi.org/project/nemati-ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official Python SDK for [Nemati AI](https://nemati.ai) - Your all-in-one AI platform for content creation, image generation, trend discovery, and more.

## Installation

```bash
pip install nemati-ai
```

## Quick Start

```python
from nemati import NematiAI

# Initialize client
client = NematiAI(api_key="your-api-key")

# Chat completion
response = client.chat.create(
    messages=[
        {"role": "user", "content": "What is machine learning?"}
    ]
)
print(response.content)

# AI Writer
content = client.writer.generate(
    prompt="Write a blog post about AI trends in 2026",
    content_type="blog_post"
)
print(content.text)

# Image Generation
image = client.image.generate(
    prompt="A futuristic city at sunset",
    size="1024x1024"
)
image.save("city.png")
```

## Features

- 🤖 **Chat Completions** - Conversational AI with multiple models
- ✍️ **AI Writer** - Generate blogs, articles, social posts, and more
- 🎨 **Image Generation** - Text-to-image, image-to-image, upscaling
- 🔊 **Audio** - Text-to-speech and speech-to-text
- 📈 **Trend Discovery** - Track trends across YouTube, TikTok, Reddit, and more
- 📊 **Market Intelligence** - Stock and crypto data with AI analysis
- 📄 **Document Processing** - Upload, convert, and chat with documents
- ⚡ **Async Support** - Full async/await support for high-performance apps

## Authentication

Get your API key from [nemati.ai/dashboard/api-keys](https://nemati.ai/dashboard/api-keys).

```python
# Option 1: Pass directly
client = NematiAI(api_key="nai_live_xxxxxxxxxxxx")

# Option 2: Environment variable
# Set NEMATI_API_KEY in your environment
client = NematiAI()
```

## Usage Examples

### Chat Completions

```python
# Simple chat
response = client.chat.create(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing"}
    ],
    model="gpt-4",
    max_tokens=1000
)

print(response.content)
print(f"Tokens used: {response.usage.total_tokens}")

# Streaming
for chunk in client.chat.create(
    messages=[{"role": "user", "content": "Write a poem about AI"}],
    stream=True
):
    print(chunk.content, end="", flush=True)
```

### AI Writer

```python
# Generate content
content = client.writer.generate(
    prompt="Write a product description for an AI assistant app",
    content_type="product_description",
    tone="professional",
    max_tokens=500
)

# Use templates
templates = client.writer.templates.list()
content = client.writer.templates.generate(
    template_id="social-media-post",
    variables={
        "topic": "AI trends",
        "platform": "LinkedIn"
    }
)
```

### Image Generation

```python
# Text to image
image = client.image.generate(
    prompt="A serene mountain landscape at dawn",
    size="1024x1024",
    quality="hd"
)
image.save("landscape.png")

# Image to image
edited = client.image.edit(
    image=open("photo.jpg", "rb"),
    prompt="Make it look like a watercolor painting"
)

# Upscale
upscaled = client.image.upscale(
    image=open("small.jpg", "rb"),
    scale=4
)
```

### Trend Discovery

```python
# Search trends
trends = client.trends.search(
    query="artificial intelligence",
    platforms=["youtube", "tiktok", "reddit"],
    timeframe="7d"
)

for trend in trends.items:
    print(f"{trend.platform}: {trend.title}")
    print(f"  Engagement: {trend.engagement}")
```

### Async Support

```python
import asyncio
from nemati import AsyncNematiAI

async def main():
    client = AsyncNematiAI(api_key="your-api-key")
    
    response = await client.chat.create(
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.content)
    
    await client.close()

asyncio.run(main())
```

### Error Handling

```python
from nemati.exceptions import (
    AuthenticationError,
    RateLimitError,
    InsufficientCreditsError,
    ValidationError,
    APIError
)

try:
    response = client.chat.create(messages=[...])
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except InsufficientCreditsError as e:
    print(f"Need {e.required} credits, have {e.available}")
except ValidationError as e:
    print(f"Invalid request: {e.errors}")
except APIError as e:
    print(f"API error {e.status_code}: {e.message}")
```

### Account & Usage

```python
# Check credits
credits = client.account.credits()
print(f"Remaining: {credits.remaining}")

# Get usage stats
usage = client.account.usage(
    start_date="2026-01-01",
    end_date="2026-01-31"
)
print(f"Total requests: {usage.total_requests}")

# Get plan limits
limits = client.account.limits()
print(f"Chat messages/day: {limits.chat.max_messages_per_day}")
```

## Documentation

Full documentation is available at [docs.nemati.ai/sdk/python](https://docs.nemati.ai/sdk/python)

## Requirements

- Python 3.8+
- API key from [nemati.ai](https://nemati.ai)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- 📧 Email: support@nemati.ai
- 💬 Discord: [discord.gg/nemati](https://discord.gg/nemati/KrFTV64NvS)
- 🐛 Issues: [GitHub Issues](https://github.com/nematiai/nemati-ai/issues)
