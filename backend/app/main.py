import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
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
from .services.config_loader import load_yaml_config, sync_config_to_db

setup_logging(level="DEBUG")
logger = get_logger(__name__)

load_dotenv()

settings = get_settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMADB_PATH, exist_ok=True)

Base.metadata.create_all(bind=engine)

from sqlalchemy import inspect as sa_inspect
_tbl_inspect = sa_inspect(engine)
if 'knowledge_settings' in _tbl_inspect.get_table_names():
    _col_names = [c['name'] for c in _tbl_inspect.get_columns('knowledge_settings')]
    if 'group_id' not in _col_names:
        _conn = engine.raw_connection()
        try:
            _cur = _conn.cursor()
            _cur.execute("CREATE TABLE IF NOT EXISTS knowledge_settings_bak AS SELECT * FROM knowledge_settings")
            _cur.execute("DROP TABLE knowledge_settings")
            _cur.execute("""CREATE TABLE knowledge_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                group_id INTEGER,
                embedding_model_id INTEGER,
                enable_rerank BOOLEAN DEFAULT 0,
                rerank_model_id INTEGER,
                chunk_method VARCHAR(50) DEFAULT 'auto',
                chunk_size INTEGER DEFAULT 500,
                chunk_overlap INTEGER DEFAULT 50,
                retrieval_method VARCHAR(50) DEFAULT 'pure',
                retrieval_top_k INTEGER DEFAULT 5,
                score_threshold VARCHAR(10) DEFAULT '0.5',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(group_id) REFERENCES knowledge_groups(id),
                UNIQUE(user_id, group_id)
            )""")
            _cur.execute("INSERT OR IGNORE INTO knowledge_settings (id, user_id, group_id, embedding_model_id, enable_rerank, rerank_model_id, chunk_method, chunk_size, chunk_overlap, retrieval_method, retrieval_top_k, score_threshold, created_at, updated_at) SELECT id, user_id, NULL, embedding_model_id, 0, NULL, chunk_method, chunk_size, chunk_overlap, retrieval_method, retrieval_top_k, score_threshold, created_at, updated_at FROM knowledge_settings_bak")
            _cur.execute("DROP TABLE knowledge_settings_bak")
            _conn.commit()
            logger.info("Migrated knowledge_settings: added group_id, enable_rerank, rerank_model_id")
        except Exception as e:
            logger.warning(f"Migration skipped (knowledge_settings): {e}")
        finally:
            _conn.close()
    elif 'enable_rerank' not in _col_names:
        _conn = engine.raw_connection()
        try:
            _cur = _conn.cursor()
            _cur.execute("ALTER TABLE knowledge_settings ADD COLUMN enable_rerank BOOLEAN DEFAULT 0")
            _cur.execute("ALTER TABLE knowledge_settings ADD COLUMN rerank_model_id INTEGER")
            _conn.commit()
            logger.info("Migrated knowledge_settings: added enable_rerank, rerank_model_id")
        except Exception as e:
            logger.warning(f"Migration skipped (rerank columns): {e}")
        finally:
            _conn.close()

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

        llm_cfg = load_yaml_config()
        if llm_cfg:
            sync_config_to_db(db, llm_cfg)
        else:
            logger.info("No llm_config.yaml found, skipping LLM config sync")
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
