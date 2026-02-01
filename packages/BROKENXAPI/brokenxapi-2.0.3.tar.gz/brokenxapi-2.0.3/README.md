# BROKENXAPI

**BROKENXAPI** is a high-performance asynchronous **Python SDK and CLI** that enables developers to search and download YouTube audio or video through a remote backend API.

It is built for **automation tools**, **Telegram bots**, and **production systems** where reliability, speed, and a clean developer experience are critical.

The SDK abstracts authentication and networking, while the CLI provides a fast and simple way to interact with the API directly from the terminal.

---

<p align="center">
  <img src="./docs/brokenx.gif" width="600" />
</p>

---

## Installation

Install via pip:

```bash
pip install BROKENXAPI
````

---

## Authentication

BROKENXAPI requires an API key for all requests.

### Environment Variable (Recommended)

**Linux / macOS**

```bash
export YTKEY="BROKENXAPI-XXXX"
```

**Windows**

```bat
set YTKEY=BROKENXAPI-XXXX
```

---

## Python SDK Usage

```python
import asyncio
from brokenxapi import BrokenXAPI

async def main():
    async with BrokenXAPI(api_key="BROKENXAPI-XXXX") as api:
        # Search YouTube
        search = await api.search("moosetape", video=False)
        video_id = search["video_id"]

        # Download audio
        audio = await api.download(video_id, "audio")
        print(audio["telegram_url"])

asyncio.run(main())
```

---

## Download Video (SDK)

```python
async with BrokenXAPI(api_key="BROKENXAPI-XXXX") as api:
    video = await api.download("VIDEO_ID", "video")
    print(video["telegram_url"])
```

---

## CLI Usage

Authenticate once:

```bash
brokenx auth BROKENXAPI-XXXX
```

Check installed version:

```bash
brokenx -v
```

Search YouTube:

```bash
brokenx search "moosetape"
```

Download audio:

```bash
brokenx download VIDEO_ID
```

Download video:

```bash
brokenx download VIDEO_ID -v
```

---

## Notes

* Python **3.8+** is required
* An API key is mandatory for all requests
* All responses are returned as JSON-compatible dictionaries
* Download responses include a **Telegram-ready file URL**

---

## License

© 2025 **MR Broken**
All rights reserved.

---
