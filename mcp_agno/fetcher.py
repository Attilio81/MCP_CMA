import html2text
import httpx

_converter = html2text.HTML2Text()
_converter.ignore_links = True
_converter.ignore_images = True
_converter.body_width = 0


def fetch_page(url: str) -> str:
    """Fetch a URL and return its content as plain text. Returns 'Error: ...' on failure."""
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            return _converter.handle(response.text)
    except httpx.HTTPStatusError as exc:
        return f"Error: could not fetch {url}: HTTP {exc.response.status_code}"
    except Exception as exc:
        return f"Error: could not fetch {url}: {exc}"
