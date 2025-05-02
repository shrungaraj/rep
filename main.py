import logging
from app import app
from routes import *

# Initialize logging
logging.basicConfig(level=logging.INFO)

# For local development
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
