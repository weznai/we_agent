from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProviderCreate(BaseModel):
    name: str
    display_name: Optional[str] = ""
    description: Optional[str] = ""
    api_base: Optional[str] = ""
    api_key: Optional[str] = ""
    logo: Optional[str] = ""


class ProviderUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    logo: Optional[str] = None
    is_active: Optional[bool] = None


class ProviderResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: str
    api_base: str
    logo: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
