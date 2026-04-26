import uuid
import time
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func

from ..entities import ChatHistory
from ..entities.factory import ChatHistoryFactory
from ..schemas.chat import ChatResponse, ChatSession
from ..utils.logger import get_logger

logger = get_logger(__name__)


def save_message(
    db: Session,
    user_id: int,
    session_id: str,
    role: str,
    content: str,
    agent_type: str = "chat",
    reasoning_content: str = None,
) -> ChatHistory:
    msg = ChatHistoryFactory.create(
        user_id=user_id,
        session_id=session_id,
        role=role,
        content=content,
        agent_type=agent_type,
        reasoning_content=reasoning_content,
    )
    db.add(msg)
    db.commit()
    return msg


def get_history(
    db: Session, user_id: int, session_id: str
) -> List[ChatResponse]:
    logger.info(f"[Chat] Get history: user_id={user_id}, session={session_id}")
    messages = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id, ChatHistory.user_id == user_id)
        .order_by(ChatHistory.created_at)
        .all()
    )
    logger.info(f"[Chat] History returned: session={session_id}, count={len(messages)}")
    return [
        ChatResponse(
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            agent_type=m.agent_type,
        )
        for m in messages
    ]


def get_sessions(db: Session, user_id: int) -> List[ChatSession]:
    logger.info(f"[Chat] Get sessions: user_id={user_id}")

    subq = (
        db.query(
            ChatHistory.session_id,
            ChatHistory.agent_type,
            sql_func.max(ChatHistory.created_at).label("max_time"),
        )
        .filter(ChatHistory.user_id == user_id, ChatHistory.role == "user")
        .group_by(ChatHistory.session_id, ChatHistory.agent_type)
        .subquery()
    )

    results = (
        db.query(
            ChatHistory.session_id,
            ChatHistory.content,
            ChatHistory.agent_type,
            ChatHistory.created_at,
        )
        .join(
            subq,
            (ChatHistory.session_id == subq.c.session_id)
            & (ChatHistory.agent_type == subq.c.agent_type)
            & (ChatHistory.created_at == subq.c.max_time),
        )
        .order_by(ChatHistory.created_at.desc())
        .all()
    )

    logger.info(f"[Chat] Sessions returned: user_id={user_id}, count={len(results)}")
    return [
        ChatSession(
            session_id=r.session_id,
            last_message=r.content[:50] if r.content else "",
            agent_type=r.agent_type,
            created_at=str(r.created_at),
        )
        for r in results
    ]


def create_session() -> str:
    session_id = str(uuid.uuid4())
    logger.info(f"[Chat] New session created: session={session_id}")
    return session_id


def delete_session(db: Session, user_id: int, session_id: str):
    logger.info(f"[Chat] Delete session: user_id={user_id}, session={session_id}")
    db.query(ChatHistory).filter(
        ChatHistory.session_id == session_id, ChatHistory.user_id == user_id
    ).delete()
    db.commit()
    logger.info(f"[Chat] Session deleted: session={session_id}")
    return {"message": "Session deleted"}
