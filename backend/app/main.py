import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import engine, Base, SessionLocal
from .routers import auth, users, providers, models, model_mappings, knowledge, chat, order_agent
from .entities import User, UserRole
from .entities.factory import UserFactory
from .utils.auth import get_password_hash
from .utils.logger import get_logger, setup_logging
from .config import get_settings

setup_logging(level="DEBUG")
logger = get_logger(__name__)

settings = get_settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

Base.metadata.create_all(bind=engine)

logger.info("Database initialized, tables created")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up...")
    db = SessionLocal()
    try:
        super_user = db.query(User).filter(User.role == UserRole.SUPER).first()
        if not super_user:
            super_user = UserFactory.create_super(
                username="admin",
                email="admin@agent.com",
                password="admin123",
                nickname="Super Admin",
                email_verified=True,
            )
            db.add(super_user)
            db.commit()
            logger.info("Super admin created: admin / admin123")
        else:
            logger.info("Super admin already exists, skip creation")
    finally:
        db.close()
    logger.info("Application startup complete")
    yield
    logger.info("Application shutting down")


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
app.include_router(order_agent.router)

if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
