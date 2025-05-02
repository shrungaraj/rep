import os
import logging
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from models import User, Source, Post, UserSettings
from instagram_api import InstagramAPI
from scheduler import schedule_post

logger = logging.getLogger(__name__)

# Home route
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Basic validation
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        # Check if username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists', 'danger')
            return render_template('register.html')
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        # Create default settings for user
        default_settings = UserSettings(user=new_user)
        
        db.session.add(new_user)
        db.session.add(default_settings)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Main application routes
@app.route('/dashboard')
@login_required
def dashboard():
    # Get basic stats
    total_sources = Source.query.filter_by(user_id=current_user.id).count()
    active_sources = Source.query.filter_by(user_id=current_user.id, is_active=True).count()
    
    # Posts by status
    pending_posts = Post.query.filter_by(user_id=current_user.id, status='pending').count()
    posted_posts = Post.query.filter_by(user_id=current_user.id, status='posted').count()
    failed_posts = Post.query.filter_by(user_id=current_user.id, status='failed').count()
    
    # Recent posts
    recent_posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).limit(5).all()
    
    # Posts today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    posts_today = Post.query.filter(
        Post.user_id == current_user.id,
        Post.status == 'posted',
        Post.posted_time >= today_start
    ).count()
    
    # User settings
    settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    post_limit = settings.post_limit_per_day if settings else 5
    
    # Instagram connection status
    instagram_api = InstagramAPI(current_user.id)
    instagram_connected = instagram_api.is_token_valid()
    
    return render_template('dashboard.html',
                          total_sources=total_sources,
                          active_sources=active_sources,
                          pending_posts=pending_posts,
                          posted_posts=posted_posts,
                          failed_posts=failed_posts,
                          recent_posts=recent_posts,
                          posts_today=posts_today,
                          post_limit=post_limit,
                          instagram_connected=instagram_connected)

@app.route('/sources', methods=['GET'])
@login_required
def sources():
    sources = Source.query.filter_by(user_id=current_user.id).order_by(Source.created_at.desc()).all()
    return render_template('sources.html', sources=sources)

@app.route('/sources/add', methods=['POST'])
@login_required
def add_source():
    source_type = request.form.get('type')
    name = request.form.get('name')
    
    if not source_type or not name:
        flash('Source type and name are required', 'danger')
        return redirect(url_for('sources'))
    
    # Remove @ symbol from account names if present
    if source_type == 'account' and name.startswith('@'):
        name = name[1:]
    
    # Remove # symbol from hashtags if present
    if source_type == 'hashtag' and name.startswith('#'):
        name = name[1:]
    
    # Check if source already exists
    existing_source = Source.query.filter_by(
        user_id=current_user.id,
        type=source_type,
        name=name
    ).first()
    
    if existing_source:
        flash(f'This {source_type} is already in your list', 'warning')
        return redirect(url_for('sources'))
    
    # Create new source
    new_source = Source(
        user_id=current_user.id,
        type=source_type,
        name=name,
        is_active=True
    )
    
    db.session.add(new_source)
    db.session.commit()
    
    flash(f'New {source_type} source added successfully', 'success')
    return redirect(url_for('sources'))

@app.route('/sources/<int:source_id>/toggle', methods=['POST'])
@login_required
def toggle_source(source_id):
    source = Source.query.filter_by(id=source_id, user_id=current_user.id).first_or_404()
    
    source.is_active = not source.is_active
    db.session.commit()
    
    status = 'activated' if source.is_active else 'deactivated'
    flash(f'Source {source.name} {status} successfully', 'success')
    return redirect(url_for('sources'))

@app.route('/sources/<int:source_id>/delete', methods=['POST'])
@login_required
def delete_source(source_id):
    source = Source.query.filter_by(id=source_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(source)
    db.session.commit()
    
    flash(f'Source {source.name} deleted successfully', 'success')
    return redirect(url_for('sources'))

@app.route('/history')
@login_required
def history():
    # Filter parameters
    status_filter = request.args.get('status', 'all')
    days = request.args.get('days', '7')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Base query
    query = Post.query.filter_by(user_id=current_user.id)
    
    # Apply status filter
    if status_filter != 'all':
        query = query.filter(Post.status == status_filter)
    
    # Apply time filter
    if days.isdigit() and int(days) > 0:
        days_ago = datetime.utcnow() - timedelta(days=int(days))
        query = query.filter(Post.created_at >= days_ago)
    
    # Order by and paginate
    posts = query.order_by(Post.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('history.html', posts=posts, status_filter=status_filter, days=days)

@app.route('/post/<int:post_id>/repost', methods=['POST'])
@login_required
def repost_post(post_id):
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first_or_404()
    
    if post.status != 'pending':
        flash('Only pending posts can be reposted', 'warning')
        return redirect(url_for('history'))
    
    # Schedule the post for immediate reposting
    if schedule_post(post.id):
        flash('Post scheduled for reposting', 'success')
    else:
        flash('Failed to schedule post for reposting', 'danger')
    
    return redirect(url_for('history'))

@app.route('/post/<int:post_id>/cancel', methods=['POST'])
@login_required
def cancel_post(post_id):
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first_or_404()
    
    if post.status != 'pending':
        flash('Only pending posts can be canceled', 'warning')
        return redirect(url_for('history'))
    
    post.status = 'canceled'
    db.session.commit()
    
    flash('Post canceled successfully', 'success')
    return redirect(url_for('history'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    
    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)
        db.session.add(user_settings)
        db.session.commit()
    
    if request.method == 'POST':
        # Update user settings
        user_settings.auto_repost = 'auto_repost' in request.form
        user_settings.add_credit = 'add_credit' in request.form
        
        # Parse numeric values
        try:
            user_settings.repost_delay = int(request.form.get('repost_delay', 0))
            user_settings.check_interval = int(request.form.get('check_interval', 60))
            user_settings.post_limit_per_day = int(request.form.get('post_limit_per_day', 5))
        except ValueError:
            flash('Invalid numeric values provided', 'danger')
            return redirect(url_for('settings'))
        
        # Update credit text
        credit_text = request.form.get('credit_text', 'Reposted from @{source}')
        user_settings.credit_text = credit_text if credit_text else 'Reposted from @{source}'
        
        # Handle Instagram credentials if provided
        insta_username = request.form.get('instagram_username')
        insta_password = request.form.get('instagram_password')
        
        if insta_username:
            current_user.instagram_username = insta_username
        
        if insta_password:
            # In a production app, you'd want to securely store these credentials
            # or better yet, use OAuth for Instagram authentication
            current_user.instagram_password_hash = generate_password_hash(insta_password)
        
        db.session.commit()
        flash('Settings updated successfully', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', settings=user_settings)

@app.route('/api/fetch-now', methods=['POST'])
@login_required
def api_fetch_now():
    """Manually trigger post fetching from sources"""
    try:
        instagram_api = InstagramAPI(current_user.id)
        instagram_api.fetch_posts_from_sources(current_user.id)
        return jsonify({"success": True, "message": "Fetching posts from sources"})
    except Exception as e:
        logger.error(f"Error fetching posts: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('layout.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('layout.html', error="Server error occurred"), 500
