from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ContentItem(BaseModel):
    id: str = ""
    source: str = "generic"  # youtube | reddit | generic
    url: str = ""
    title: str = ""
    author: str = ""
    published_at: Optional[str] = None
    extracted_text: str = ""
    engagement: dict = Field(default_factory=dict)
    raw_metadata: dict = Field(default_factory=dict)
    relevance_score: float = 0.0


class ContentSource(ABC):
    source_name: str = "generic"

    @abstractmethod
    def scrape(self, url: str, keywords: list[str], time_window: str = "7d") -> list[ContentItem]:
        """Scrape the given URL and return content items."""
        pass

    def _safe_request(self, url: str, headers: dict = None) -> Optional[str]:
        import requests
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        if headers:
            default_headers.update(headers)
        try:
            resp = requests.get(url, headers=default_headers, timeout=15)
            resp.raise_for_status()
            return resp.text
        except Exception:
            return None
