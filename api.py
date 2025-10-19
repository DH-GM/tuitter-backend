# ruff: noqa: E402
from __future__ import annotations

import sys, pathlib
PKG_ROOT = pathlib.Path(__file__).resolve().parent
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from datetime import datetime, timezone
from typing import Optional
from typing_extensions import Annotated
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db_models import (
    get_session,
    DATABASE_URL,
    User as DBUser,
    Post as DBPost,
    Message as DBMessage,
    Conversation as DBConversation,
    Notification as DBNotification,
    ConversationParticipant,
)
from db_repo import (
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

class UserOut(BaseModel):
    # matches frontend User dataclass
    username: str
    display_name: str
    bio: str
    followers: int = 0
    following: int = 0
    posts_count: int = 0
    ascii_pic: str = ""

    @staticmethod
    def from_db(u: DBUser, db) -> "UserOut":
        # compute posts_count and follower counts
        posts_count = db.query(DBPost).filter(DBPost.author_id == u.id).count()
        followers = db.execute(
            "SELECT COUNT(*) FROM follows WHERE followed_id = :uid",
            {"uid": u.id}
        ).scalar() or 0
        following = db.execute(
            "SELECT COUNT(*) FROM follows WHERE follower_id = :uid",
            {"uid": u.id}
        ).scalar() or 0
        return UserOut(
            username=u.handle,
            display_name=u.display_name,
            bio=u.bio or "",
            followers=int(followers),
            following=int(following),
            posts_count=int(posts_count),
            ascii_pic=(u.ascii_pic if getattr(u, 'ascii_pic', None) else ""),
        )

class PostOut(BaseModel):
    # matches frontend Post dataclass
    id: str
    author: str
    content: str
    timestamp: datetime
    likes: int = 0
    reposts: int = 0
    comments: int = 0
    liked_by_user: bool = False
    reposted_by_user: bool = False

    @staticmethod
    def from_db(p: DBPost, db) -> "PostOut":
        author = db.get(DBUser, p.author_id)
        author_handle = author.handle if author else "unknown"
        return PostOut(
            id=p.id,
            author=author_handle,
            content=p.content,
            timestamp=p.created_at,
            likes=int(p.likes_count or 0),
            reposts=int(p.reposts_count or 0),
            comments=int(p.comments_count or 0),
            liked_by_user=False,
            reposted_by_user=False,
        )

class PostCreate(BaseModel):
    content: str
    author_handle: str = "yourname"
    parent_id: Optional[str] = None

class MessageOut(BaseModel):
    # matches frontend Message dataclass
    id: str
    sender: str
    content: str
    timestamp: datetime
    is_read: bool = False

    @staticmethod
    def from_db(m: DBMessage, db) -> "MessageOut":
        sender = db.get(DBUser, m.sender_id)
        sender_handle = sender.handle if sender else "unknown"
        return MessageOut(
            id=m.id,
            sender=sender_handle,
            content=m.content,
            timestamp=m.created_at,
            is_read=bool(m.is_read),
        )

class MessageCreate(BaseModel):
    sender_handle: str = "yourname"
    content: str

class ConversationOut(BaseModel):
    # matches frontend Conversation dataclass
    id: str
    username: str
    last_message: str | None = None
    timestamp: datetime | None = None
    unread: bool = False

class DMOpenRequest(BaseModel):
    user_a_handle: str
    user_b_handle: str

class NotificationOut(BaseModel):
    # matches frontend Notification dataclass
    id: str
    type: str
    actor: str
    content: str
    timestamp: datetime
    read: bool
    related_post: Optional[str]

class CommentIn(BaseModel):
    text: str
    user: str = "yourname"

class CommentOut(BaseModel):
    user: str
    text: str

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

_SETTINGS_STORE: dict[str, Settings] = {}

def _get_or_create_user(handle: str) -> DBUser:
    """Get an existing user or create a new one with proper error handling."""
    try:
        # Check if the handle is valid (under 32 characters)
        if len(handle) > 30:
            # Truncate to avoid database errors
            handle = handle[:30]
        
        # First try to get the existing user
        u = get_user_by_handle(handle)
        
        # If user doesn't exist, create a new one
        if u is None:
            # Ensure display name is valid
            display_name = handle.capitalize()
            if len(display_name) > 90:
                display_name = display_name[:90]
                
            u = create_user(handle, display_name)
            
        return u
    except Exception as e:
        # Log the error but return a default user to avoid breaking the API
        print(f"Error in _get_or_create_user: {str(e)}")
        
        # Try to get a default user
        default_user = get_user_by_handle("defaultuser")
        if default_user:
            return default_user
            
        # If that fails, try to create a fallback user
        try:
            return create_user("defaultuser", "Default User")
        except Exception:
            # Last resort - raise the error since we can't proceed
            raise HTTPException(
                status_code=500, 
                detail="Failed to get or create user and couldn't fall back to default user"
            )

def _settings_for(user: DBUser) -> Settings:
    if user.id not in _SETTINGS_STORE:
        _SETTINGS_STORE[user.id] = Settings(
            username=user.handle, display_name=user.display_name, bio=user.bio or ""
        )
    return _SETTINGS_STORE[user.id]

app = FastAPI(title="tuitter-backend", version="0.1.2")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

Limit200 = Annotated[int, Query(ge=1, le=200)]
Limit500 = Annotated[int, Query(ge=1, le=500)]

@app.api_route("/health", methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"])
def health(
    debug: bool = False,
    db_test: bool = False,
    show_tables: bool = False,
    error_info: bool = False,
):
    """Health check endpoint with optional diagnostics."""
    response = {
        "status": "ok",
        "service": "tuitter-backend",
        "time": datetime.now(timezone.utc).isoformat(),
    }
    
    # Add database connection test if requested
    if db_test:
        try:
            with get_session() as db:
                # Simple query to test connection
                db.execute("SELECT 1").scalar()
                response["database"] = "connected"
        except Exception as e:
            response["status"] = "degraded"
            response["database"] = "disconnected"
            if error_info:
                response["db_error"] = str(e)
    
    # Add detailed debug info if requested
    if debug:
        response["environment"] = {
            "database_url": DATABASE_URL.replace(
                # Remove credentials from displayed URL
                DATABASE_URL[DATABASE_URL.find("://") + 3:DATABASE_URL.find("@")] if "@" in DATABASE_URL else "",
                "***:***"
            ) if "@" in DATABASE_URL else DATABASE_URL,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        }
    
    # Show database tables if requested
    if show_tables and debug:
        try:
            with get_session() as db:
                tables = db.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'").scalars().all()
                response["tables"] = list(tables)
        except Exception as e:
            response["tables_error"] = str(e) if error_info else "Error retrieving tables"
            
    return response

@app.get("/me", response_model=UserOut)
def get_me(handle: str = "yourname"):
    u = _get_or_create_user(handle)
    with get_session() as db:
        return UserOut.from_db(u, db)

@app.get("/timeline", response_model=list[PostOut])
def get_timeline(limit: Limit200 = 50):
    with get_session() as db:
        posts = list_feed(limit=limit)
        return [PostOut.from_db(p, db) for p in posts]

@app.get("/discover", response_model=list[PostOut])
def get_discover(limit: Limit200 = 50):
    with get_session() as db:
        posts = list_feed(limit=limit)
        return [PostOut.from_db(p, db) for p in posts]

@app.get("/posts", response_model=list[PostOut])
def list_posts(limit: Limit200 = 50):
    with get_session() as db:
        posts = list_feed(limit=limit)
        return [PostOut.from_db(p, db) for p in posts]

@app.post("/posts", response_model=PostOut, status_code=201)
def create_post_ep(payload: PostCreate):
    author = _get_or_create_user(payload.author_handle)
    p = repo_create_post(author_id=author.id, content=payload.content, parent_id=payload.parent_id)
    with get_session() as db:
        return PostOut.from_db(p, db)

@app.get("/posts/{post_id}", response_model=PostOut)
def get_post_ep(post_id: str):
    p = repo_get_post(post_id)
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")
    with get_session() as db:
        return PostOut.from_db(p, db)

@app.delete("/posts/{post_id}", status_code=204)
def delete_post_ep(post_id: str):
    ok = repo_delete_post(post_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Post not found")
    return None

@app.post("/posts/{post_id}/like", response_model=PostOut)
def like_post(post_id: str):
    with get_session() as db:
        p = db.get(DBPost, post_id)
        if not p:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Toggle like (increment if not liked, decrement if liked)
        liked_status = True  # In a real app, would check user's like status
        if liked_status:
            p.likes_count = (p.likes_count or 0) + 1
        else:
            p.likes_count = max(0, (p.likes_count or 0) - 1)
            
        db.commit(); db.refresh(p)
        return PostOut.from_db(p, db)

@app.post("/posts/{post_id}/repost", response_model=PostOut)
def repost_post(post_id: str):
    with get_session() as db:
        p = db.get(DBPost, post_id)
        if not p:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Toggle repost (increment if not reposted, decrement if reposted)
        reposted_status = True  # In a real app, would check user's repost status
        if reposted_status:
            p.reposts_count = (p.reposts_count or 0) + 1
        else:
            p.reposts_count = max(0, (p.reposts_count or 0) - 1)
            
        db.commit(); db.refresh(p)
        return PostOut.from_db(p, db)

@app.get("/conversations", response_model=list[ConversationOut])
def list_conversations():
    with get_session() as db:
        convs: list[DBConversation] = db.query(DBConversation).all()
        results: list[ConversationOut] = []
        for c in convs:
            parts = db.query(ConversationParticipant)\
                .filter(ConversationParticipant.conversation_id == c.id).all()
            handles: list[str] = []
            for uid in (p.user_id for p in parts):
                user = db.get(DBUser, uid)
                if user:
                    handles.append(user.handle)
            last = (db.query(DBMessage).filter(DBMessage.conversation_id == c.id)
                    .order_by(DBMessage.created_at.desc()).first())
            # choose a display username (first other participant)
            username = handles[0] if handles else "unknown"
            results.append(ConversationOut(
                id=c.id,
                username=(handles[1] if len(handles) > 1 else username),
                last_message=(last.content if last else None),
                timestamp=(last.created_at if last else None),
                unread=False,
            ))
        return results

@app.get("/conversations/{conv_id}/messages", response_model=list[MessageOut])
def get_conversation_messages(conv_id: str, limit: Limit500 = 100):
    with get_session() as db:
        msgs = list_dm(conv_id, limit=limit)
        return [MessageOut.from_db(m, db) for m in msgs]

@app.post("/conversations/{conv_id}/messages", response_model=MessageOut, status_code=201)
def send_conversation_message(conv_id: str, payload: MessageCreate):
    sender = _get_or_create_user(payload.sender_handle)
    m = send_dm(conversation_id=conv_id, sender_id=sender.id, text=payload.content)
    with get_session() as db:
        return MessageOut.from_db(m, db)

@app.post("/dm", response_model=ConversationOut, status_code=201)
def open_dm(req: DMOpenRequest):
    a = _get_or_create_user(req.user_a_handle)
    b = _get_or_create_user(req.user_b_handle)
    conv = get_or_create_dm(a.id, b.id)
    other = b.handle if a.handle == req.user_a_handle else a.handle
    return ConversationOut(id=conv.id, username=other, last_message=None, timestamp=None, unread=False)

@app.get("/notifications", response_model=list[NotificationOut])
def get_notifications(handle: str = "yourname"):
    user = _get_or_create_user(handle)
    with get_session() as db:
        rows: list[DBNotification] = (
            db.query(DBNotification).filter(DBNotification.user_id == user.id)
            .order_by(DBNotification.created_at.desc()).all()
        )
        results: list[NotificationOut] = []
        for n in rows:
            actor = db.get(DBUser, n.actor_id)
            results.append(NotificationOut(
                id=n.id,
                type=n.type,
                actor=(actor.handle if actor else "unknown"),
                content=n.content or "",
                timestamp=n.created_at,
                read=bool(n.read),
                related_post=(n.related_post_id if n.related_post_id else None),
            ))
        return results

@app.post("/notifications/{notif_id}/read")
def mark_notification_read_ep(notif_id: str):
    ok = repo_mark_notification_read(notif_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"ok": True}

@app.get("/posts/{post_id}/comments")
def get_comments(post_id: str):
    """Return comments for a post"""
    # Check if post exists
    p = repo_get_post(post_id)
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")
        
    # In a real app, these would be stored in a comments table
    # For now, return dummy data matching format expected by frontend
    comments = [
        {"user": "alice", "text": "Looks awesome!"},
        {"user": "bob", "text": "🔥"}
    ]
    return comments

@app.post("/posts/{post_id}/comments")
def add_comment(post_id: str, comment: CommentIn):
    """Add a comment to a post"""
    with get_session() as db:
        # Check if post exists
        p = db.get(DBPost, post_id)
        if not p:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Increment comments count
        p.comments_count = (p.comments_count or 0) + 1
        db.commit()
        
        # In a real app, we would add to a comments table
        # For now, just echo back the comment
        return {"user": comment.user, "text": comment.text}

@app.get("/diag/db")
def db_diagnostics():
    """Diagnostic endpoint for database troubleshooting."""
    try:
        diagnostics = {
            "status": "operational",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database_url_type": DATABASE_URL.split(":")[0],
            "connection_test": None,
            "table_counts": {},
        }
        
        # Test basic connection
        with get_session() as db:
            diagnostics["connection_test"] = "success"
            
            # Get table counts
            tables = ["users", "posts", "follows", "conversations", 
                      "conversation_participants", "messages", "notifications"]
            
            for table in tables:
                try:
                    count = db.execute(f"SELECT COUNT(*) FROM {table}").scalar()
                    diagnostics["table_counts"][table] = count
                except Exception as e:
                    diagnostics["table_counts"][table] = f"Error: {str(e)}"
                    
        return diagnostics
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }

@app.get("/settings", response_model=Settings)
def get_settings(handle: str = "yourname"):
    return _settings_for(_get_or_create_user(handle))

@app.put("/settings", response_model=Settings)
def put_settings(payload: Settings, handle: str = "yourname"):
    u = _get_or_create_user(handle)
    _ = update_user_bio(u.id, payload.bio)
    with get_session() as db:
        dbu = db.get(DBUser, u.id)
        if dbu:
            dbu.display_name = payload.display_name
            db.commit()
    _SETTINGS_STORE[u.id] = payload
    return payload
