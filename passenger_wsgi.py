import sys
import os

# Add your project directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import your Flask application
from app import app as application

# Set environment variables
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_APP'] = 'app.py' 