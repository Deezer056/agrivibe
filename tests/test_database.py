import asyncio

import pytest

from agrivibe.core.database import UNREADABLE, open_database, where

SECRET = "s3cret-password"
URL = f"postgresql://owner:{SECRET}@ep-example.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"


def test_where_shows_the_host_and_database_only():
    assert where(URL) == "ep-example.ap-southeast-1.aws.neon.tech/neondb"


@pytest.mark.parametrize("broken", [f'"{URL}"', f"'{URL}'", "not a url", ""])
def test_where_never_echoes_an_unreadable_url(broken):
    assert where(broken) == UNREADABLE


def test_a_quoted_url_fails_before_connecting_without_the_password():
    async def open_quoted():
        async with open_database(f'"{URL}"'):
            pass

    with pytest.raises(RuntimeError) as error:
        asyncio.run(open_quoted())

    assert SECRET not in str(error.value)
    assert "quotes" in str(error.value)
