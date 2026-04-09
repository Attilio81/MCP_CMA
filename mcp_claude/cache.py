class Cache:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def get(self, url: str) -> str | None:
        return self._store.get(url)

    def set(self, url: str, content: str) -> None:
        self._store[url] = content
