from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.model_mapping import ModelMapping
from ..models.model import Model
from ..models.provider import Provider
from ..schemas.model_mapping import ModelMappingCreate, ModelMappingUpdate, ModelMappingResponse
from ..utils.auth import get_current_user, get_current_admin
from ..models.user import User

router = APIRouter(prefix="/api/model-mappings", tags=["model-mappings"])


@router.get("", response_model=List[ModelMappingResponse])
async def list_mappings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    mappings = db.query(ModelMapping).all()
    result = []
    for m in mappings:
        model = db.query(Model).filter(Model.id == m.model_id).first()
        provider = db.query(Provider).filter(Provider.id == model.provider_id).first() if model else None
        resp = ModelMappingResponse(
            id=m.id,
            agent_type=m.agent_type,
            model_id=m.model_id,
            priority=m.priority,
            created_at=m.created_at,
            model_name=model.name if model else "",
            provider_name=provider.display_name if provider else "",
        )
        result.append(resp)
    return result


@router.post("", response_model=ModelMappingResponse)
async def create_mapping(
    data: ModelMappingCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    model = db.query(Model).filter(Model.id == data.model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    mapping = ModelMapping(**data.model_dump())
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return ModelMappingResponse(
        id=mapping.id,
        agent_type=mapping.agent_type,
        model_id=mapping.model_id,
        priority=mapping.priority,
        created_at=mapping.created_at,
        model_name=model.name,
        provider_name="",
    )


@router.put("/{mapping_id}", response_model=ModelMappingResponse)
async def update_mapping(
    mapping_id: int,
    data: ModelMappingUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    mapping = db.query(ModelMapping).filter(ModelMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(mapping, key, value)
    db.commit()
    db.refresh(mapping)
    model = db.query(Model).filter(Model.id == mapping.model_id).first()
    return ModelMappingResponse(
        id=mapping.id,
        agent_type=mapping.agent_type,
        model_id=mapping.model_id,
        priority=mapping.priority,
        created_at=mapping.created_at,
        model_name=model.name if model else "",
        provider_name="",
    )


@router.delete("/{mapping_id}")
async def delete_mapping(
    mapping_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    mapping = db.query(ModelMapping).filter(ModelMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    db.delete(mapping)
    db.commit()
    return {"message": "Mapping deleted"}

