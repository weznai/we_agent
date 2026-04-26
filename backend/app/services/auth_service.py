import time
import random
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..entities import User, UserRole
from ..entities.factory import UserFactory
from ..schemas.user import UserResponse, Token
from ..utils.auth import verify_password, create_access_token
from ..utils.logger import get_logger

logger = get_logger(__name__)

_verification_codes: dict[str, str] = {}


def send_verification_code(email: str) -> str:
    code = str(random.randint(100000, 999999))
    _verification_codes[email] = code
    logger.info(f"[Auth] Verification code sent: email={email}, code={code}")
    return code


def register(
    db: Session,
    username: str,
    email: str,
    password: str,
    verification_code: Optional[str] = None,
) -> Token:
    start_time = time.time()
    logger.info(f"[Auth] Register attempt: username={username}, email={email}")

    existing = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    if existing:
        logger.warning(
            f"[Auth] Register failed: username={username} - already exists"
        )
        raise HTTPException(status_code=400, detail="Username or email already registered")

    if verification_code:
        stored_code = _verification_codes.get(email)
        if not stored_code or stored_code != verification_code:
            logger.warning(f"[Auth] Register failed: invalid verification code for email={email}")
            raise HTTPException(status_code=400, detail="Invalid verification code")

    user = UserFactory.create(
        username=username,
        email=email,
        password=password,
        email_verified=bool(verification_code),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    elapsed = time.time() - start_time
    logger.info(
        f"[Auth] Register success: user_id={user.id}, username={user.username}, elapsed={elapsed:.2f}s"
    )

    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


def login(db: Session, login: str, password: str) -> Token:
    start_time = time.time()
    logger.info(f"[Auth] Login attempt: login={login}")

    user = db.query(User).filter(
        (User.username == login) | (User.email == login)
    ).first()

    if not user:
        logger.warning(f"[Auth] Login failed: user not found for login={login}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    logger.info(
        f"[Auth] User found: user_id={user.id}, username={user.username}, role={user.role}, is_active={user.is_active}"
    )

    if not user.is_active:
        logger.warning(f"[Auth] Login failed: account disabled for user={user.username}")
        raise HTTPException(status_code=403, detail="Account is disabled")

    pwd_ok = verify_password(password, user.hashed_password)
    logger.info(f"[Auth] Password verify: user={user.username}, result={pwd_ok}")

    if not pwd_ok:
        logger.warning(f"[Auth] Login failed: wrong password for user={user.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": str(user.id)})

    elapsed = time.time() - start_time
    logger.info(
        f"[Auth] Login success: user={user.username}, user_id={user.id}, elapsed={elapsed:.2f}s"
    )

    return Token(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )
