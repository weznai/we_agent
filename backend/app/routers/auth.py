import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User, UserRole
from ..schemas.user import UserRegister, UserLogin, UserResponse, Token
from ..utils.auth import verify_password, get_password_hash, create_access_token
import random

logger = logging.getLogger("auth")
logging.basicConfig(level=logging.DEBUG)

router = APIRouter(prefix="/api/auth", tags=["auth"])

verification_codes = {}


@router.post("/send-code")
async def send_verification_code(email: str):
    code = str(random.randint(100000, 999999))
    verification_codes[email] = code
    logger.info(f"Verification code sent to {email}: {code}")
    return {"message": "Verification code sent", "code": code}


@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    logger.info(f"Register attempt: username={user_data.username}, email={user_data.email}")

    existing = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing:
        logger.warning(f"Register failed: username or email already exists")
        raise HTTPException(status_code=400, detail="Username or email already registered")

    if user_data.verification_code:
        stored_code = verification_codes.get(user_data.email)
        if not stored_code or stored_code != user_data.verification_code:
            raise HTTPException(status_code=400, detail="Invalid verification code")

    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        nickname=user_data.username,
        email_verified=bool(user_data.verification_code),
        role=UserRole.USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"User registered successfully: id={user.id}, username={user.username}")
    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    logger.info(f"Login attempt: login={user_data.login}")

    user = db.query(User).filter(
        (User.username == user_data.login) | (User.email == user_data.login)
    ).first()

    if not user:
        logger.warning(f"Login failed: user not found for login={user_data.login}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    logger.info(f"User found: id={user.id}, username={user.username}, role={user.role}, is_active={user.is_active}")

    if not user.is_active:
        logger.warning(f"Login failed: account disabled for user={user.username}")
        raise HTTPException(status_code=403, detail="Account is disabled")

    pwd_ok = verify_password(user_data.password, user.hashed_password)
    logger.info(f"Password verify result: {pwd_ok}, hash_prefix={user.hashed_password[:20]}...")

    if not pwd_ok:
        logger.warning(f"Login failed: wrong password for user={user.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": str(user.id)})
    logger.info(f"Login success: user={user.username}, token generated")
    return Token(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )
