import pytest

from telegram_easy.aio import get_updates
from utl_test import remove_env_vars


@pytest.mark.asyncio
async def test_get_updates_error():
    remove_env_vars()

    with pytest.raises(ValueError):
        await get_updates()

    try:
        updates = await get_updates(token="123")
        assert updates['ok'] == False, f"Invalid token should return error: {updates}"
    except ValueError:
        pytest.fail("ValueError raised when it shouldn't have")
