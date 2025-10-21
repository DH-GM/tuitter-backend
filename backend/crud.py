"""
CRUD (Create, Read, Update, Delete) operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from typing import List, Optional
import models
import schemas


# ========== USER OPERATIONS ==========

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Get a user by username"""
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    """Get a user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()


# ========== POST OPERATIONS ==========

def get_timeline_posts(db: Session, limit: int = 50) -> List[models.Post]:
    """Get timeline posts (all posts, ordered by most recent)"""
    return db.query(models.Post).order_by(desc(models.Post.created_at)).limit(limit).all()


def get_discover_posts(db: Session, limit: int = 50) -> List[models.Post]:
    """Get discover posts (trending/popular posts)"""
    # For demo, return posts ordered by engagement (likes + reposts + comments)
    return db.query(models.Post).order_by(
        desc(models.Post.likes_count + models.Post.reposts_count + models.Post.comments_count)
    ).limit(limit).all()


def create_post(db: Session, user_id: int, username: str, content: str) -> models.Post:
    """Create a new post"""
    post = models.Post(
        author_id=user_id,
        author_handle=username,
        content=content
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Update user's posts count
    user = get_user_by_id(db, user_id)
    if user:
        user.posts_count += 1
        db.commit()
    
    return post


def get_post_by_id(db: Session, post_id: int) -> Optional[models.Post]:
    """Get a post by ID"""
    return db.query(models.Post).filter(models.Post.id == post_id).first()


# ========== POST INTERACTION OPERATIONS ==========

def get_user_interaction(db: Session, post_id: int, user_id: int, interaction_type: str) -> Optional[models.PostInteraction]:
    """Check if user has interacted with a post"""
    return db.query(models.PostInteraction).filter(
        models.PostInteraction.post_id == post_id,
        models.PostInteraction.user_id == user_id,
        models.PostInteraction.interaction_type == interaction_type
    ).first()


def toggle_like(db: Session, post_id: int, user_id: int) -> bool:
    """Toggle like on a post"""
    post = get_post_by_id(db, post_id)
    if not post:
        return False
    
    existing = get_user_interaction(db, post_id, user_id, "like")
    
    if existing:
        # Unlike
        db.delete(existing)
        post.likes_count = max(0, post.likes_count - 1)
    else:
        # Like
        interaction = models.PostInteraction(
            post_id=post_id,
            user_id=user_id,
            interaction_type="like"
        )
        db.add(interaction)
        post.likes_count += 1
    
    db.commit()
    return True


def toggle_repost(db: Session, post_id: int, user_id: int) -> bool:
    """Toggle repost on a post"""
    post = get_post_by_id(db, post_id)
    if not post:
        return False
    
    existing = get_user_interaction(db, post_id, user_id, "repost")
    
    if existing:
        # Unrepost
        db.delete(existing)
        post.reposts_count = max(0, post.reposts_count - 1)
    else:
        # Repost
        interaction = models.PostInteraction(
            post_id=post_id,
            user_id=user_id,
            interaction_type="repost"
        )
        db.add(interaction)
        post.reposts_count += 1
    
    db.commit()
    return True


def check_user_liked_post(db: Session, post_id: int, user_id: int) -> bool:
    """Check if user liked a post"""
    return get_user_interaction(db, post_id, user_id, "like") is not None


def check_user_reposted(db: Session, post_id: int, user_id: int) -> bool:
    """Check if user reposted a post"""
    return get_user_interaction(db, post_id, user_id, "repost") is not None


# ========== COMMENT OPERATIONS ==========

def get_comments(db: Session, post_id: int) -> List[models.Comment]:
    """Get all comments for a post"""
    return db.query(models.Comment).filter(
        models.Comment.post_id == post_id
    ).order_by(models.Comment.created_at).all()


def add_comment(db: Session, post_id: int, user_id: int, username: str, text: str) -> models.Comment:
    """Add a comment to a post"""
    comment = models.Comment(
        post_id=post_id,
        user_id=user_id,
        username=username,
        text=text
    )
    db.add(comment)
    
    # Update post comments count
    post = get_post_by_id(db, post_id)
    if post:
        post.comments_count += 1
    
    db.commit()
    db.refresh(comment)
    return comment


# ========== CONVERSATION OPERATIONS ==========

def get_conversations_for_user(db: Session, user_id: int) -> List[models.Conversation]:
    """Get all conversations for a user"""
    return db.query(models.Conversation).filter(
        or_(
            models.Conversation.participant_a_id == user_id,
            models.Conversation.participant_b_id == user_id
        )
    ).order_by(desc(models.Conversation.last_message_at)).all()


def get_conversation_by_id(db: Session, conversation_id: int) -> Optional[models.Conversation]:
    """Get a conversation by ID"""
    return db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()


def get_or_create_conversation(db: Session, user_a_id: int, user_b_id: int) -> models.Conversation:
    """Get or create a conversation between two users"""
    # Ensure participant_a_id < participant_b_id
    min_id, max_id = min(user_a_id, user_b_id), max(user_a_id, user_b_id)
    
    # Check if conversation exists
    conversation = db.query(models.Conversation).filter(
        models.Conversation.participant_a_id == min_id,
        models.Conversation.participant_b_id == max_id
    ).first()
    
    if conversation:
        return conversation
    
    # Create new conversation
    conversation = models.Conversation(
        participant_a_id=min_id,
        participant_b_id=max_id
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


# ========== MESSAGE OPERATIONS ==========

def get_messages_for_conversation(db: Session, conversation_id: int) -> List[models.Message]:
    """Get all messages for a conversation"""
    return db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).order_by(models.Message.created_at).all()


def create_message(db: Session, conversation_id: int, sender_id: int, sender_handle: str, content: str) -> models.Message:
    """Create a new message in a conversation"""
    message = models.Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        sender_handle=sender_handle,
        content=content,
        is_read=False
    )
    db.add(message)
    
    # Update conversation's last message
    conversation = get_conversation_by_id(db, conversation_id)
    if conversation:
        conversation.last_message_preview = content[:50] + "..." if len(content) > 50 else content
        conversation.last_message_at = message.created_at
    
    db.commit()
    db.refresh(message)
    return message


# ========== NOTIFICATION OPERATIONS ==========

def get_notifications_for_user(db: Session, user_id: int, unread_only: bool = False) -> List[models.Notification]:
    """Get notifications for a user"""
    query = db.query(models.Notification).filter(models.Notification.user_id == user_id)
    
    if unread_only:
        query = query.filter(models.Notification.read == False)
    
    return query.order_by(desc(models.Notification.created_at)).all()


def mark_notification_read(db: Session, notification_id: int) -> bool:
    """Mark a notification as read"""
    notification = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if not notification:
        return False
    
    notification.read = True
    db.commit()
    return True


# ========== SETTINGS OPERATIONS ==========

def get_user_settings(db: Session, user_id: int) -> Optional[models.UserSettings]:
    """Get user settings"""
    return db.query(models.UserSettings).filter(models.UserSettings.user_id == user_id).first()


def update_user_settings(db: Session, user_id: int, settings_update: schemas.SettingsUpdate) -> Optional[models.UserSettings]:
    """Update user settings"""
    settings = get_user_settings(db, user_id)
    if not settings:
        # Create default settings if they don't exist
        settings = models.UserSettings(user_id=user_id)
        db.add(settings)
    
    # Update settings fields
    update_data = settings_update.model_dump(exclude_unset=True)
    
    # Handle user profile updates separately
    if 'username' in update_data or 'display_name' in update_data or 'bio' in update_data or 'ascii_pic' in update_data:
        user = get_user_by_id(db, user_id)
        if user:
            if 'username' in update_data:
                user.username = update_data.pop('username')
            if 'display_name' in update_data:
                user.display_name = update_data.pop('display_name')
            if 'bio' in update_data:
                user.bio = update_data.pop('bio')
            if 'ascii_pic' in update_data:
                user.ascii_pic = update_data.pop('ascii_pic')
    
    # Update remaining settings
    for key, value in update_data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    
    db.commit()
    db.refresh(settings)
    return settings

