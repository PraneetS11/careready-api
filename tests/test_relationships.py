from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Site, SiteTag, User
from app.schemas.site_notes import SiteNoteCreate
from app.schemas.sites import SiteCreate
from app.services.site_notes import SiteNoteService
from app.services.site_tags import SiteTagService
from app.services.sites import SiteService


@pytest.mark.asyncio
async def test_note_unknown_site_is_404():
    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = None
    with pytest.raises(HTTPException) as error:
        await SiteNoteService().create_note(
            uuid4(), uuid4(), SiteNoteCreate(text="Fictional equipment check"), session
        )
    assert error.value.status_code == 404
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_note_author_cannot_be_spoofed():
    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = Site()
    user_id, site_id = uuid4(), uuid4()
    data = SiteNoteCreate(text="Fictional equipment check", author_user_id=uuid4())
    note = await SiteNoteService().create_note(site_id, user_id, data, session)
    assert note.author_user_id == user_id
    assert note.site_id == site_id


@pytest.mark.asyncio
async def test_notes_are_filtered_by_site():
    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = Site()
    session.execute.return_value = MagicMock()
    site_id = uuid4()
    await SiteNoteService().list_notes(site_id, session)
    statement = session.execute.call_args.args[0]
    assert site_id in statement.compile().params.values()
    assert "sitenote.site_id =" in str(statement)


@pytest.mark.asyncio
async def test_tag_attachment_uses_conflict_safe_insert():
    session = AsyncMock(spec=AsyncSession)
    session.get.side_effect = [Site(), SiteTag(name="Fictional")]
    await SiteTagService().attach_tag(uuid4(), uuid4(), session)
    assert "ON CONFLICT DO NOTHING" in str(session.execute.call_args.args[0])


@pytest.mark.asyncio
async def test_tag_attachment_unknown_tag_is_404():
    session = AsyncMock(spec=AsyncSession)
    session.get.side_effect = [Site(), None]
    with pytest.raises(HTTPException) as error:
        await SiteTagService().attach_tag(uuid4(), uuid4(), session)
    assert error.value.status_code == 404
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_site_creator_comes_from_current_user():
    session = AsyncMock(spec=AsyncSession)
    user = User(email="fictional@example.com")
    data = SiteCreate(
        name="Fictional", city="Hamilton", timezone="America/Toronto", created_by_user_id=uuid4()
    )
    site = await SiteService().create_site(data, session, creator=user)
    assert site.created_by_user_id == user.id
    assert site.creator is user
