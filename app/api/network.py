from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import RoleChecker, get_current_user
from app.api.email_routes import send_account_link, settings_for
from app.core.security import hash_password
from app.db.session import get_session
from app.models.network import Agency, CareDevice, CareEvent, CareProfile, CareVisit
from app.models.users import User
from app.schemas.network import (
    CITIES,
    SERVICES,
    Approval,
    DeviceCreate,
    DeviceState,
    Register,
    Transition,
    VisitCreate,
)
from app.services.network import eligible, occurrences, overlaps, visit_view

router = APIRouter()
network_user = RoleChecker(["requester", "provider", "agency"])


async def agency_for(user, session):
    agency = (
        (await session.execute(select(Agency).where(Agency.owner_id == user.id))).scalars().first()
    )
    if user.role != "agency" or agency is None:
        raise HTTPException(403, "An agency account is required")
    return agency


async def verified_agency(agency_id, session):
    agency = await session.get(Agency, agency_id)
    owner = await session.get(User, agency.owner_id) if agency else None
    if not owner or not owner.is_verified or not owner.is_active:
        raise HTTPException(422, "Select an active, verified agency")
    return agency


@router.get("/catalog")
async def catalog():
    return {
        "services": SERVICES,
        "cities": {
            k: {"latitude": v[0], "longitude": v[1], "timezone": v[2]} for k, v in CITIES.items()
        },
        "experience_levels": ["New to care", "1–2 years", "3–5 years", "6+ years"],
        "languages": [
            "English",
            "French",
            "Spanish",
            "Mandarin",
            "Cantonese",
            "Hindi",
            "Punjabi",
            "Arabic",
            "Portuguese",
            "Other",
        ],
    }


@router.get("/agencies")
async def agencies(session: AsyncSession = Depends(get_session)):
    rows = (
        (
            await session.execute(
                select(Agency)
                .join(User, Agency.owner_id == User.id)
                .where(User.is_verified, User.is_active)
            )
        )
        .scalars()
        .all()
    )
    return [{"id": a.id, "name": a.name, "city": a.city} for a in rows]


@router.post("/register", status_code=201)
async def register(data: Register, request: Request, session: AsyncSession = Depends(get_session)):
    if data.role == "provider":
        await verified_agency(data.agency_id, session)
    user = User(
        email=str(data.email),
        password_hash=await run_in_threadpool(hash_password, data.password.get_secret_value()),
        role=data.role,
    )
    try:
        session.add(user)
        await session.flush()
        agency_id = data.agency_id if data.role == "provider" else None
        if data.role == "agency":
            agency = Agency(owner_id=user.id, name=data.agency_name.strip(), city=data.city)
            session.add(agency)
            await session.flush()
            agency_id = agency.id
        session.add(
            CareProfile(
                user_id=user.id,
                name=data.name.strip(),
                agency_id=agency_id,
                experience=data.experience if data.role == "provider" else 0,
                gender=data.gender,
                services=data.services if data.role == "provider" else [],
                languages=data.languages,
                approved=False,
            )
        )
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(409, "An account with this email already exists") from None
    try:
        await send_account_link(user, settings_for(request), "verify")
        queued = True
    except HTTPException:
        queued = False
    return {"id": user.id, "role": user.role, "email": user.email, "verification_queued": queued}


@router.get("/me")
async def me(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    profile = await session.get(CareProfile, user.id)
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "is_verified": user.is_verified,
        "profile": profile,
    }


@router.get("/team")
async def team(user: User = Depends(network_user), session: AsyncSession = Depends(get_session)):
    agency = await agency_for(user, session)
    rows = (
        await session.execute(
            select(CareProfile, User)
            .join(User, User.id == CareProfile.user_id)
            .where(CareProfile.agency_id == agency.id, User.role == "provider")
        )
    ).all()
    return [{**p.model_dump(), "email": u.email, "is_verified": u.is_verified} for p, u in rows]


@router.patch("/team/{provider_id}")
async def approve(
    provider_id: UUID,
    data: Approval,
    user: User = Depends(network_user),
    session: AsyncSession = Depends(get_session),
):
    agency = await agency_for(user, session)
    profile = await session.get(CareProfile, provider_id)
    provider = await session.get(User, provider_id)
    if not profile or profile.agency_id != agency.id or not provider or provider.role != "provider":
        raise HTTPException(404, "Provider not found")
    if data.approved and not provider.is_verified:
        raise HTTPException(409, "Provider must verify their email first")
    profile.approved = data.approved
    await session.commit()
    return profile


@router.post("/visits", status_code=201)
async def create_visits(
    data: VisitCreate,
    user: User = Depends(network_user),
    session: AsyncSession = Depends(get_session),
):
    if user.role != "requester":
        raise HTTPException(403, "A requester account is required")
    agency = await verified_agency(data.agency_id, session)
    if agency.city != data.city:
        raise HTTPException(422, "Choose an agency serving the selected city")
    try:
        dates = occurrences(data)
    except ValueError as e:
        raise HTTPException(422, str(e)) from None
    series = uuid4()
    rows = []
    for date in dates:
        values = data.model_dump(exclude={"occurrences", "consent_confirmed", "starts_at"})
        visit = CareVisit(
            **values,
            series_id=series,
            requester_id=user.id,
            starts_at=date,
            latitude=CITIES[data.city][0],
            longitude=CITIES[data.city][1],
            timezone=CITIES[data.city][2],
        )
        session.add(visit)
        rows.append(visit)
    await session.flush()
    for visit in rows:
        session.add(CareEvent(visit_id=visit.id, actor_id=user.id, action="requested"))
    await session.commit()
    return [visit_view(v, user) for v in rows]


