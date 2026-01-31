from typing import Any

import httpx


async def get_data(
    database_url: str,
    path: str,
    id_token: str,
) -> Any:
    """
    Get data from Firebase Realtime Database.

    Args:
        database_url: Firebase database URL (e.g., "https://my-project.firebaseio.com")
        path: Database path to get data from (e.g., "/users/user123")
        id_token: Firebase ID token for authentication

    Returns:
        Data at the specified path (dict, list, str, int, float, bool, or None)

    Raises:
        httpx.HTTPError: If request fails

    Example:
        >>> from kiarina.lib.firebase.rtdb import get_data
        >>>
        >>> # With TokenManager
        >>> from kiarina.lib.firebase.auth import TokenManager
        >>> manager = TokenManager(refresh_token="...", api_key="...")
        >>> id_token = await manager.get_id_token()
        >>> data = await get_data(
        ...     "https://my-project.firebaseio.com",
        ...     "/users/user123",
        ...     id_token
        ... )
        >>> print(data)  # {"name": "John", "age": 30}
        >>>
        >>> # Or with direct token
        >>> data = await get_data(
        ...     "https://my-project.firebaseio.com",
        ...     "/users/user123",
        ...     "your_id_token_here"
        ... )
    """
    url = f"{database_url.rstrip('/')}{path}.json"
    params = {"auth": id_token}

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()
