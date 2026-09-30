from fastapi import APIRouter, HTTPException, status

from app.api import site_data
from app.schemas.sites import SiteCreate, SiteUpdate


router = APIRouter()


@router.get("")
async def get_all_sites(
    active: bool | None = None,
) -> list[dict]:
    if active is None:
        return site_data.sites

    return [
        site
        for site in site_data.sites
        if site["active"] == active
    ]


@router.get("/{site_id}")
async def get_site(site_id: int) -> dict:
    for site in site_data.sites:
        if site["id"] == site_id:
            return site

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Site not found",
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_site(site_data_input: SiteCreate) -> dict:
    new_site = site_data_input.model_dump()

    new_site["id"] = site_data.next_id
    site_data.next_id += 1

    site_data.sites.append(new_site)

    return new_site


@router.patch("/{site_id}")
async def update_site(
    site_id: int,
    site_update_data: SiteUpdate,
) -> dict:
    for site in site_data.sites:
        if site["id"] == site_id:
            site["active"] = site_update_data.active
            return site

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Site not found",
    )


@router.delete(
    "/{site_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_site(site_id: int):
    for site in site_data.sites:
        if site["id"] == site_id:
            site_data.sites.remove(site)
            return

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Site not found",
    )