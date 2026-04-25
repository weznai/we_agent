from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.model import Model
from ..models.provider import Provider
from ..schemas.model import ModelCreate, ModelUpdate, ModelResponse
from ..utils.auth import get_current_user, get_current_admin
from ..models.user import User

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=List[ModelResponse])
async def list_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    models = db.query(Model).all()
    return [ModelResponse.model_validate(m) for m in models]


@router.post("", response_model=ModelResponse)
async def create_model(
    data: ModelCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if data.provider_id:
        provider = db.query(Provider).filter(Provider.id == data.provider_id).first()
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
    model = Model(**data.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)
    return ModelResponse.model_validate(model)


@router.put("/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: int,
    data: ModelUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(model, key, value)
    db.commit()
    db.refresh(model)
    return ModelResponse.model_validate(model)


@router.delete("/{model_id}")
async def delete_model(
    model_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    db.delete(model)
    db.commit()
    return {"message": "Model deleted"}
