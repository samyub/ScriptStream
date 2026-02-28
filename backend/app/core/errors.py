class ResearchError(Exception):
    """Base exception for research operations."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ScrapingError(ResearchError):
    """Raised when scraping a source fails."""
    def __init__(self, message: str, source: str = "unknown"):
        self.source = source
        super().__init__(f"Scraping error [{source}]: {message}", 502)


class LLMError(ResearchError):
    """Raised when LLM call fails."""
    def __init__(self, message: str):
        super().__init__(f"LLM error: {message}", 503)


class StorageError(ResearchError):
    """Raised when local storage operation fails."""
    def __init__(self, message: str):
        super().__init__(f"Storage error: {message}", 500)
