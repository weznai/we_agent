from typing import Optional

from .user import User, UserRole
from .chat_history import ChatHistory
from .provider import Provider
from .model import Model
from .model_mapping import ModelMapping
from .knowledge import Knowledge
from .knowledge_group import KnowledgeGroup
from .knowledge_chunk import KnowledgeChunk
from .knowledge_setting import KnowledgeSetting
from ..utils.auth import get_password_hash


class UserFactory:
    @staticmethod
    def create(
        username: str,
        email: str,
        password: str,
        role: UserRole = UserRole.USER,
        **kwargs,
    ) -> User:
        return User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            nickname=kwargs.get("nickname", username),
            avatar=kwargs.get("avatar", ""),
            role=role,
            is_active=kwargs.get("is_active", True),
            email_verified=kwargs.get("email_verified", False),
        )

    @staticmethod
    def create_super(
        username: str,
        email: str,
        password: str,
        **kwargs,
    ) -> User:
        return UserFactory.create(
            username, email, password, role=UserRole.SUPER, **kwargs
        )


class ProviderFactory:
    @staticmethod
    def create(
        name: str,
        display_name: str = "",
        api_base: str = "",
        api_key: str = "",
        **kwargs,
    ) -> Provider:
        return Provider(
            name=name,
            display_name=display_name,
            description=kwargs.get("description", ""),
            api_base=api_base,
            api_key=api_key,
            logo=kwargs.get("logo", ""),
            is_active=kwargs.get("is_active", True),
        )


class ModelFactory:
    @staticmethod
    def create(
        name: str,
        provider_id: Optional[int] = None,
        **kwargs,
    ) -> Model:
        return Model(
            provider_id=provider_id,
            name=name,
            display_name=kwargs.get("display_name", ""),
            model_type=kwargs.get("model_type", "chat"),
            description=kwargs.get("description", ""),
            max_tokens=kwargs.get("max_tokens", 1048576),
            temperature=kwargs.get("temperature", "0.7"),
            embedding_dimension=kwargs.get("embedding_dimension", 0),
            model_path=kwargs.get("model_path", ""),
            is_active=kwargs.get("is_active", True),
        )


class ModelMappingFactory:
    @staticmethod
    def create(
        agent_type: str,
        model_id: int,
        priority: int = 0,
    ) -> ModelMapping:
        return ModelMapping(
            agent_type=agent_type,
            model_id=model_id,
            priority=priority,
        )


class KnowledgeGroupFactory:
    @staticmethod
    def create(
        user_id: int,
        name: str,
        **kwargs,
    ) -> KnowledgeGroup:
        return KnowledgeGroup(
            user_id=user_id,
            name=name,
            description=kwargs.get("description", ""),
            color=kwargs.get("color", "#6366f1"),
            icon=kwargs.get("icon", "Folder"),
            sort_order=kwargs.get("sort_order", 0),
        )


class KnowledgeFactory:
    @staticmethod
    def create(
        user_id: int,
        name: str,
        **kwargs,
    ) -> Knowledge:
        return Knowledge(
            user_id=user_id,
            group_id=kwargs.get("group_id"),
            name=name,
            description=kwargs.get("description", ""),
            file_path=kwargs.get("file_path", ""),
            file_type=kwargs.get("file_type", ""),
            file_size=kwargs.get("file_size", 0),
            content=kwargs.get("content", ""),
            chunk_count=kwargs.get("chunk_count", 0),
            status=kwargs.get("status", "active"),
            indexed=kwargs.get("indexed", False),
        )

    @staticmethod
    def create_chunk(
        knowledge_id: int,
        chunk_index: int,
        content: str,
        embedding: str,
        group_id: Optional[int] = None,
    ) -> KnowledgeChunk:
        return KnowledgeChunk(
            knowledge_id=knowledge_id,
            group_id=group_id,
            chunk_index=chunk_index,
            content=content,
            embedding=embedding,
        )


class KnowledgeSettingFactory:
    @staticmethod
    def create(
        user_id: int,
        **kwargs,
    ) -> KnowledgeSetting:
        return KnowledgeSetting(
            user_id=user_id,
            group_id=kwargs.get("group_id"),
            embedding_model_id=kwargs.get("embedding_model_id"),
            enable_rerank=kwargs.get("enable_rerank", False),
            rerank_model_id=kwargs.get("rerank_model_id"),
            chunk_method=kwargs.get("chunk_method", "auto"),
            chunk_size=kwargs.get("chunk_size", 500),
            chunk_overlap=kwargs.get("chunk_overlap", 50),
            retrieval_method=kwargs.get("retrieval_method", "pure"),
            retrieval_top_k=kwargs.get("retrieval_top_k", 5),
            score_threshold=kwargs.get("score_threshold", "0.5"),
        )


class ChatHistoryFactory:
    @staticmethod
    def create(
        user_id: int,
        session_id: str,
        role: str,
        content: str,
        agent_type: str = "chat",
        **kwargs,
    ) -> ChatHistory:
        return ChatHistory(
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content,
            reasoning_content=kwargs.get("reasoning_content"),
            agent_type=agent_type,
        )
