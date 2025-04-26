from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_socketio import SocketIO, emit
from iot_chatbot import IoTChatbot
import os
from dotenv import load_dotenv
import socket
import logging
from database import (
    db, Database, User, ChatHistory, ChatMessage,
    get_conversation_history
)
from datetime import timedelta, datetime
from flask_login import login_required, current_user, LoginManager, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Initialize database
database = Database()
database.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

chatbot = IoTChatbot()

@app.route('/')
def index():
    user_id = session.get('user')
    email = session.get('email')
    username = session.get('username')
    
    if user_id:
        chat_history = get_conversation_history(user_id)
        return render_template('index.html', 
                             user=user_id, 
                             email=email, 
                             username=username,
                             chat_history=chat_history)
    return render_template('index.html', 
                         user=None, 
                         email=None, 
                         username=None,
                         chat_history=None)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please fill in all fields', 'error')
            return render_template('login.html')
            
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['user'] = user.id
            session['email'] = user.email
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not username or not email or not password:
            flash('Please fill in all fields', 'error')
            return render_template('register.html')
            
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
            
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'error')
            return render_template('register.html')
            
        try:
            new_user = User(username=username, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            
            session['user'] = new_user.id
            session['email'] = new_user.email
            session['username'] = new_user.username
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration', 'error')
            return render_template('register.html')
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@socketio.on('send_message')
def handle_message(data):
    try:
        user_id = session.get('user')
        message = data.get('message')
        chat_id = data.get('chat_id')
        is_new_chat = data.get('is_new_chat', False)
        
        # Get response from chatbot
        response = chatbot.get_response(message)
        
        if user_id:
            # Save chat history only for logged-in users
            if is_new_chat:
                chat = ChatHistory(user_id=user_id)
                db.session.add(chat)
                db.session.commit()
                chat_id = chat.id
            elif not chat_id:
                chat = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.created_at.desc()).first()
                if not chat:
                    chat = ChatHistory(user_id=user_id)
                    db.session.add(chat)
                    db.session.commit()
                chat_id = chat.id
            
            # Save message to database
            chat_message = ChatMessage(
                chat_id=chat_id,
                user_message=message,
                bot_response=response
            )
            db.session.add(chat_message)
            db.session.commit()
        
        emit('receive_message', {
            'message': response,
            'chat_id': chat_id
        })
        
    except Exception as e:
        print(f"Error handling message: {str(e)}")
        emit('receive_message', {'message': 'Error processing message'})

@socketio.on('load_chat')
def handle_load_chat(data):
    try:
        chat_id = data.get('chat_id')
        user_id = session.get('user')
        
        if not chat_id or not user_id:
            return
        
        # Get specific chat from database
        chat = ChatHistory.query.filter_by(id=chat_id, user_id=user_id).first()
        if chat:
            messages = ChatMessage.query.filter_by(chat_id=chat_id).order_by(ChatMessage.created_at.asc()).all()
            emit('chat_loaded', {
                'messages': [{
                    'user_message': msg.user_message,
                    'bot_response': msg.bot_response,
                    'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
                } for msg in messages]
            })
    except Exception as e:
        logger.error(f"Error loading chat: {str(e)}")
        emit('chat_loaded', {
            'error': 'Error loading chat'
        })

@app.route('/get_chat_history')
def get_chat_history():
    try:
        chat_id = request.args.get('chat_id')
        user_id = session.get('user')
        
        if not user_id:
            return jsonify({'error': 'Not logged in'}), 401
            
        chat = ChatHistory.query.filter_by(id=chat_id, user_id=user_id).first()
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
            
        messages = ChatMessage.query.filter_by(chat_id=chat_id).order_by(ChatMessage.created_at.asc()).all()
        
        return jsonify({
            'messages': [{
                'user_message': msg.user_message,
                'bot_response': msg.bot_response,
                'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            } for msg in messages]
        })
        
    except Exception as e:
        print(f"Error getting chat history: {str(e)}")
        return jsonify({'error': 'Error getting chat history'}), 500

@app.route('/new_chat', methods=['POST'])
@login_required
def new_chat():
    try:
        # Create new chat history
        chat = ChatHistory(user_id=current_user.id)
        db.session.add(chat)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@socketio.on('new_chat')
def handle_new_chat():
    try:
        user_id = session.get('user')
        if user_id:
            # Create new chat history
            chat = ChatHistory(user_id=user_id)
            db.session.add(chat)
            db.session.commit()
            emit('chat_created', {'chat_id': chat.id})
    except Exception as e:
        logger.error(f"Error creating new chat: {str(e)}")
        emit('chat_created', {'error': 'Error creating new chat'})

def find_available_port(start_port=5000, max_port=6000):
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError("No available ports found")

@app.route('/settings')
def settings():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session.get('user')
    user = User.query.get(user_id)
    
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    return render_template('settings.html', user=user, email=user.email, username=user.username)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    try:
        user_id = session.get('user')
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401

        data = request.get_json()
        new_username = data.get('username')
        
        if not new_username:
            return jsonify({'error': 'Username is required'}), 400

        # Check if username already exists
        existing_user = User.query.filter(User.username == new_username, User.id != user_id).first()
        if existing_user:
            return jsonify({'error': 'Username already taken'}), 400

        # Update username
        user = User.query.get(user_id)
        if user:
            user.username = new_username
            db.session.commit()
            session['username'] = new_username
            return jsonify({'message': 'Profile updated successfully'})
        
        return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        return jsonify({'error': 'Error updating profile'}), 500

@app.route('/reset_password', methods=['POST'])
@login_required
def reset_password():
    try:
        user_id = session.get('user')
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401

        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if not all([current_password, new_password, confirm_password]):
            return jsonify({'error': 'All fields are required'}), 400

        if new_password != confirm_password:
            return jsonify({'error': 'New passwords do not match'}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400

        user.set_password(new_password)
        db.session.commit()
        return jsonify({'message': 'Password updated successfully'})
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        return jsonify({'error': 'Error resetting password'}), 500

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    try:
        user_id = session.get('user')
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401

        data = request.get_json()
        password = data.get('password')
        if not password:
            return jsonify({'error': 'Password is required'}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if not user.check_password(password):
            return jsonify({'error': 'Incorrect password'}), 400

        # Delete user's chat history and messages
        ChatMessage.query.filter(ChatMessage.chat_id.in_(
            db.session.query(ChatHistory.id).filter_by(user_id=user_id)
        )).delete()
        ChatHistory.query.filter_by(user_id=user_id).delete()
        
        # Delete user
        db.session.delete(user)
        db.session.commit()
        
        # Clear session
        session.clear()
        return jsonify({'message': 'Account deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting account: {str(e)}")
        return jsonify({'error': 'Error deleting account'}), 500

if __name__ == '__main__':
    # Check if running in production (cPanel)
    if os.environ.get('FLASK_ENV') == 'production':
        # Production settings
        port = int(os.environ.get('PORT', 5000))
        socketio.run(
            app,
            host='0.0.0.0',
            port=port,
            debug=False,
            allow_unsafe_werkzeug=True
        )
    else:
        # Development settings
        port = find_available_port()
        print(f"Starting server on port {port}")
        print(f"Open http://localhost:{port} in your browser")
        socketio.run(
            app,
            host='0.0.0.0',
            port=port,
            debug=True
        ) 