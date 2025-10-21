"""
FastAPI backend for Social.vim application
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn

import models
import schemas
import crud
from database import engine, get_db

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Social.vim API",
    description="Backend API for Social.vim TUI application",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== UTILITY FUNCTIONS ==========

def get_current_user_from_handle(db: Session, handle: str, auto_create: bool = True) -> models.User:
    """
    Get current user by handle (username).
    Auto-creates user if they don't exist (when auto_create=True).
    """
    user = crud.get_user_by_username(db, handle)
    
    if not user and auto_create:
        # Auto-create new user
        user = models.User(
            username=handle,
            display_name=handle.capitalize(),
            bio=f"Hi, I'm {handle}!",
            followers=0,
            following=0,
            posts_count=0
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create default settings
        settings = models.UserSettings(
            user_id=user.id,
            email_notifications=True,
            show_online_status=True,
            private_account=False
        )
        db.add(settings)
        db.commit()
    elif not user:
        raise HTTPException(status_code=404, detail=f"User '{handle}' not found")
    
    return user


# ========== USER ENDPOINTS ==========

@app.get("/me", response_model=schemas.UserResponse)
def get_current_user(
    handle: str = Query(..., description="Username/handle of the current user"),
    db: Session = Depends(get_db)
):
    """
    Get current user profile.
    Auto-creates user if they don't exist (for demo purposes).
    """
    user = get_current_user_from_handle(db, handle, auto_create=True)
    return schemas.UserResponse.from_orm(user)


# ========== POST ENDPOINTS ==========

@app.get("/timeline", response_model=List[schemas.PostResponse])
def get_timeline(
    limit: int = Query(50, ge=1, le=100),
    handle: str = Query("yourname", description="Current user handle"),
    db: Session = Depends(get_db)
):
    """Get timeline posts (recent posts from all users)"""
    posts = crud.get_timeline_posts(db, limit)
    
    # Get current user to check interactions
    user = crud.get_user_by_username(db, handle)
    user_id = user.id if user else None
    
    # Build response with user interaction status
    result = []
    for post in posts:
        liked = crud.check_user_liked_post(db, post.id, user_id) if user_id else False
        reposted = crud.check_user_reposted(db, post.id, user_id) if user_id else False
        result.append(schemas.PostResponse.from_orm(post, user_id, liked, reposted))
    
    return result


@app.get("/discover", response_model=List[schemas.PostResponse])
def get_discover(
    limit: int = Query(50, ge=1, le=100),
    handle: str = Query("yourname", description="Current user handle"),
    db: Session = Depends(get_db)
):
    """Get discover posts (trending/popular posts)"""
    posts = crud.get_discover_posts(db, limit)
    
    # Get current user to check interactions
    user = crud.get_user_by_username(db, handle)
    user_id = user.id if user else None
    
    # Build response with user interaction status
    result = []
    for post in posts:
        liked = crud.check_user_liked_post(db, post.id, user_id) if user_id else False
        reposted = crud.check_user_reposted(db, post.id, user_id) if user_id else False
        result.append(schemas.PostResponse.from_orm(post, user_id, liked, reposted))
    
    return result


@app.post("/posts", response_model=schemas.PostResponse)
def create_post(
    post_data: schemas.PostCreate,
    handle: str = Query("yourname", description="Current user handle"),
    db: Session = Depends(get_db)
):
    """Create a new post"""
    user = get_current_user_from_handle(db, handle)
    post = crud.create_post(db, user.id, user.username, post_data.content)
    return schemas.PostResponse.from_orm(post, user.id, False, False)


@app.post("/posts/{post_id}/like")
def like_post(
    post_id: int,
    handle: str = Query("yourname", description="Current user handle"),
    db: Session = Depends(get_db)
):
    """Toggle like on a post"""
    user = get_current_user_from_handle(db, handle)
    success = crud.toggle_like(db, post_id, user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"success": True}


@app.post("/posts/{post_id}/repost")
def repost_post(
    post_id: int,
    handle: str = Query("yourname", description="Current user handle"),
    db: Session = Depends(get_db)
):
    """Toggle repost on a post"""
    user = get_current_user_from_handle(db, handle)
    success = crud.toggle_repost(db, post_id, user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"success": True}


# ========== COMMENT ENDPOINTS ==========

@app.get("/posts/{post_id}/comments", response_model=List[schemas.CommentResponse])
def get_comments(
    post_id: int,
    db: Session = Depends(get_db)
):
    """Get all comments for a post"""
    comments = crud.get_comments(db, post_id)
    return [schemas.CommentResponse(user=c.username, text=c.text) for c in comments]


@app.post("/posts/{post_id}/comments", response_model=schemas.CommentResponse)
def add_comment(
    post_id: int,
    comment_data: schemas.CommentCreate,
    handle: str = Query("yourname", description="Current user handle"),
    db: Session = Depends(get_db)
):
    """Add a comment to a post"""
    user = get_current_user_from_handle(db, handle)
    comment = crud.add_comment(db, post_id, user.id, user.username, comment_data.text)
    return schemas.CommentResponse(user=comment.username, text=comment.text)


# ========== CONVERSATION & MESSAGE ENDPOINTS ==========

@app.get("/conversations", response_model=List[schemas.ConversationResponse])
def get_conversations(
    handle: str = Query("yourname", description="Current user handle"),
    db: Session = Depends(get_db)
):
    """Get all conversations for the current user"""
    user = get_current_user_from_handle(db, handle)
    conversations = crud.get_conversations_for_user(db, user.id)
    
    result = []
    for conv in conversations:
        # Get participant handles
        user_a = crud.get_user_by_id(db, conv.participant_a_id)
        user_b = crud.get_user_by_id(db, conv.participant_b_id)
        
        handles = []
        if user_a:
            handles.append(user_a.username)
        if user_b:
            handles.append(user_b.username)
        
        result.append(schemas.ConversationResponse(
            id=conv.id,
            participant_handles=handles,
            last_message_preview=conv.last_message_preview,
            last_message_at=conv.last_message_at,
            unread=False  # TODO: implement unread logic
        ))
    
    return result


@app.get("/conversations/{conversation_id}/messages", response_model=List[schemas.MessageResponse])
def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """Get all messages in a conversation"""
    messages = crud.get_messages_for_conversation(db, conversation_id)
    return [schemas.MessageResponse.from_orm(m) for m in messages]


@app.post("/conversations/{conversation_id}/messages", response_model=schemas.MessageResponse)
def send_message(
    conversation_id: int,
    message_data: schemas.MessageCreate,
    db: Session = Depends(get_db)
):
    """Send a message in a conversation"""
    sender = crud.get_user_by_username(db, message_data.sender_handle)
    if not sender:
        raise HTTPException(status_code=404, detail="Sender not found")
    
    message = crud.create_message(
        db, 
        conversation_id, 
        sender.id, 
        sender.username, 
        message_data.content
    )
    return schemas.MessageResponse.from_orm(message)


@app.post("/dm", response_model=schemas.ConversationResponse)
def get_or_create_dm(
    conversation_data: schemas.ConversationCreate,
    db: Session = Depends(get_db)
):
    """Get or create a direct message conversation between two users"""
    user_a = crud.get_user_by_username(db, conversation_data.user_a_handle)
    user_b = crud.get_user_by_username(db, conversation_data.user_b_handle)
    
    if not user_a:
        raise HTTPException(status_code=404, detail=f"User '{conversation_data.user_a_handle}' not found")
    if not user_b:
        raise HTTPException(status_code=404, detail=f"User '{conversation_data.user_b_handle}' not found")
    
    conversation = crud.get_or_create_conversation(db, user_a.id, user_b.id)
    
    return schemas.ConversationResponse(
        id=conversation.id,
        participant_handles=[user_a.username, user_b.username],
        last_message_preview=conversation.last_message_preview,
        last_message_at=conversation.last_message_at,
        unread=False
    )


# ========== NOTIFICATION ENDPOINTS ==========

@app.get("/notifications", response_model=List[schemas.NotificationResponse])
def get_notifications(
    unread: bool = Query(False, description="Get only unread notifications"),
    handle: str = Query("yourname", description="Current user handle"),
    db: Session = Depends(get_db)
):
    """Get notifications for the current user"""
    user = get_current_user_from_handle(db, handle)
    notifications = crud.get_notifications_for_user(db, user.id, unread)
    return [schemas.NotificationResponse.from_orm(n) for n in notifications]


@app.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    success = crud.mark_notification_read(db, notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}


# ========== SETTINGS ENDPOINTS ==========

@app.get("/settings", response_model=schemas.SettingsResponse)
def get_settings(
    handle: str = Query("yourname", description="Current user handle"),
    db: Session = Depends(get_db)
):
    """Get user settings"""
    user = get_current_user_from_handle(db, handle)
    settings = crud.get_user_settings(db, user.id)
    
    if not settings:
        # Return default settings with user info
        return schemas.SettingsResponse(
            username=user.username,
            display_name=user.display_name,
            bio=user.bio,
            email_notifications=True,
            show_online_status=True,
            private_account=False,
            github_connected=False,
            gitlab_connected=False,
            google_connected=False,
            discord_connected=False,
            ascii_pic=user.ascii_pic
        )
    
    return schemas.SettingsResponse(
        username=user.username,
        display_name=user.display_name,
        bio=user.bio,
        email_notifications=settings.email_notifications,
        show_online_status=settings.show_online_status,
        private_account=settings.private_account,
        github_connected=settings.github_connected,
        gitlab_connected=settings.gitlab_connected,
        google_connected=settings.google_connected,
        discord_connected=settings.discord_connected,
        ascii_pic=user.ascii_pic
    )


@app.put("/settings")
def update_settings(
    settings_update: schemas.SettingsUpdate,
    handle: str = Query("yourname", description="Current user handle"),
    db: Session = Depends(get_db)
):
    """Update user settings"""
    user = get_current_user_from_handle(db, handle)
    crud.update_user_settings(db, user.id, settings_update)
    return {"success": True}


# ========== HEALTH CHECK ==========

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "social.vim API"}


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "Social.vim API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.post("/admin/seed-database")
def seed_database(db: Session = Depends(get_db)):
    """
    Seed the database with demo data.
    Call this once after deployment to populate initial data.
    """
    try:
        # Check if data already exists
        existing_users = db.query(models.User).count()
        if existing_users > 0:
            return {"message": "Database already seeded", "users": existing_users}
        
        # Create demo users
        users_data = [
            {"username": "yourname", "display_name": "Your Name", "bio": "Building cool stuff with TUIs | vim enthusiast | developer", "followers": 891, "following": 328, "posts_count": 142},
            {"username": "alice", "display_name": "Alice Johnson", "bio": "Full-stack developer | Open source contributor", "followers": 1234, "following": 567, "posts_count": 89},
            {"username": "bob", "display_name": "Bob Smith", "bio": "Tech blogger | Code reviewer | Coffee enthusiast", "followers": 2345, "following": 890, "posts_count": 234},
            {"username": "charlie", "display_name": "Charlie Davis", "bio": "CLI tools developer | Rust advocate", "followers": 456, "following": 234, "posts_count": 67},
            {"username": "techwriter", "display_name": "Tech Writer", "bio": "Writing about technology and development", "followers": 3456, "following": 1234, "posts_count": 456},
            {"username": "cliexpert", "display_name": "CLI Expert", "bio": "Terminal user interface expert", "followers": 2890, "following": 1100, "posts_count": 389},
            {"username": "vimfan", "display_name": "Vim Fan", "bio": "Vim configuration enthusiast", "followers": 1567, "following": 678, "posts_count": 234},
            {"username": "opensource_dev", "display_name": "OpenSource Dev", "bio": "Building tools for developers", "followers": 1200, "following": 450, "posts_count": 156},
        ]
        
        created_users = {}
        for user_data in users_data:
            user = models.User(**user_data)
            db.add(user)
            db.flush()
            created_users[user.username] = user.id
            
            # Create settings for each user
            settings = models.UserSettings(
                user_id=user.id,
                email_notifications=True,
                show_online_status=True,
                private_account=False,
                github_connected=(user.username == "yourname")
            )
            db.add(settings)
        
        db.commit()
        
        # Create demo posts
        from datetime import datetime, timedelta
        now = datetime.now()
        
        posts_data = [
            {"author_id": created_users["yourname"], "author_handle": "yourname", "content": "Just shipped a new feature! The TUI is looking amazing 🚀", "likes_count": 12, "reposts_count": 3, "comments_count": 2, "created_at": now - timedelta(minutes=5)},
            {"author_id": created_users["alice"], "author_handle": "alice", "content": "Working on a new CLI tool for developers. Any testers?", "likes_count": 45, "reposts_count": 12, "comments_count": 1, "created_at": now - timedelta(minutes=15)},
            {"author_id": created_users["bob"], "author_handle": "bob", "content": "Refactoring is like cleaning your room. You know where everything is in the mess, but it's still better to organize it.", "likes_count": 234, "reposts_count": 67, "comments_count": 0, "created_at": now - timedelta(hours=1)},
            {"author_id": created_users["techwriter"], "author_handle": "techwriter", "content": "Just discovered this amazing TUI framework! #vim #tui #opensource", "likes_count": 234, "reposts_count": 45, "comments_count": 18, "created_at": now - timedelta(hours=2)},
            {"author_id": created_users["cliexpert"], "author_handle": "cliexpert", "content": "Hot take: TUIs are making a comeback! 💻", "likes_count": 189, "reposts_count": 52, "comments_count": 34, "created_at": now - timedelta(hours=4)},
            {"author_id": created_users["vimfan"], "author_handle": "vimfan", "content": "Finally got my vim config working with this social network.", "likes_count": 156, "reposts_count": 28, "comments_count": 12, "created_at": now - timedelta(hours=5)},
        ]
        
        created_posts = []
        for post_data in posts_data:
            post = models.Post(**post_data)
            db.add(post)
            db.flush()
            created_posts.append(post.id)
        
        db.commit()
        
        return {
            "success": True,
            "message": "Database seeded successfully!",
            "users_created": len(created_users),
            "posts_created": len(created_posts)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error seeding database: {str(e)}")


# ========== RUN SERVER ==========

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

