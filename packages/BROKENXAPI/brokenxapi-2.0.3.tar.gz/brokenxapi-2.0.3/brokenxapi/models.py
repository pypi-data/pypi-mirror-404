from typing import TypedDict

class DownloadResponse(TypedDict, total=False):
    success: bool
    status: str
    video_id: str
    type: str
    telegram_url: str
    thumbnail: str
    source: str

class SearchResponse(TypedDict, total=False):
    success: bool
    status: str
    title: str
    video_id: str
    duration: str
    thumbnail: str
    stream_url: str
