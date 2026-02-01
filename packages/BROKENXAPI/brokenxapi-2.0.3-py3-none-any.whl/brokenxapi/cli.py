import argparse
import asyncio
from .client import BrokenXAPI
from .auth import get_key, save_key
from .__version__ import __version__

def main():
    parser = argparse.ArgumentParser("brokenx")
    parser.add_argument("-v", "--version", action="store_true")

    sub = parser.add_subparsers(dest="cmd")

    auth = sub.add_parser("auth")
    auth.add_argument("key")

    search = sub.add_parser("search")
    search.add_argument("query")

    dl = sub.add_parser("download")
    dl.add_argument("video_id")
    dl.add_argument("-v", "--video", action="store_true")

    args = parser.parse_args()

    if args.version:
        print(__version__)
        return

    if args.cmd == "auth":
        save_key(args.key)
        print("✅ API key saved")
        return

    api_key = get_key()
    if not api_key:
        print("❌ Please run: brokenx auth <API_KEY>")
        return

    asyncio.run(run(args, api_key))


async def run(args, api_key):
    async with BrokenXAPI(api_key) as api:
        if args.cmd == "search":
            res = await api.search(args.query)
            print(res)

        elif args.cmd == "download":
            media = "video" if args.video else "audio"
            res = await api.download(args.video_id, media)
            print(res["telegram_url"])
