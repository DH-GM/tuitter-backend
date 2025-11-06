"""
CRUD (Create, Read, Update, Delete) operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from typing import List, Optional
import models
import schemas
import json

def get_conversations_for_user(db: Session, user_id: int):
    """Get all conversations for a user using the junction table"""
    return db.query(models.Conversation).join(
        models.conversation_participants,
        models.Conversation.id == models.conversation_participants.c.conversation_id
    ).filter(
        models.conversation_participants.c.user_id == user_id
    ).all()


def get_or_create_conversation(db: Session, user_a_id: int, user_b_id: int):
    """Get or create a conversation between two users"""
    # Find existing conversation between these two users
    # This is more complex with many-to-many, so we need to find conversations
    # where both users are participants
    
    # Subquery to find conversations with user_a
    conv_with_a = db.query(models.conversation_participants.c.conversation_id).filter(
        models.conversation_participants.c.user_id == user_a_id
    ).subquery()
    
    # Subquery to find conversations with user_b
    conv_with_b = db.query(models.conversation_participants.c.conversation_id).filter(
        models.conversation_participants.c.user_id == user_b_id
    ).subquery()
    
    # Find conversations that have both users
    existing_conv = db.query(models.Conversation).filter(
        and_(
            models.Conversation.id.in_(conv_with_a),
            models.Conversation.id.in_(conv_with_b)
        )
    ).first()
    
    if existing_conv:
        return existing_conv
    
    # Create new conversation
    new_conv = models.Conversation()
    db.add(new_conv)
    db.flush()  # Get the ID
    
    # Add both participants to the junction table
    db.execute(
        models.conversation_participants.insert().values([
            {"conversation_id": new_conv.id, "user_id": user_a_id},
            {"conversation_id": new_conv.id, "user_id": user_b_id}
        ])
    )
    db.commit()
    db.refresh(new_conv)
    
    return new_conv


def get_messages_for_conversation(db: Session, conversation_id: int):
    """Get all messages in a conversation, ordered by timestamp"""
    return db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).order_by(models.Message.timestamp.asc()).all()


def create_message(db: Session, conversation_id: int, sender_id: int, sender_handle: str, content: str):
    """Create a new message in a conversation"""
    message = models.Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        sender_handle=sender_handle,
        content=content
    )
    db.add(message)
    
    # Update conversation's last message (if you add these columns to the conversations table)
    # conversation = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
    # if conversation:
    #     conversation.last_message_preview = content[:100]
    #     conversation.last_message_at = datetime.utcnow()
    
    db.commit()
    db.refresh(message)
    return message

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


def create_post(db: Session, user_id: int, username: str, content: str, attachments: Optional[List[dict]] = None) -> models.Post:
    """Create a new post"""
    # Validate attachment size before creating post
    if attachments:
        serialized = json.dumps(attachments)
        if len(serialized) > 16384:
            raise ValueError("Attachments exceed maximum size of 16384 characters")

    post = models.Post(
        author_id=user_id,
        author_handle=username,
        content=content,
        attachments=attachments  # JSONString type will handle serialization
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

def get_conversation_by_id(db: Session, conversation_id: int) -> Optional[models.Conversation]:
    """Get a conversation by ID"""
    return db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()

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

