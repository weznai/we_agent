import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.user import UserRegister, UserLogin, Token
from ..services.auth_service import send_verification_code, register, login
from ..utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/send-code")
async def send_code(email: str):
    code = send_verification_code(email)
    return {"message": "Verification code sent", "code": code}


@router.post("/register", response_model=Token)
async def register_endpoint(user_data: UserRegister, db: Session = Depends(get_db)):
    return register(
        db=db,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        verification_code=user_data.verification_code,
    )


@router.post("/login", response_model=Token)
async def login_endpoint(user_data: UserLogin, db: Session = Depends(get_db)):
    return login(db=db, login=user_data.login, password=user_data.password)
