import httpx

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

DEFAULT_TIMEOUT = 10.0 
DEFAULT_MAX_CONNECTIONS = 50 
DEFAULT_MAX_KEEPALIVE_CONNECTIONS = 20 


def create_http_client() -> httpx.AsyncClient:
    """
    Create a configured httpx.AsyncClient.
    
    Returns:
        httpx.AsyncClient with proper timeout, limits, and headers configured.
    """
    limits = httpx.Limits(
        max_connections=DEFAULT_MAX_CONNECTIONS,
        max_keepalive_connections=DEFAULT_MAX_KEEPALIVE_CONNECTIONS,
    )
    
    timeout = httpx.Timeout(DEFAULT_TIMEOUT)
    
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
    }
    
    return httpx.AsyncClient(
        limits=limits,
        timeout=timeout,
        headers=headers,
        follow_redirects=True,
        trust_env=True,
    )
