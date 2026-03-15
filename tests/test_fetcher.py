import httpx
from unittest.mock import MagicMock, patch
from mcp_agno.fetcher import fetch_page

SAMPLE_HTML = """
<html><body>
  <h1>Agents</h1>
  <p>Build intelligent agents with <b>tools</b> and memory.</p>
  <a href="/other">Link</a>
</body></html>
"""

def test_fetch_returns_plain_text():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.text = SAMPLE_HTML

    with patch("mcp_agno.fetcher.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.get.return_value = mock_resp
        result = fetch_page("https://docs.agno.com/agents")

    assert "Agents" in result
    assert "Build intelligent agents" in result
    # Links should not appear (ignore_links=True)
    assert "href" not in result
    assert "/other" not in result

def test_fetch_network_error_returns_error_string():
    with patch("mcp_agno.fetcher.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.get.side_effect = httpx.TimeoutException("timeout")
        result = fetch_page("https://docs.agno.com/agents")

    assert result.startswith("Error:")
    assert "docs.agno.com/agents" in result

def test_fetch_http_error_returns_error_string():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404", request=MagicMock(), response=MagicMock(status_code=404)
    )
    with patch("mcp_agno.fetcher.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.get.return_value = mock_resp
        result = fetch_page("https://docs.agno.com/missing")

    assert result.startswith("Error:")
