# GitHub Deployment Guide

This guide explains how to deploy your Instagram Repost Bot application to GitHub and how to set up hosting platforms.

## 1. Push to GitHub

### Initialize Git Repository

If you haven't initialized a Git repository yet:

```bash
git init
```

### Add Your Files

```bash
git add .
```

### Commit Your Changes

```bash
git commit -m "Initial commit"
```

### Create GitHub Repository

1. Go to [GitHub](https://github.com/) and sign in
2. Click on the "+" icon in the top right corner and select "New repository"
3. Name your repository (e.g., "instagram-repost-bot")
4. Choose whether it should be public or private
5. Do not initialize with README, .gitignore, or license as we already have those
6. Click "Create repository"

### Link and Push to GitHub

```bash
git remote add origin https://github.com/yourusername/instagram-repost-bot.git
git branch -M main
git push -u origin main
```

## 2. Deployment Options

### Option 1: Heroku

1. Create a Heroku account at [heroku.com](https://heroku.com)
2. Install the Heroku CLI: [instructions](https://devcenter.heroku.com/articles/heroku-cli)
3. Login to Heroku:
   ```bash
   heroku login
   ```
4. Create a new Heroku app:
   ```bash
   heroku create your-app-name
   ```
5. Add PostgreSQL addon:
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```
6. Set environment variables:
   ```bash
   heroku config:set SESSION_SECRET=your_secure_secret_key
   ```
7. Push to Heroku:
   ```bash
   git push heroku main
   ```
8. Initialize the database:
   ```bash
   heroku run python -c "from app import db; db.create_all()"
   ```

### Option 2: PythonAnywhere

1. Sign up for a PythonAnywhere account
2. Create a new web app with Flask
3. Clone your GitHub repository
4. Set up a virtual environment and install requirements
5. Configure the WSGI file to point to your Flask app
6. Set up PostgreSQL database
7. Configure environment variables

### Option 3: GitHub Actions with Cloud Providers

You can set up GitHub Actions to automatically deploy to:
- AWS Elastic Beanstalk
- Google Cloud Run
- Azure App Service

## 3. Setting Up GitHub Actions (CI/CD)

Create a GitHub Actions workflow file at `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        if [ -f requirements-github.txt ]; then pip install -r requirements-github.txt; fi
    
    - name: Run tests
      run: |
        pytest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    # Add deployment steps for your preferred hosting platform
    # Example for Heroku:
    - name: Deploy to Heroku
      uses: akhileshns/heroku-deploy@v3.12.12
      with:
        heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
        heroku_app_name: ${{ secrets.HEROKU_APP_NAME }}
        heroku_email: ${{ secrets.HEROKU_EMAIL }}
```

Remember to set up the appropriate secrets in your GitHub repository settings.

## 4. Database Management

For production environments, make sure to:

1. Use a secure database connection
2. Set up database migrations (you can use Flask-Migrate)
3. Create regular database backups
4. Monitor database performance

## 5. Environment Variables

Key environment variables for your application:

- `DATABASE_URL`: PostgreSQL connection string
- `SESSION_SECRET`: Secret key for Flask sessions
- `INSTAGRAM_API_KEY`: If using the real Instagram API
- `FLASK_ENV`: Set to 'production' for deployment