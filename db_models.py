from __future__ import annotations

import os
import uuid
import datetime as dt
from typing import Optional

from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    ForeignKey,
    TIMESTAMP,
    Index,
    create_engine,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)


# ---------- base / engine / session ----------
class Base(DeclarativeBase):
    pass


def uid() -> str:
    return str(uuid.uuid4())


def now_utc() -> dt.datetime:
    # SQL default handles tz; python default only used for client-side
    return dt.datetime.now(dt.timezone.utc)


DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///socialvim.db")
ENGINE = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=ENGINE, expire_on_commit=False, future=True)


# ---------- tables ----------
class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    handle: Mapped[str] = mapped_column(String, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String)
    bio: Mapped[str] = mapped_column(Text, default="")
    ascii_pic: Mapped[str] = mapped_column(Text, default="")
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")


class Post(Base):
    __tablename__ = "posts"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    parent_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("posts.id"), nullable=True, index=True
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), index=True
    )
    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    reposts_count: Mapped[int] = mapped_column(Integer, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, default=0)

    author = relationship("User", back_populates="posts")


Index("idx_posts_author_time", Post.author_id, Post.created_at.desc())


class Follow(Base):
    __tablename__ = "follows"
    follower_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    followed_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )


Index("idx_follows_followed", Follow.followed_id)


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    created_at: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )


class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)


Index("idx_cp_user", ConversationParticipant.user_id)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id"), index=True
    )
    sender_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)


Index("idx_messages_conv_time", Message.conversation_id, Message.created_at.asc())


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)  # receiver
    type: Mapped[str] = mapped_column(
        String
    )  # 'mention','like','repost','follow','reply'
    actor_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), index=True
    )  # who did it
    content: Mapped[str] = mapped_column(Text, default="")
    related_post_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("posts.id"), nullable=True
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), index=True
    )
    read: Mapped[bool] = mapped_column(Boolean, default=False)


Index(
    "idx_notifications_user_time", Notification.user_id, Notification.created_at.desc()
)


# ---------- helpers ----------
def create_db() -> None:
    Base.metadata.create_all(ENGINE)


def get_session():
    return SessionLocal()
