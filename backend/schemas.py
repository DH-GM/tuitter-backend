"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# User schemas
class UserBase(BaseModel):
    username: str
    display_name: str
    bio: str = ""
    ascii_pic: str = ""


class UserResponse(UserBase):
    id: int
    handle: str  # alias for username
    followers: int
    following: int
    posts_count: int
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm(cls, user):
        return cls(
            id=user.id,
            username=user.username,
            handle=user.username,
            display_name=user.display_name,
            bio=user.bio,
            followers=user.followers,
            following=user.following,
            posts_count=user.posts_count,
            ascii_pic=user.ascii_pic
        )


# Post schemas
class PostCreate(BaseModel):
    content: str


class PostResponse(BaseModel):
    id: int
    author: str
    author_handle: str
    author_id: int
    content: str
    timestamp: datetime
    created_at: datetime
    likes: int
    likes_count: int
    reposts: int
    reposts_count: int
    comments: int
    comments_count: int
    liked_by_user: bool = False
    reposted_by_user: bool = False
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm(cls, post, user_id: Optional[int] = None, liked_by_user: bool = False, reposted_by_user: bool = False):
        return cls(
            id=post.id,
            author=post.author_handle,
            author_handle=post.author_handle,
            author_id=post.author_id,
            content=post.content,
            timestamp=post.created_at,
            created_at=post.created_at,
            likes=post.likes_count,
            likes_count=post.likes_count,
            reposts=post.reposts_count,
            reposts_count=post.reposts_count,
            comments=post.comments_count,
            comments_count=post.comments_count,
            liked_by_user=liked_by_user,
            reposted_by_user=reposted_by_user
        )


# Comment schemas
class CommentCreate(BaseModel):
    text: str


class CommentResponse(BaseModel):
    user: str
    text: str
    
    class Config:
        from_attributes = True


# Message schemas
class MessageCreate(BaseModel):
    content: str
    sender_handle: str


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    content: str
    timestamp: datetime
    created_at: datetime
    is_read: bool
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm(cls, message):
        return cls(
            id=message.id,
            sender_id=message.sender_id,
            content=message.content,
            timestamp=message.created_at,
            created_at=message.created_at,
            is_read=message.is_read
        )


# Conversation schemas
class ConversationCreate(BaseModel):
    user_a_handle: str
    user_b_handle: str


class ConversationResponse(BaseModel):
    id: int
    participant_handles: List[str]
    last_message_preview: str
    last_message_at: datetime
    unread: bool = False
    
    class Config:
        from_attributes = True


# Notification schemas
class NotificationResponse(BaseModel):
    id: int
    type: str
    actor: str
    username: str
    content: str
    timestamp: datetime
    created_at: datetime
    read: bool
    post_id: Optional[int] = None
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm(cls, notification):
        return cls(
            id=notification.id,
            type=notification.type,
            actor=notification.actor_handle,
            username=notification.actor_handle,
            content=notification.content,
            timestamp=notification.created_at,
            created_at=notification.created_at,
            read=notification.read,
            post_id=notification.post_id
        )


# Settings schemas
class SettingsUpdate(BaseModel):
    username: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    email_notifications: Optional[bool] = None
    show_online_status: Optional[bool] = None
    private_account: Optional[bool] = None
    ascii_pic: Optional[str] = None


class SettingsResponse(BaseModel):
    username: str
    display_name: str
    bio: str
    email_notifications: bool
    show_online_status: bool
    private_account: bool
    github_connected: bool
    gitlab_connected: bool
    google_connected: bool
    discord_connected: bool
    ascii_pic: str
    
    class Config:
        from_attributes = True

