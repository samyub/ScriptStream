import re
import uuid
import json
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from app.sources.base import ContentSource, ContentItem


class YouTubeSource(ContentSource):
    source_name = "youtube"

    def scrape(self, url: str, keywords: list[str], time_window: str = "7d") -> list[ContentItem]:
        items = []

        # If it's a direct YouTube URL, scrape that page
        if "youtube.com" in url or "youtu.be" in url:
            items.extend(self._scrape_page(url, keywords))
        else:
            # Treat as search keywords
            search_query = quote_plus(" ".join(keywords))
            search_url = f"https://www.youtube.com/results?search_query={search_query}"
            items.extend(self._scrape_page(search_url, keywords))

        return items

    def _scrape_page(self, url: str, keywords: list[str]) -> list[ContentItem]:
        html = self._safe_request(url)
        if not html:
            return []

        items = []
        # YouTube embeds data in JSON within script tags
        try:
            # Extract ytInitialData JSON
            pattern = r'var ytInitialData\s*=\s*({.*?});</script>'
            match = re.search(pattern, html, re.DOTALL)
            if not match:
                # Try alternate pattern
                pattern = r'ytInitialData\s*=\s*({.*?});\s*</script>'
                match = re.search(pattern, html, re.DOTALL)

            if match:
                data = json.loads(match.group(1))
                items = self._extract_from_initial_data(data, keywords)
        except (json.JSONDecodeError, KeyError):
            pass

        # Fallback: basic HTML parsing
        if not items:
            items = self._fallback_parse(html, keywords)

        return items

    def _extract_from_initial_data(self, data: dict, keywords: list[str]) -> list[ContentItem]:
        items = []
        try:
            # Navigate through search results
            contents = (
                data.get("contents", {})
                .get("twoColumnSearchResultsRenderer", {})
                .get("primaryContents", {})
                .get("sectionListRenderer", {})
                .get("contents", [])
            )

            for section in contents:
                item_section = section.get("itemSectionRenderer", {}).get("contents", [])
                for entry in item_section:
                    video = entry.get("videoRenderer")
                    if not video:
                        continue

                    video_id = video.get("videoId", "")
                    title_runs = video.get("title", {}).get("runs", [])
                    title = " ".join(r.get("text", "") for r in title_runs)

                    channel_runs = video.get("ownerText", {}).get("runs", [])
                    author = " ".join(r.get("text", "") for r in channel_runs)

                    view_text = video.get("viewCountText", {}).get("simpleText", "0 views")
                    views = self._parse_view_count(view_text)

                    published = video.get("publishedTimeText", {}).get("simpleText", "")

                    snippet_runs = video.get("detailedMetadataSnippets", [{}])
                    snippet_text = ""
                    if snippet_runs:
                        snippet_runs_inner = snippet_runs[0].get("snippetText", {}).get("runs", [])
                        snippet_text = " ".join(r.get("text", "") for r in snippet_runs_inner)

                    items.append(ContentItem(
                        id=str(uuid.uuid4()),
                        source="youtube",
                        url=f"https://www.youtube.com/watch?v={video_id}",
                        title=title,
                        author=author,
                        published_at=published,
                        extracted_text=snippet_text or title,
                        engagement={"views": views, "view_text": view_text},
                        raw_metadata={"video_id": video_id},
                    ))
        except Exception:
            pass
        return items

    def _fallback_parse(self, html: str, keywords: list[str]) -> list[ContentItem]:
        """Fallback parsing using regex patterns for video data in page source."""
        items = []
        # Try to find video entries in the raw JSON
        video_pattern = r'"videoId":"([^"]+)".*?"text":"([^"]*?)"'
        matches = re.finditer(video_pattern, html)

        seen_ids = set()
        for match in matches:
            video_id = match.group(1)
            if video_id in seen_ids or len(video_id) != 11:
                continue
            seen_ids.add(video_id)
            title = match.group(2)
            if not title or len(title) < 5:
                continue

            items.append(ContentItem(
                id=str(uuid.uuid4()),
                source="youtube",
                url=f"https://www.youtube.com/watch?v={video_id}",
                title=title,
                extracted_text=title,
                engagement={"views": 0},
                raw_metadata={"video_id": video_id},
            ))
            if len(items) >= 20:
                break

        return items

    @staticmethod
    def _parse_view_count(text: str) -> int:
        text = text.lower().replace(",", "").replace(" views", "").replace(" view", "").strip()
        try:
            if "k" in text:
                return int(float(text.replace("k", "")) * 1000)
            elif "m" in text:
                return int(float(text.replace("m", "")) * 1_000_000)
            elif "b" in text:
                return int(float(text.replace("b", "")) * 1_000_000_000)
            return int(text) if text.isdigit() else 0
        except ValueError:
            return 0
