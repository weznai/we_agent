import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import engine, Base, SessionLocal
from .routers import auth, users, providers, models, model_mappings, knowledge, chat
from .models.user import User, UserRole
from .utils.auth import get_password_hash
from .config import get_settings

settings = get_settings()

if settings.DATABASE_URL.startswith("sqlite"):
    db_path = settings.DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
    db_dir = os.path.dirname(db_path) if db_path else "data"
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        super_user = db.query(User).filter(User.role == UserRole.SUPER).first()
        if not super_user:
            super_user = User(
                username="admin",
                email="admin@agent.com",
                hashed_password=get_password_hash("admin123"),
                nickname="Super Admin",
                role=UserRole.SUPER,
                is_active=True,
                email_verified=True,
            )
            db.add(super_user)
            db.commit()
            print("Super admin created: admin / admin123")
    finally:
        db.close()
    yield


app = FastAPI(title="Super Agent API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(providers.router)
app.include_router(models.router)
app.include_router(model_mappings.router)
app.include_router(knowledge.router)
app.include_router(chat.router)

if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
