from flask import Flask
from database import db, Database
import os
from dotenv import load_dotenv
from sqlalchemy import text

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
database = Database()
database.init_app(app)

def migrate():
    with app.app_context():
        try:
            # Add is_active column to user table
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE user ADD COLUMN is_active BOOLEAN DEFAULT TRUE'))
                conn.commit()
            print("Migration completed successfully!")
        except Exception as e:
            print(f"Error during migration: {str(e)}")

if __name__ == '__main__':
    migrate() 