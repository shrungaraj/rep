import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import current_app
from datetime import datetime, timedelta
from app import db
from models import User, UserSettings, Post, Source
from instagram_api import InstagramAPI

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()

def init_scheduler(app):
    """Initialize the scheduler with the Flask app context"""
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")
        
        # Register a function to shut down the scheduler when the app is shutting down
        app.teardown_appcontext(lambda exception: scheduler.shutdown(wait=False) if scheduler.running else None)
        
        # Add the default jobs
        with app.app_context():
            # Schedule job to check for new posts from sources
            scheduler.add_job(
                check_sources_for_new_posts,
                IntervalTrigger(minutes=15),
                id='check_sources',
                replace_existing=True
            )
            
            # Schedule job to process pending posts
            scheduler.add_job(
                process_pending_posts,
                IntervalTrigger(minutes=5),
                id='process_posts',
                replace_existing=True
            )
            
            # Schedule job to refresh tokens that are about to expire
            scheduler.add_job(
                refresh_expiring_tokens,
                IntervalTrigger(hours=24),
                id='refresh_tokens',
                replace_existing=True
            )
            
            logger.info("Scheduled default jobs")


def check_sources_for_new_posts():
    """Check all active sources for new posts"""
    logger.info("Checking sources for new posts")
    try:
        # Get all users with active settings
        users = User.query.join(UserSettings).filter(UserSettings.auto_repost.is_(True)).all()
        
        for user in users:
            # Get user settings
            settings = user.settings
            
            # Check if we should run based on the check interval
            if not settings or not settings.check_interval:
                continue
            
            # Find active sources that haven't been checked within the interval
            check_time = datetime.utcnow() - timedelta(minutes=settings.check_interval)
            sources = Source.query.filter(
                Source.user_id == user.id,
                Source.is_active.is_(True),
                (Source.last_checked.is_(None) | (Source.last_checked < check_time))
            ).all()
            
            if sources:
                instagram_api = InstagramAPI(user.id)
                instagram_api.fetch_posts_from_sources(user.id)
                
    except Exception as e:
        logger.error(f"Error checking sources for new posts: {str(e)}")


def process_pending_posts():
    """Process pending posts for all users"""
    logger.info("Processing pending posts")
    try:
        # Get all users with auto_repost enabled
        users = User.query.join(UserSettings).filter(UserSettings.auto_repost.is_(True)).all()
        
        for user in users:
            # Get user settings
            settings = user.settings
            
            # Check if we can repost
            if not settings:
                continue
            
            # Count posts already made today
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            posts_today = Post.query.filter(
                Post.user_id == user.id,
                Post.status == 'posted',
                Post.posted_time >= today_start
            ).count()
            
            # Check if we've hit the daily limit
            if posts_today >= settings.post_limit_per_day:
                logger.info(f"User {user.id} has reached daily post limit of {settings.post_limit_per_day}")
                continue
            
            # Get oldest pending posts up to the remaining limit
            remaining_posts = settings.post_limit_per_day - posts_today
            
            # Get pending posts that are scheduled to be posted now or in the past
            current_time = datetime.utcnow()
            pending_posts = Post.query.filter(
                Post.user_id == user.id,
                Post.status == 'pending',
                (Post.scheduled_time.is_(None) | (Post.scheduled_time <= current_time))
            ).order_by(Post.created_at.asc()).limit(remaining_posts).all()
            
            # Process each post
            for post in pending_posts:
                try:
                    instagram_api = InstagramAPI(user.id)
                    
                    # If repost is successful, update the status
                    if instagram_api.repost_media(post.id):
                        logger.info(f"Successfully reposted post {post.id} for user {user.id}")
                    else:
                        logger.error(f"Failed to repost post {post.id} for user {user.id}")
                    
                except Exception as e:
                    logger.error(f"Error processing post {post.id}: {str(e)}")
                    post.status = 'failed'
                    post.error_message = str(e)
                    db.session.commit()
            
    except Exception as e:
        logger.error(f"Error processing pending posts: {str(e)}")


def refresh_expiring_tokens():
    """Refresh tokens that are about to expire"""
    logger.info("Refreshing expiring tokens")
    try:
        # Find tokens that expire in the next 7 days
        expiration_threshold = datetime.utcnow() + timedelta(days=7)
        users = User.query.filter(
            User.instagram_token.isnot(None),
            User.token_expires_at < expiration_threshold
        ).all()
        
        for user in users:
            instagram_api = InstagramAPI(user.id)
            if instagram_api.refresh_token():
                logger.info(f"Successfully refreshed token for user {user.id}")
            else:
                logger.error(f"Failed to refresh token for user {user.id}")
                
    except Exception as e:
        logger.error(f"Error refreshing expiring tokens: {str(e)}")


def schedule_post(post_id, scheduled_time=None):
    """Schedule a post to be published at the specified time"""
    try:
        post = Post.query.get(post_id)
        if not post:
            logger.error(f"Post {post_id} not found")
            return False
        
        # If no scheduled time is provided, use the current time plus the user's repost delay
        if scheduled_time is None:
            user_settings = UserSettings.query.filter_by(user_id=post.user_id).first()
            delay_minutes = user_settings.repost_delay if user_settings else 0
            scheduled_time = datetime.utcnow() + timedelta(minutes=delay_minutes)
        
        # Update the post's scheduled time
        post.scheduled_time = scheduled_time
        db.session.commit()
        
        logger.info(f"Post {post_id} scheduled for {scheduled_time}")
        return True
        
    except Exception as e:
        logger.error(f"Error scheduling post {post_id}: {str(e)}")
        return False