async def scoped_visits(user, session):
    stmt = select(CareVisit)
    profile = await session.get(CareProfile, user.id)
    if user.role == "agency":
        agency = await agency_for(user, session)
        stmt = stmt.where(CareVisit.agency_id == agency.id)
    elif user.role == "requester":
        stmt = stmt.where(CareVisit.requester_id == user.id)
    else:
        stmt = stmt.where(CareVisit.provider_id == user.id)
    rows = (await session.execute(stmt.order_by(CareVisit.starts_at))).scalars().all()
    return rows, profile


@router.get("/visits")
async def visits(user: User = Depends(network_user), session: AsyncSession = Depends(get_session)):
    rows, profile = await scoped_visits(user, session)
    return [visit_view(v, user, profile) for v in rows]


@router.get("/jobs")
async def jobs(user: User = Depends(network_user), session: AsyncSession = Depends(get_session)):
    if user.role != "provider":
        raise HTTPException(403, "A provider account is required")
    assigned, profile = await scoped_visits(user, session)
    if not profile or not profile.approved:
        return []
    rows = (
        (
            await session.execute(
                select(CareVisit)
                .where(
                    CareVisit.agency_id == profile.agency_id,
                    CareVisit.status == "open",
                    CareVisit.starts_at > datetime.now(timezone.utc),
                )
                .order_by(CareVisit.starts_at)
            )
        )
        .scalars()
        .all()
    )
    return [
        visit_view(v, user, profile)
        for v in rows
        if eligible(profile, v)
        and not any(overlaps(v, a) for a in assigned if a.status in ("accepted", "in_progress"))
    ]


@router.post("/jobs/{visit_id}/accept")
async def accept(
    visit_id: UUID, user: User = Depends(network_user), session: AsyncSession = Depends(get_session)
):
    if user.role != "provider":
        raise HTTPException(403, "A provider account is required")
    # Lock provider first to serialize acceptance of two different overlapping visits.
    profile = (
        (
            await session.execute(
                select(CareProfile).where(CareProfile.user_id == user.id).with_for_update()
            )
        )
        .scalars()
        .first()
    )
    visit = (
        (await session.execute(select(CareVisit).where(CareVisit.id == visit_id).with_for_update()))
        .scalars()
        .first()
    )
    if not visit or not eligible(profile, visit):
        raise HTTPException(404, "Eligible visit not found")
    if visit.status != "open" or visit.starts_at <= datetime.now(timezone.utc):
        raise HTTPException(409, "This visit is no longer available")
    assigned = (
        (
            await session.execute(
                select(CareVisit).where(
                    CareVisit.provider_id == user.id,
                    CareVisit.status.in_(["accepted", "in_progress"]),
                )
            )
        )
        .scalars()
        .all()
    )
    if any(overlaps(visit, a) for a in assigned):
        raise HTTPException(409, "This visit conflicts with your schedule or travel buffer")
    visit.provider_id = user.id
    visit.status = "accepted"
    session.add(CareEvent(visit_id=visit.id, actor_id=user.id, action="accepted"))
    await session.commit()
    return visit_view(visit, user, profile)


@router.post("/visits/{visit_id}/transition")
async def transition(
    visit_id: UUID,
    data: Transition,
    user: User = Depends(network_user),
    session: AsyncSession = Depends(get_session),
):
    visit = (
        (await session.execute(select(CareVisit).where(CareVisit.id == visit_id).with_for_update()))
        .scalars()
        .first()
    )
    if not visit:
        raise HTTPException(404, "Visit not found")
    agency = await agency_for(user, session) if user.role == "agency" else None
    owns = agency and agency.id == visit.agency_id
    requester = user.role == "requester" and visit.requester_id == user.id
    provider = user.role == "provider" and visit.provider_id == user.id
    if not (owns or requester or provider):
        raise HTTPException(404, "Visit not found")
    allowed = {
        "publish": (owns and visit.status == "requested", "open"),
        "cancel": (
            (owns or requester) and visit.status in ("requested", "open", "accepted"),
            "cancelled",
        ),
        "start": (provider and visit.status == "accepted", "in_progress"),
        "complete": (provider and visit.status == "in_progress", "completed"),
    }
    valid, status = allowed[data.action]
    if not valid:
        raise HTTPException(409, "This action is not available for this visit")
    if data.action == "publish" and visit.starts_at <= datetime.now(timezone.utc):
        raise HTTPException(409, "Past visits cannot be published")
    if data.action == "start" and visit.starts_at > datetime.now(timezone.utc):
        raise HTTPException(409, "The visit has not started yet")
    visit.status = status
    session.add(CareEvent(visit_id=visit.id, actor_id=user.id, action=status))
    await session.commit()
    return visit_view(visit, user)


@router.get("/devices")
async def devices(user: User = Depends(network_user), session: AsyncSession = Depends(get_session)):
    agency = await agency_for(user, session)
    return (
        (
            await session.execute(
                select(CareDevice)
                .where(CareDevice.agency_id == agency.id)
                .order_by(CareDevice.name)
            )
        )
        .scalars()
        .all()
    )


@router.post("/devices", status_code=201)
async def create_device(
    data: DeviceCreate,
    user: User = Depends(network_user),
    session: AsyncSession = Depends(get_session),
):
    agency = await agency_for(user, session)
    device = CareDevice(**data.model_dump(), agency_id=agency.id)
    session.add(device)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(409, "Asset code already exists in your agency") from None
    return device


@router.patch("/devices/{device_id}")
async def device_state(
    device_id: UUID,
    data: DeviceState,
    user: User = Depends(network_user),
    session: AsyncSession = Depends(get_session),
):
    agency = await agency_for(user, session)
    device = await session.get(CareDevice, device_id)
    if not device or device.agency_id != agency.id:
        raise HTTPException(404, "Device not found")
    device.status = data.status
    await session.commit()
    return device
