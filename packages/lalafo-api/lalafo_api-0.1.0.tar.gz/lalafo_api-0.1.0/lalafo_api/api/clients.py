import httpx
from typing import Optional


_async_client: Optional[httpx.AsyncClient] = None
_sync_client: Optional[httpx.Client] = None


def get_async_client() -> httpx.AsyncClient:
    """Получить асинхронный клиент"""
    global _async_client
    
    if _async_client is None or _async_client.is_closed:
        _async_client = httpx.AsyncClient(base_url="https://api.lalafo.com")
    return _async_client


def get_sync_client() -> httpx.Client:
    """Получить синхронный клиент"""
    global _sync_client
    
    if _sync_client is None or _sync_client.is_closed:
        _sync_client = httpx.Client(base_url="https://api.lalafo.com")
    return _sync_client