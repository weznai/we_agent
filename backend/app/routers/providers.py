from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.provider import Provider
from ..schemas.provider import ProviderCreate, ProviderUpdate, ProviderResponse
from ..utils.auth import get_current_user, get_current_admin
from ..models.user import User

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("", response_model=List[ProviderResponse])
async def list_providers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    providers = db.query(Provider).all()
    return [ProviderResponse.model_validate(p) for p in providers]


@router.post("", response_model=ProviderResponse)
async def create_provider(
    data: ProviderCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    existing = db.query(Provider).filter(Provider.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Provider name already exists")
    provider = Provider(**data.model_dump())
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return ProviderResponse.model_validate(provider)


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: int,
    data: ProviderUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(provider, key, value)
    db.commit()
    db.refresh(provider)
    return ProviderResponse.model_validate(provider)


@router.delete("/{provider_id}")
async def delete_provider(
    provider_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    db.delete(provider)
    db.commit()
    return {"message": "Provider deleted"}
