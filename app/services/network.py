from datetime import timedelta, timezone
from zoneinfo import ZoneInfo

from app.schemas.network import CITIES


def occurrences(data):
    local = data.starts_at.astimezone(ZoneInfo(CITIES[data.city][2]))
    result = []
    for week in range(data.occurrences):
        candidate = local + timedelta(weeks=week)
        # Reject a DST gap rather than silently shifting the promised wall time.
        if candidate.astimezone(timezone.utc).astimezone(candidate.tzinfo).replace(
            tzinfo=None
        ) != candidate.replace(tzinfo=None):
            raise ValueError(
                "A recurring visit falls in a daylight-saving gap; choose another time"
            )
        result.append(candidate.astimezone(timezone.utc))
    return result


def eligible(profile, visit):
    return bool(
        profile
        and profile.approved
        and profile.agency_id == visit.agency_id
        and profile.experience >= visit.min_experience
        and visit.service in profile.services
    )


def overlaps(a, b):
    # A fixed 30-minute travel buffer keeps the initial scheduling rule transparent.
    return a.starts_at < b.starts_at + timedelta(
        minutes=b.duration_minutes + 30
    ) and b.starts_at < a.starts_at + timedelta(minutes=a.duration_minutes + 30)


def visit_view(visit, user, profile=None):
    data = visit.model_dump()
    private = (
        user.role == "requester"
        and visit.requester_id == user.id
        or user.role == "agency"
        or visit.provider_id == user.id
    )
    if not private:
        for key in ("recipient", "address", "notes", "requester_id"):
            data.pop(key, None)
    data["preference_match"] = bool(
        profile and visit.gender_preference != "any" and profile.gender == visit.gender_preference
    )
    data["language_match"] = bool(profile and visit.preferred_language in profile.languages)
    return data
