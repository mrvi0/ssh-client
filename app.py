#!/usr/bin/env python3
"""
SSH Client Web Application
Provides web interface for user registration and command management
"""

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_socketio import SocketIO, emit, disconnect
from flask_cors import CORS
import jwt
import bcrypt
import logging
from datetime import datetime, timedelta
import os
from pathlib import Path
from functools import wraps

# Add project root to path
project_root = Path(__file__).parent
import sys
sys.path.insert(0, str(project_root))

from models.database import DatabaseManager
from utils.encryption import EncryptionManager
from config import *

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY

# Initialize extensions
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

# Initialize database and encryption
db_manager = DatabaseManager()
encryption = EncryptionManager()

# Ensure instance directory exists
instance_dir = Path("instance")
instance_dir.mkdir(exist_ok=True)

def create_admin_user():
    """Create admin user if it doesn't exist"""
    if not ADMIN_ENABLED:
        return
        
    try:
        # Check if admin user exists
        admin_user = db_manager.get_user_by_username(ADMIN_USERNAME)
        if not admin_user:
            # Create admin user
            password_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt())
            admin_data = {
                'username': ADMIN_USERNAME,
                'email': ADMIN_EMAIL,
                'password_hash': password_hash.decode('utf-8'),
                'is_admin': True
            }
            db_manager.add_user(admin_data)
            logger.info(f"Created admin user: {ADMIN_USERNAME}")
        else:
            logger.info(f"Admin user already exists: {ADMIN_USERNAME}")
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")

def generate_token(user_id: int, username: str, is_admin: bool = False):
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'is_admin': is_admin,
        'exp': datetime.utcnow() + timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRES)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def auth_decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
            
        token = token.split(' ')[1]
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
            
        request.user = payload
        return f(*args, **kwargs)
    return auth_decorated_function

def require_admin(f):
    """Decorator to require admin access"""
    @wraps(f)
    def admin_decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
            
        token = token.split(' ')[1]
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
            
        if not payload.get('is_admin'):
            return jsonify({'error': 'Admin access required'}), 403
            
        request.user = payload
        return f(*args, **kwargs)
    return admin_decorated_function

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({'error': 'All fields are required'}), 400
            
        # Check if user already exists
        if db_manager.get_user_by_username(username):
            return jsonify({'error': 'Username already exists'}), 409
            
        if db_manager.get_user_by_email(email):
            return jsonify({'error': 'Email already exists'}), 409
            
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user
        user_data = {
            'username': username,
            'email': email,
            'password_hash': password_hash.decode('utf-8'),
            'is_admin': False
        }
        
        user_id = db_manager.add_user(user_data)
        
        # Generate token
        token = generate_token(user_id, username, False)
        
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user': {
                'id': user_id,
                'username': username,
                'email': email,
                'is_admin': False
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not all([username, password]):
            return jsonify({'error': 'Username and password are required'}), 400
            
        # Get user
        user = db_manager.get_user_by_username(username)
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
            
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({'error': 'Invalid credentials'}), 401
            
        # Generate token
        token = generate_token(user['id'], user['username'], user['is_admin'])
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'is_admin': user['is_admin']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/verify', methods=['GET'])
@require_auth
def verify():
    """Verify token endpoint"""
    return jsonify({
        'valid': True,
        'user': request.user
    }), 200

@app.route('/api/connections', methods=['GET'])
@require_auth
def get_connections():
    """Get user's connections"""
    try:
        connections = db_manager.get_all_connections()
        return jsonify(connections), 200
    except Exception as e:
        logger.error(f"Error getting connections: {e}")
        return jsonify({'error': 'Failed to get connections'}), 500

@app.route('/api/connections', methods=['POST'])
@require_auth
def create_connection():
    """Create a new connection"""
    try:
        data = request.get_json()
        connection_id = db_manager.add_connection(data)
        return jsonify({'id': connection_id, 'message': 'Connection created'}), 201
    except Exception as e:
        logger.error(f"Error creating connection: {e}")
        return jsonify({'error': 'Failed to create connection'}), 500

@app.route('/api/connections/<int:connection_id>', methods=['PUT'])
@require_auth
def update_connection(connection_id):
    """Update a connection"""
    try:
        data = request.get_json()
        db_manager.update_connection(connection_id, data)
        return jsonify({'message': 'Connection updated'}), 200
    except Exception as e:
        logger.error(f"Error updating connection: {e}")
        return jsonify({'error': 'Failed to update connection'}), 500

@app.route('/api/connections/<int:connection_id>', methods=['DELETE'])
@require_auth
def delete_connection(connection_id):
    """Delete a connection"""
    try:
        db_manager.delete_connection(connection_id)
        return jsonify({'message': 'Connection deleted'}), 200
    except Exception as e:
        logger.error(f"Error deleting connection: {e}")
        return jsonify({'error': 'Failed to delete connection'}), 500

@app.route('/api/commands', methods=['GET'])
@require_auth
def get_commands():
    """Get command snippets"""
    try:
        commands = db_manager.get_all_commands()
        return jsonify(commands), 200
    except Exception as e:
        logger.error(f"Error getting commands: {e}")
        return jsonify({'error': 'Failed to get commands'}), 500

@app.route('/api/commands', methods=['POST'])
@require_auth
def create_command():
    """Create a new command snippet"""
    try:
        data = request.get_json()
        command_id = db_manager.add_command(data)
        return jsonify({'id': command_id, 'message': 'Command created'}), 201
    except Exception as e:
        logger.error(f"Error creating command: {e}")
        return jsonify({'error': 'Failed to create command'}), 500

@app.route('/api/groups', methods=['GET'])
@require_auth
def get_groups():
    """Get user groups"""
    try:
        groups = db_manager.get_all_groups()
        return jsonify(groups), 200
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        return jsonify({'error': 'Failed to get groups'}), 500

@app.route('/api/groups', methods=['POST'])
@require_admin
def create_group():
    """Create a new group (admin only)"""
    try:
        data = request.get_json()
        group_id = db_manager.add_group(data)
        return jsonify({'id': group_id, 'message': 'Group created'}), 201
    except Exception as e:
        logger.error(f"Error creating group: {e}")
        return jsonify({'error': 'Failed to create group'}), 500

@app.route('/api/users', methods=['GET'])
@require_admin
def get_users():
    """Get all users (admin only)"""
    try:
        # This would need to be implemented in DatabaseManager
        return jsonify({'message': 'Not implemented yet'}), 501
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({'error': 'Failed to get users'}), 500

@app.route('/api/admin/stats', methods=['GET'])
@require_admin
def admin_stats():
    """Get admin statistics"""
    try:
        connections = db_manager.get_all_connections()
        commands = db_manager.get_all_commands()
        groups = db_manager.get_all_groups()
        
        stats = {
            'connections_count': len(connections),
            'commands_count': len(commands),
            'groups_count': len(groups),
            'total_users': 1  # Would need to implement user counting
        }
        
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('message')
def handle_message(data):
    """Handle WebSocket message"""
    logger.info(f"Received message: {data}")
    emit('response', {'message': 'Message received'})

if __name__ == '__main__':
    # Create admin user on startup
    create_admin_user()
    
    # Start the application
    logger.info(f"Starting web server on {WEB_HOST}:{WEB_PORT}")
    socketio.run(
        app,
        host=WEB_HOST,
        port=WEB_PORT,
        debug=WEB_DEBUG
    ) 