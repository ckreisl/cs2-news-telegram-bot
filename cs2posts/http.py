from __future__ import annotations

import atexit
import logging
import threading

import httpx

logger = logging.getLogger(__name__)

# One timeout for every outbound HTTP call this package makes. Previously
# duplicated as CRAWLER_REQUEST_TIMEOUT and REQUESTS_TIMEOUT.
HTTP_TIMEOUT_SECONDS = 10.0
USER_AGENT = "cs2-news-telegram-bot"

METHOD_NOT_ALLOWED = 405

_client: httpx.Client | None = None
_client_lock = threading.Lock()


def client() -> httpx.Client:
    """The process-wide pooled HTTP client for blocking calls.

    Message rendering probes one URL per image; without pooling a carousel
    costs a TLS handshake per picture. Created lazily so importing the package
    opens no sockets.
    """
    global _client
    with _client_lock:
        if _client is None:
            _client = httpx.Client(
                timeout=HTTP_TIMEOUT_SECONDS,
                headers={"User-Agent": USER_AGENT},
            )
        return _client


def close_client() -> None:
    global _client
    with _client_lock:
        if _client is not None:
            _client.close()
            _client = None


atexit.register(close_client)


def head_or_get(url: str) -> httpx.Response:
    """HEAD ``url``, following redirects, falling back to GET.

    Steam's CDNs answer some paths with 405 for HEAD; the GET fallback keeps
    those usable. Shared by the URL validator and the redirect resolver, which
    previously carried two copies of this logic.
    """
    response = client().head(url, follow_redirects=True)
    if response.status_code == METHOD_NOT_ALLOWED:
        response = client().get(url, follow_redirects=True)
    return response
