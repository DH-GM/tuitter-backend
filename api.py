from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from typing_extensions import Annotated

from fastapi import FastAPI, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .db_models import (
    get_session,
    User as DBUser,
    Post as DBPost,
    Message as DBMessage,
    Conversation as DBConversation,
    Notification as DBNotification,
    ConversationParticipant,
)
from .db_repo import (
    create_user,
    get_user_by_handle,
    update_user_bio,
    create_post as repo_create_post,
    get_post as repo_get_post,
    delete_post as repo_delete_post,
    list_feed,
    get_or_create_dm,
    send_dm,
    list_dm,
    mark_notification_read as repo_mark_notification_read,
)


# -----------------------------------------------------------------------------
# Pydantic response/request models (API surface)
# -----------------------------------------------------------------------------
class UserOut(BaseModel):
    id: str
    handle: str
    display_name: str
    bio: str

    @staticmethod
    def from_db(u: DBUser) -> "UserOut":
        return UserOut(
            id=u.id, handle=u.handle, display_name=u.display_name, bio=u.bio or ""
        )


class PostOut(BaseModel):
    id: str
    author_id: str
    content: str
    created_at: datetime
    likes_count: int
    reposts_count: int
    comments_count: int

    @staticmethod
    def from_db(p: DBPost) -> "PostOut":
        return PostOut(
            id=p.id,
            author_id=p.author_id,
            content=p.content,
            created_at=p.created_at,
            likes_count=p.likes_count or 0,
            reposts_count=p.reposts_count or 0,
            comments_count=p.comments_count or 0,
        )


class PostCreate(BaseModel):
    content: str
    author_handle: str = "yourname"
    parent_id: Optional[str] = None


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    content: str
    created_at: datetime
    is_read: bool

    @staticmethod
    def from_db(m: DBMessage) -> "MessageOut":
        return MessageOut(
            id=m.id,
            conversation_id=m.conversation_id,
            sender_id=m.sender_id,
            content=m.content,
            created_at=m.created_at,
            is_read=bool(m.is_read),
        )


class MessageCreate(BaseModel):
    sender_handle: str = "yourname"
    content: str


class ConversationOut(BaseModel):
    id: str
    participant_handles: list[str]
    last_message_preview: str | None = None
    last_message_at: datetime | None = None


class DMOpenRequest(BaseModel):
    user_a_handle: str
    user_b_handle: str


class NotificationOut(BaseModel):
    id: str
    type: str
    actor_id: str
    content: str
    related_post_id: Optional[str]
    created_at: datetime
    read: bool


# Very light in-memory settings shim
class Settings(BaseModel):
    username: str
    display_name: str
    bio: str
    email_notifications: bool = True
    show_online_status: bool = True
    private_account: bool = False
    ascii_pic: str = ""
    github_connected: bool = False
    gitlab_connected: bool = False
    google_connected: bool = False
    discord_connected: bool = False


_SETTINGS_STORE: dict[str, Settings] = {}  # key = user_id


def _get_or_create_user(handle: str) -> DBUser:
    u = get_user_by_handle(handle)
    if u is None:
        u = create_user(handle, handle.capitalize())
    return u


def _settings_for(user: DBUser) -> Settings:
    if user.id not in _SETTINGS_STORE:
        _SETTINGS_STORE[user.id] = Settings(
            username=user.handle,
            display_name=user.display_name,
            bio=user.bio or "",
        )
    return _SETTINGS_STORE[user.id]


# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------
app = FastAPI(title="tuitter-backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Common annotations
Limit200 = Annotated[int, Query(ge=1, le=200)]
Limit500 = Annotated[int, Query(ge=1, le=500)]


# -----------------------------------------------------------------------------
# /health  (ANY)
# -----------------------------------------------------------------------------
@app.api_route("/health", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
def health():
    return {
        "status": "ok",
        "service": "tuitter-backend",
        "time": datetime.now(timezone.utc).isoformat(),
    }


# -----------------------------------------------------------------------------
# /me (GET)
# -----------------------------------------------------------------------------
@app.get("/me", response_model=UserOut)
def get_me(handle: str = "yourname"):
    u = _get_or_create_user(handle)
    return UserOut.from_db(u)


# -----------------------------------------------------------------------------
# /timeline (GET)
# -----------------------------------------------------------------------------
@app.get("/timeline", response_model=list[PostOut])
def get_timeline(limit: Limit200 = 50):
    posts = list_feed(limit=limit)
    return [PostOut.from_db(p) for p in posts]


# -----------------------------------------------------------------------------
# /discover (GET)
# -----------------------------------------------------------------------------
@app.get("/discover", response_model=list[PostOut])
def get_discover(limit: Limit200 = 50):
    posts = list_feed(limit=limit)
    return [PostOut.from_db(p) for p in posts]


# -----------------------------------------------------------------------------
# /posts (GET, POST)
# -----------------------------------------------------------------------------
@app.get("/posts", response_model=list[PostOut])
def list_posts(limit: Limit200 = 50):
    posts = list_feed(limit=limit)
    return [PostOut.from_db(p) for p in posts]


@app.post("/posts", response_model=PostOut, status_code=201)
def create_post(payload: PostCreate):
    author = _get_or_create_user(payload.author_handle)
    p = repo_create_post(
        author_id=author.id, content=payload.content, parent_id=payload.parent_id
    )
    return PostOut.from_db(p)


# -----------------------------------------------------------------------------
# /posts/{post_id} (GET, DELETE)
# -----------------------------------------------------------------------------
@app.get("/posts/{post_id}", response_model=PostOut)
def get_post(post_id: str):
    p = repo_get_post(post_id)
    if not p:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Post not found")
    return PostOut.from_db(p)


@app.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: str):
    ok = repo_delete_post(post_id)
    if not ok:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Post not found")
    return None


# -----------------------------------------------------------------------------
# /posts/{post_id}/like  (POST)
# -----------------------------------------------------------------------------
@app.post("/posts/{post_id}/like", response_model=PostOut)
def like_post(post_id: str):
    with get_session() as db:
        p = db.get(DBPost, post_id)
        if not p:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Post not found")
        p.likes_count = (p.likes_count or 0) + 1
        db.commit()
        db.refresh(p)
        return PostOut.from_db(p)


# -----------------------------------------------------------------------------
# /posts/{post_id}/repost (POST)
# -----------------------------------------------------------------------------
@app.post("/posts/{post_id}/repost", response_model=PostOut)
def repost_post(post_id: str):
    with get_session() as db:
        p = db.get(DBPost, post_id)
        if not p:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Post not found")
        p.reposts_count = (p.reposts_count or 0) + 1
        db.commit()
        db.refresh(p)
        return PostOut.from_db(p)


# -----------------------------------------------------------------------------
# /conversations (GET)
# -----------------------------------------------------------------------------
@app.get("/conversations", response_model=list[ConversationOut])
def list_conversations():
    with get_session() as db:
        convs: list[DBConversation] = db.query(DBConversation).all()
        results: list[ConversationOut] = []
        for c in convs:
            parts = (
                db.query(ConversationParticipant)
                .filter(ConversationParticipant.conversation_id == c.id)
                .all()
            )
            user_ids = [p.user_id for p in parts]
            handles = [
                db.get(DBUser, uid).handle for uid in user_ids if db.get(DBUser, uid)
            ]
            last = (
                db.query(DBMessage)
                .filter(DBMessage.conversation_id == c.id)
                .order_by(DBMessage.created_at.desc())
                .first()
            )
            results.append(
                ConversationOut(
                    id=c.id,
                    participant_handles=handles,
                    last_message_preview=last.content if last else None,
                    last_message_at=last.created_at if last else None,
                )
            )
        return results


# -----------------------------------------------------------------------------
# /conversations/{conv_id}/messages (GET, POST)
# -----------------------------------------------------------------------------
@app.get("/conversations/{conv_id}/messages", response_model=list[MessageOut])
def get_conversation_messages(conv_id: str, limit: Limit500 = 100):
    msgs = list_dm(conv_id, limit=limit)
    return [MessageOut.from_db(m) for m in msgs]


@app.post(
    "/conversations/{conv_id}/messages", response_model=MessageOut, status_code=201
)
def send_conversation_message(conv_id: str, payload: MessageCreate):
    sender = _get_or_create_user(payload.sender_handle)
    m = send_dm(conversation_id=conv_id, sender_id=sender.id, text=payload.content)
    return MessageOut.from_db(m)


# -----------------------------------------------------------------------------
# /dm (POST)
# -----------------------------------------------------------------------------
@app.post("/dm", response_model=ConversationOut, status_code=201)
def open_dm(req: DMOpenRequest):
    a = _get_or_create_user(req.user_a_handle)
    b = _get_or_create_user(req.user_b_handle)
    conv = get_or_create_dm(a.id, b.id)
    return ConversationOut(id=conv.id, participant_handles=[a.handle, b.handle])


# -----------------------------------------------------------------------------
# /notifications (GET)  &  /notifications/{notif_id}/read (POST)
# -----------------------------------------------------------------------------
@app.get("/notifications", response_model=list[NotificationOut])
def get_notifications(handle: str = "yourname"):
    user = _get_or_create_user(handle)
    with get_session() as db:
        rows: list[DBNotification] = (
            db.query(DBNotification)
            .filter(DBNotification.user_id == user.id)
            .order_by(DBNotification.created_at.desc())
            .all()
        )
        return [
            NotificationOut(
                id=n.id,
                type=n.type,
                actor_id=n.actor_id,
                content=n.content or "",
                related_post_id=n.related_post_id,
                created_at=n.created_at,
                read=bool(n.read),
            )
            for n in rows
        ]


@app.post("/notifications/{notif_id}/read")
def mark_notification_read(notif_id: str):
    ok = repo_mark_notification_read(notif_id)
    if not ok:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Notification not found")
    return {"ok": True}


# -----------------------------------------------------------------------------
# /settings (GET, PUT)
# -----------------------------------------------------------------------------
@app.get("/settings", response_model=Settings)
def get_settings(handle: str = "yourname"):
    u = _get_or_create_user(handle)
    return _settings_for(u)


@app.put("/settings", response_model=Settings)
def put_settings(payload: Settings, handle: str = "yourname"):
    u = _get_or_create_user(handle)
    update_user_bio(u.id, payload.bio)
    with get_session() as db:
        dbu = db.get(DBUser, u.id)
        if dbu:
            dbu.display_name = payload.display_name
            db.commit()
    _SETTINGS_STORE[u.id] = payload
    return payload
