
# 🚀 BROKENXAPI

**Official async Python SDK & CLI for BrokenX YouTube API**
Built by **Broken X Network**

BROKENXAPI developers ko YouTube search aur media processing (audio/video) ke liye ek **fast, async aur secure API** provide karta hai —
jisme **SDK + CLI dono** available hain.

---

## ✨ Features

* ⚡ Async Python SDK (aiohttp based)
* 🖥️ Built-in CLI (`brokenx`)
* 🔑 Secure API-key authentication
* 🎵 Audio & 🎬 Video support
* ☁️ Telegram-based media delivery
* 🚀 Server-side caching & rate limits
* 🧱 Clean, production-ready packaging

---

## 📦 Installation

```bash
pip install BROKENXAPI
```

Verify installation:

```bash
brokenx -v
```

---

## 🔑 Authentication (One-time)

CLI ke through **ek baar API key authenticate** karni hoti hai:

```bash
brokenx auth BROKENXAPI-XXXX
```

### 🔐 How it works

* API key securely local machine par store hoti hai
* Uske baad har command automatically authenticated hoti hai
* Environment variables ki zarurat nahi

---

## 📟 Command Line Interface (CLI)

BROKENXAPI with powerful CLI :

### 🔢 Version

```bash
brokenx -v
```

---

### 🔍 Search YouTube

```bash
brokenx search "lofi beats"
```

Returns:

* title
* video_id
* duration
* thumbnail
* temporary stream URL

---

### 🎵 Download Audio

```bash
brokenx download VIDEO_ID
```

Default mode **audio** hota hai.

---

### 🎬 Download Video

```bash
brokenx download VIDEO_ID -v
```

`-v` flag use karke video download hota hai.

---

## 🐍 Python SDK Usage

### Basic Example

```python
import asyncio
from brokenxapi import BrokenXAPI

async def main():
    async with BrokenXAPI(api_key="BROKENXAPI-XXXX") as api:
        result = await api.search("Arijit Singh")
        print(result)

asyncio.run(main())
```

---

### Download Example

```python
async with BrokenXAPI(api_key="BROKENXAPI-XXXX") as api:
    audio = await api.download("VIDEO_ID", "audio")
    video = await api.download("VIDEO_ID", "video")
```

---

## 🧠 How Authentication Works

* API key har request ke saath backend par verify hoti hai
* Rate limits server-side enforce hote hain
* Invalid / expired key par request reject ho jaati hai

---

## 📚 Documentation

📘 **Full Docs:**
👉 [DOCS](https://brokenxapi-docs.vercel.app) 

---

## ⚠️ Important Notes

* Media files **Telegram** ke through deliver hote hain
* Stream URLs **temporary** hote hain
* Rate limits API key ke type par depend karte hain
* SDK async hai — `async/await` required

---
---

## 🔒 Security & Licensing

* Core client logic intentionally compiled (`.pyc`)
* No sensitive keys repo me store nahi hoti
* License: **MIT**

---

## 🤝 Contributing

Currently BROKENXAPI core is maintained by **Broken X Network**.
Issues, feature requests aur suggestions welcome hain:

👉 [DROP ISSUES](https://github.com/mrxbroken011/BROKENXAPI/issues)

---

## 🏁 Roadmap (High-level)

* ✅ SDK + CLI
* 🔜 Advanced CLI flags
* 🔜 Improved docs & examples
* 🔜 Multi-profile auth support
* 🔜 Production backend scaling

---

## © License

MIT License
© 2025–2026 **MR BROKEN**

---



