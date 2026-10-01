from uuid import UUID

import pytest
from pydantic import ValidationError

from app.models.sites import Site
from app.schemas.sites import SiteCreate, SiteRead, SiteUpdate


def test_site_identity_and_schema_boundary():
    values = {"name": "Test office", "city": "Hamilton", "timezone": "America/Toronto"}
    first, second = Site(**values), Site(**values)
    assert isinstance(first.id, UUID)
    assert first.id != second.id
    assert first.active is True
    assert "id" not in SiteCreate.model_fields
    assert SiteRead.model_validate(first).id == first.id
    with pytest.raises(ValidationError):
        SiteRead(**values)
    assert SiteUpdate(active=False).model_dump() == {"active": False}
