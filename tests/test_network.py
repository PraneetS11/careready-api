from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.network import CareVisit
from app.schemas.network import Register, VisitCreate
from app.services.network import eligible, occurrences, overlaps, visit_view


def request_data(**kwargs):
    return VisitCreate(
        agency_id=uuid4(),
        service="companionship",
        recipient="Fictional recipient",
        address="Fictional address",
        city="Toronto",
        starts_at=datetime.now(timezone.utc) + timedelta(days=2),
        consent_confirmed=True,
        **kwargs,
    )


def test_recurrence_preserves_local_time_across_dst():
    data = request_data(occurrences=3)
    data.starts_at = datetime(2027, 3, 7, 15, tzinfo=timezone.utc)
    dates = occurrences(data)
    assert dates[0].hour == 15 and dates[1].hour == 14 and dates[2].hour == 14


def test_dst_gap_rejected():
    data = request_data(occurrences=2)
    data.starts_at = datetime(2027, 3, 7, 7, 30, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        occurrences(data)


def test_profile_rules_and_optional_preferences():
    agency = uuid4()
    profile = SimpleNamespace(approved=True, agency_id=agency, experience=2, services=["nursing"])
    visit = SimpleNamespace(agency_id=agency, min_experience=2, service="nursing")
    assert eligible(profile, visit)
    profile.experience = 1
    assert not eligible(profile, visit)
    profile.experience = 2
    profile.approved = False
    assert not eligible(profile, visit)
    profile.approved = True
    profile.agency_id = uuid4()
    assert not eligible(profile, visit)


def test_unassigned_provider_never_sees_private_fields():
    visit = CareVisit(
        agency_id=uuid4(),
        requester_id=uuid4(),
        recipient="Private",
        address="Private street",
        notes="Private notes",
        service="companionship",
        city="Toronto",
        timezone="America/Toronto",
        latitude=43.65,
        longitude=-79.38,
        starts_at=datetime.now(timezone.utc),
        duration_minutes=60,
    )
    provider = SimpleNamespace(id=uuid4(), role="provider")
    view = visit_view(visit, provider)
    assert not {"recipient", "address", "notes", "requester_id"} & view.keys()
    visit.provider_id = provider.id
    assert visit_view(visit, provider)["address"] == "Private street"


def test_travel_buffer():
    start = datetime.now(timezone.utc)
    a = SimpleNamespace(starts_at=start, duration_minutes=60)
    assert overlaps(
        a, SimpleNamespace(starts_at=start + timedelta(minutes=89), duration_minutes=30)
    )
    assert not overlaps(
        a, SimpleNamespace(starts_at=start + timedelta(minutes=90), duration_minutes=30)
    )


def test_signup_cannot_escalate_to_admin():
    with pytest.raises(ValidationError):
        Register(email="test@example.com", password="example-password", name="Test", role="admin")


def test_language_and_preferences_validated():
    data = request_data(preferred_language="French", communication="slow_clear", pets_present=True)
    assert data.preferred_language == "French"
    with pytest.raises(ValidationError):
        request_data(preferred_language="invented-language")
    with pytest.raises(ValidationError):
        request_data(occurrences=100)
