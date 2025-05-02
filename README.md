# Instagram Repost Bot

A Flask web application that automatically fetches and reposts content from specified Instagram sources (accounts and hashtags).

## Features

- User authentication system
- Dashboard with post and source statistics
- Source management (Instagram accounts and hashtags)
- Post history with filtering options
- Customizable repost settings
- Automatic post scheduling and publishing

## Technologies Used

- **Backend**: Flask, Flask-SQLAlchemy, Flask-Login
- **Database**: PostgreSQL
- **Scheduler**: APScheduler
- **Frontend**: Bootstrap, Feather Icons
- **API**: Instagram Graph API (simulated)

## Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL database

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/instagram-repost-bot.git
   cd instagram-repost-bot
   ```

2. Install dependencies:
   ```
   pip install -r requirements-github.txt
   ```

3. Set up environment variables:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/dbname
   SESSION_SECRET=your_secure_secret_key
   ```

4. Initialize the database:
   ```
   flask shell
   >>> from app import db
   >>> db.create_all()
   >>> exit()
   ```

5. Run the application:
   ```
   python main.py
   ```

## Deployment

The application can be deployed to various platforms:

- Heroku: Use the included Procfile
- PythonAnywhere
- AWS, GCP, or Azure

Make sure to set up the required environment variables on your hosting platform.

## License

MIT

## Disclaimer

This application is for educational purposes only. Always respect Instagram's terms of service and respect copyright when reposting content.