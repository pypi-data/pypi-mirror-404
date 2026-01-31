import pytest

from kiarina.lib.firebase.rtdb import get_data


async def test_unauthorized(database_url, id_token) -> None:
    with pytest.raises(Exception, match="401"):
        await get_data(database_url, "/posts/other_user", id_token)


async def test_happy_path(database_url, user_id, id_token) -> None:
    data = await get_data(database_url, f"/posts/{user_id}", id_token)
    assert isinstance(data, dict)
    assert data.get("content") == "hello"
