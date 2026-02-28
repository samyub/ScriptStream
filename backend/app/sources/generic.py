import uuid
from bs4 import BeautifulSoup

from app.sources.base import ContentSource, ContentItem


class GenericSource(ContentSource):
    source_name = "generic"

    def scrape(self, url: str, keywords: list[str], time_window: str = "7d") -> list[ContentItem]:
        html = self._safe_request(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")

        # Remove script and style tags
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # Page title
        title = soup.title.get_text(strip=True) if soup.title else url

        # Extract headings
        headings = []
        for h in soup.find_all(["h1", "h2", "h3"]):
            text = h.get_text(strip=True)
            if text:
                headings.append(text)

        # Extract main content paragraphs
        paragraphs = []
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if text and len(text) > 30:
                paragraphs.append(text)

        # Extract links with text
        links = []
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            if text and len(text) > 10:
                links.append({"text": text, "href": a.get("href", "")})

        extracted_text = "\n\n".join(
            [f"# {title}"]
            + [f"## {h}" for h in headings[:10]]
            + paragraphs[:20]
        )

        return [
            ContentItem(
                id=str(uuid.uuid4()),
                source="generic",
                url=url,
                title=title,
                extracted_text=extracted_text[:3000],
                engagement={},
                raw_metadata={
                    "headings": headings[:10],
                    "link_count": len(links),
                },
            )
        ]
