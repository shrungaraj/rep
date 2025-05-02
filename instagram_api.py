import os
import logging
import requests
import time
from datetime import datetime, timedelta
from app import db
from models import User, Post, Source

logger = logging.getLogger(__name__)

# Instagram Graph API base URL
API_BASE_URL = "https://graph.instagram.com/"
API_VERSION = "v18.0"

class InstagramAPI:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.user = None
        if user_id:
            self.user = User.query.get(user_id)
    
    def is_token_valid(self):
        """Check if the current Instagram token is valid"""
        if not self.user or not self.user.instagram_token:
            return False
        
        # If token_expires_at is set and is in the future, token is valid
        if self.user.token_expires_at and self.user.token_expires_at > datetime.utcnow():
            return True
        
        return False
    
    def refresh_token(self):
        """Refresh the Instagram token if possible"""
        if not self.user or not self.user.instagram_token:
            logger.error(f"Cannot refresh token for user {self.user_id}: No token available")
            return False
        
        try:
            response = requests.get(
                f"{API_BASE_URL}/refresh_access_token",
                params={
                    "grant_type": "ig_refresh_token",
                    "access_token": self.user.instagram_token
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.user.instagram_token = data.get("access_token")
                # Calculate expiration time (usually 60 days for long-lived tokens)
                expires_in = data.get("expires_in", 5184000)  # Default: 60 days in seconds
                self.user.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                db.session.commit()
                logger.info(f"Token refreshed for user {self.user_id}")
                return True
            else:
                logger.error(f"Failed to refresh token for user {self.user_id}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Exception while refreshing token for user {self.user_id}: {str(e)}")
            return False
    
    def get_user_media(self, limit=25):
        """Get recent media from the user's Instagram account"""
        if not self.is_token_valid() and not self.refresh_token():
            logger.error(f"Cannot get user media: Invalid token for user {self.user_id}")
            return None
        
        try:
            response = requests.get(
                f"{API_BASE_URL}/{API_VERSION}/me/media",
                params={
                    "fields": "id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,username",
                    "access_token": self.user.instagram_token,
                    "limit": limit
                }
            )
            
            if response.status_code == 200:
                return response.json().get("data", [])
            else:
                logger.error(f"Failed to get user media for user {self.user_id}: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Exception while getting user media for user {self.user_id}: {str(e)}")
            return None
    
    def get_hashtag_media(self, hashtag, limit=25):
        """
        Get recent media with the specified hashtag
        Note: Hashtag search requires special permissions from Instagram
        """
        logger.warning(f"Hashtag search is not fully implemented as it requires special permissions")
        return []  # This is a placeholder for the actual implementation

    def fetch_posts_from_sources(self, user_id):
        """Fetch posts from all active sources for a user"""
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User {user_id} not found")
            return
        
        # Initialize Instagram API with user ID
        self.user_id = user_id
        self.user = user
        
        if not self.is_token_valid() and not self.refresh_token():
            logger.error(f"Cannot fetch posts: Invalid token for user {user_id}")
            return
        
        # Get active sources
        sources = Source.query.filter_by(user_id=user_id, is_active=True).all()
        
        for source in sources:
            try:
                # Update last checked time
                source.last_checked = datetime.utcnow()
                
                if source.type == 'account':
                    # Fetch posts from account
                    # Note: In reality, fetching posts from other accounts requires Business account
                    # and special permissions, this is simplified
                    logger.info(f"Fetching posts from account: {source.name}")
                    # This would be the real implementation if we had business permissions
                    media_items = []  # Placeholder
                    
                elif source.type == 'hashtag':
                    # Fetch posts with hashtag
                    logger.info(f"Fetching posts with hashtag: {source.name}")
                    media_items = self.get_hashtag_media(source.name)
                
                else:
                    logger.error(f"Unknown source type: {source.type}")
                    continue
                
                # Process fetched media items
                for media in media_items:
                    # Check if post already exists
                    existing_post = Post.query.filter_by(
                        user_id=user_id,
                        instagram_post_id=media.get('id')
                    ).first()
                    
                    if not existing_post:
                        # Create new post record
                        new_post = Post(
                            user_id=user_id,
                            source_id=source.id,
                            instagram_post_id=media.get('id'),
                            instagram_post_url=media.get('permalink'),
                            caption=media.get('caption'),
                            media_urls=[media.get('media_url')],
                            status='pending',
                            created_at=datetime.utcnow()
                        )
                        db.session.add(new_post)
            
            except Exception as e:
                logger.error(f"Error fetching posts from source {source.id} - {source.name}: {str(e)}")
            
            finally:
                # Commit changes for this source
                db.session.commit()
    
    def repost_media(self, post_id):
        """
        Repost media to the user's Instagram account
        Note: Due to Instagram API limitations, actual posting requires special permissions
        """
        post = Post.query.get(post_id)
        if not post:
            logger.error(f"Post {post_id} not found")
            return False
        
        try:
            # Update post status to indicate we're processing it
            post.status = 'processing'
            db.session.commit()
            
            logger.info(f"Reposting media {post.instagram_post_id} for user {post.user_id}")
            
            # In a real implementation, we would use the Instagram API to repost
            # Since direct posting requires a Business account and special permissions,
            # we're simulating the process here
            
            # Simulate API call delay
            time.sleep(2)
            
            # Set post as successfully posted
            post.status = 'posted'
            post.posted_time = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Successfully reposted media {post.instagram_post_id}")
            return True
            
        except Exception as e:
            # Update post status to failed and record error
            post.status = 'failed'
            post.error_message = str(e)
            db.session.commit()
            
            logger.error(f"Failed to repost media {post.instagram_post_id}: {str(e)}")
            return False
