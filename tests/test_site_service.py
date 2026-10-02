import unittest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import SiteNotFound
from app.services.sites import SiteService


class MissingSiteServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_missing_site_raises_without_writing(self):
        session = AsyncMock(spec=AsyncSession)
        session.execute.return_value = MagicMock()
        session.execute.return_value.scalars.return_value.first.return_value = None
        with self.assertRaises(SiteNotFound):
            await SiteService().get_site(uuid4(), session)
        session.commit.assert_not_awaited()
