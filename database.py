from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# Load environment variables
load_dotenv()

db = SQLAlchemy()

class Database:
    def __init__(self):
        self.db = db

    def init_app(self, app):
        db.init_app(app)
        with app.app_context():
            db.create_all()

    def get_session(self):
        return db.session

    def close(self):
        db.session.close()

    def save_conversation(self, user_message, bot_response, model_used, question_type, user_id=None):
        if user_id is None:
            print("Error: user_id is required")
            return False
            
        try:
            # Get or create chat history
            chat = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.created_at.desc()).first()
            if not chat:
                chat = ChatHistory(user_id=user_id)
                self.db.session.add(chat)
                self.db.session.commit()
            
            # Save message
            message = ChatMessage(
                chat_id=chat.id,
                user_message=user_message,
                bot_response=bot_response
            )
            self.db.session.add(message)
            self.db.session.commit()
            return True
        except Exception as e:
            self.db.session.rollback()
            print(f"Error saving conversation: {str(e)}")
            return False

# Models
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class ChatHistory(db.Model):
    __tablename__ = 'chat_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('chats', lazy=True))
    messages = db.relationship('ChatMessage', backref='chat', lazy=True)
    
    def __repr__(self):
        return f'<ChatHistory {self.id}>'

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat_history.id'), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ChatMessage {self.id}>'

# Database operations
def register_user(username, email, password):
    try:
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return user.id
    except Exception as e:
        db.session.rollback()
        return None

def verify_user(email, password):
    try:
        user = User.query.filter_by(email=email, password=password).first()
        return user.id if user else None
    except Exception as e:
        return None

def get_conversation_history(user_id):
    try:
        # Get all chat histories for the user, ordered by most recent first
        chats = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.created_at.desc()).all()
        
        # Format the chat histories
        history = []
        for chat in chats:
            # Get the most recent message for preview
            last_message = ChatMessage.query.filter_by(chat_id=chat.id).order_by(ChatMessage.created_at.desc()).first()
            if last_message:
                history.append({
                    'id': chat.id,
                    'user_message': last_message.user_message,
                    'bot_response': last_message.bot_response,
                    'timestamp': chat.created_at.strftime('%Y-%m-%d %H:%M'),
                    'message_count': ChatMessage.query.filter_by(chat_id=chat.id).count()
                })
        
        return history
    except Exception as e:
        print(f"Error getting conversation history: {str(e)}")
        return []

def init_app(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()