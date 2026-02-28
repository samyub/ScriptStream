import uuid
import re
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from app.sources.base import ContentSource, ContentItem


class RedditSource(ContentSource):
    source_name = "reddit"

    def scrape(self, url: str, keywords: list[str], time_window: str = "7d") -> list[ContentItem]:
        items = []

        if "reddit.com" in url:
            # Convert to old reddit for easier parsing
            old_url = url.replace("www.reddit.com", "old.reddit.com")
            items.extend(self._scrape_page(old_url, keywords))
        else:
            # Search Reddit
            time_map = {"24h": "day", "7d": "week", "14d": "month", "30d": "month"}
            reddit_time = time_map.get(time_window, "week")
            search_query = quote_plus(" ".join(keywords))
            search_url = f"https://old.reddit.com/search?q={search_query}&sort=relevance&t={reddit_time}"
            items.extend(self._scrape_page(search_url, keywords))

        return items

    def _scrape_page(self, url: str, keywords: list[str]) -> list[ContentItem]:
        html = self._safe_request(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        items = []

        # old.reddit.com uses div.thing for each post
        posts = soup.select("div.thing.link")
        if not posts:
            # Fallback: try other selectors
            posts = soup.select("[data-fullname]")

        for post in posts[:20]:
            try:
                # Title
                title_el = post.select_one("a.title, a.search-title")
                title = title_el.get_text(strip=True) if title_el else ""
                post_url = title_el.get("href", "") if title_el else ""
                if post_url and not post_url.startswith("http"):
                    post_url = f"https://old.reddit.com{post_url}"

                # Author
                author_el = post.select_one("a.author")
                author = author_el.get_text(strip=True) if author_el else "[deleted]"

                # Score
                score_el = post.select_one("div.score.unvoted, span.score.unvoted")
                score_text = score_el.get_text(strip=True) if score_el else "0"
                score = self._parse_score(score_text)

                # Comments
                comments_el = post.select_one("a.comments")
                comments_text = comments_el.get_text(strip=True) if comments_el else "0"
                comments_match = re.search(r'(\d+)', comments_text)
                comments = int(comments_match.group(1)) if comments_match else 0

                # Time
                time_el = post.select_one("time")
                published = time_el.get("datetime", "") if time_el else ""

                # Subreddit
                sub_el = post.select_one("a.subreddit")
                subreddit = sub_el.get_text(strip=True) if sub_el else ""

                if title:
                    items.append(ContentItem(
                        id=str(uuid.uuid4()),
                        source="reddit",
                        url=post_url,
                        title=title,
                        author=author,
                        published_at=published,
                        extracted_text=title,
                        engagement={"score": score, "comments": comments},
                        raw_metadata={"subreddit": subreddit},
                    ))
            except Exception:
                continue

        return items

    @staticmethod
    def _parse_score(text: str) -> int:
        text = text.strip().lower().replace(",", "")
        if text in ("•", "-", ""):
            return 0
        try:
            if "k" in text:
                return int(float(text.replace("k", "")) * 1000)
            return int(text)
        except ValueError:
            return 0
