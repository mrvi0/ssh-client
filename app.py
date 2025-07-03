#!/usr/bin/env python3
"""
SSH Client - Self-hosted SSH connection manager
A simple but beautiful web interface for managing SSH connections
"""

import os
import json
import io
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import bcrypt
from cryptography.fernet import Fernet
import paramiko
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ssh_client.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Encryption key for sensitive data
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = Fernet.generate_key()
    cipher = Fernet(ENCRYPTION_KEY)
else:
    try:
        # Try to use the provided key
        cipher = Fernet(ENCRYPTION_KEY.encode())
    except:
        # If it fails, generate a new one
        ENCRYPTION_KEY = Fernet.generate_key()
        cipher = Fernet(ENCRYPTION_KEY)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    connections = db.relationship('Connection', backref='user', lazy=True)

class Connection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    host = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, default=22)
    username = db.Column(db.String(100), nullable=False)
    password_encrypted = db.Column(db.Text)
    private_key_encrypted = db.Column(db.Text)
    passphrase_encrypted = db.Column(db.Text)
    group = db.Column(db.String(100))
    tags = db.Column(db.String(255))
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Command(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    command = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    connection_id = db.Column(db.Integer, db.ForeignKey('connection.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Utility functions
def encrypt_data(data):
    """Encrypt sensitive data"""
    if data:
        return cipher.encrypt(data.encode()).decode()
    return None

def decrypt_data(encrypted_data):
    """Decrypt sensitive data"""
    if encrypted_data:
        return cipher.decrypt(encrypted_data.encode()).decode()
    return None

def generate_token(user_id):
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# SSH Connection Manager
class SSHManager:
    def __init__(self):
        self.connections = {}
    
    def connect(self, connection_id, host, port, username, password=None, private_key=None, passphrase=None):
        """Establish SSH connection"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if private_key:
                key = paramiko.RSAKey.from_private_key(
                    io.StringIO(decrypt_data(private_key)),
                    password=decrypt_data(passphrase) if passphrase else None
                )
                client.connect(host, port, username, pkey=key)
            else:
                client.connect(host, port, username, password=decrypt_data(password))
            
            self.connections[connection_id] = client
            return True, "Connected successfully"
        except Exception as e:
            return False, str(e)
    
    def execute_command(self, connection_id, command):
        """Execute command on SSH connection"""
        if connection_id not in self.connections:
            return False, "Connection not found"
        
        try:
            client = self.connections[connection_id]
            stdin, stdout, stderr = client.exec_command(command)
            
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            return True, {
                'output': output,
                'error': error,
                'exit_code': stdout.channel.recv_exit_status()
            }
        except Exception as e:
            return False, str(e)
    
    def disconnect(self, connection_id):
        """Close SSH connection"""
        if connection_id in self.connections:
            self.connections[connection_id].close()
            del self.connections[connection_id]

# Global SSH manager
ssh_manager = SSHManager()

# Routes
@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    """User registration"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    password_hash = generate_password_hash(data['password'])
    user = User(
        username=data['username'],
        password_hash=password_hash,
        email=data.get('email')
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = generate_token(user.id)
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    })

@app.route('/api/connections', methods=['GET'])
def get_connections():
    """Get user connections"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = verify_token(token)
    
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    
    connections = Connection.query.filter_by(user_id=user_id).all()
    result = []
    
    for conn in connections:
        result.append({
            'id': conn.id,
            'name': conn.name,
            'host': conn.host,
            'port': conn.port,
            'username': conn.username,
            'has_password': bool(conn.password_encrypted),
            'has_private_key': bool(conn.private_key_encrypted),
            'group': conn.group,
            'tags': conn.tags,
            'notes': conn.notes,
            'created_at': conn.created_at.isoformat()
        })
    
    return jsonify(result)

@app.route('/api/connections', methods=['POST'])
def create_connection():
    """Create new connection"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = verify_token(token)
    
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('host') or not data.get('username'):
        return jsonify({'error': 'Name, host, and username required'}), 400
    
    connection = Connection(
        name=data['name'],
        host=data['host'],
        port=data.get('port', 22),
        username=data['username'],
        password_encrypted=encrypt_data(data.get('password')),
        private_key_encrypted=encrypt_data(data.get('private_key')),
        passphrase_encrypted=encrypt_data(data.get('passphrase')),
        group=data.get('group'),
        tags=data.get('tags'),
        notes=data.get('notes'),
        user_id=user_id
    )
    
    db.session.add(connection)
    db.session.commit()
    
    return jsonify({
        'id': connection.id,
        'name': connection.name,
        'host': connection.host,
        'port': connection.port,
        'username': connection.username,
        'group': connection.group,
        'tags': connection.tags,
        'notes': connection.notes,
        'created_at': connection.created_at.isoformat()
    }), 201

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('ssh_connect')
def handle_ssh_connect(data):
    """Handle SSH connection request"""
    try:
        connection_id = data.get('connection_id')
        connection = Connection.query.get(connection_id)
        
        if not connection:
            emit('ssh_error', {'message': 'Connection not found'})
            return
        
        success, message = ssh_manager.connect(
            connection_id,
            connection.host,
            connection.port,
            connection.username,
            connection.password_encrypted,
            connection.private_key_encrypted,
            connection.passphrase_encrypted
        )
        
        if success:
            emit('ssh_connected', {'connection_id': connection_id, 'message': message})
        else:
            emit('ssh_error', {'message': message})
    
    except Exception as e:
        emit('ssh_error', {'message': str(e)})

@socketio.on('ssh_command')
def handle_ssh_command(data):
    """Handle SSH command execution"""
    try:
        connection_id = data.get('connection_id')
        command = data.get('command')
        
        success, result = ssh_manager.execute_command(connection_id, command)
        
        if success:
            emit('ssh_output', {
                'connection_id': connection_id,
                'output': result['output'],
                'error': result['error'],
                'exit_code': result['exit_code']
            })
        else:
            emit('ssh_error', {'message': result})
    
    except Exception as e:
        emit('ssh_error', {'message': str(e)})

@socketio.on('ssh_disconnect')
def handle_ssh_disconnect(data):
    """Handle SSH disconnection"""
    try:
        connection_id = data.get('connection_id')
        ssh_manager.disconnect(connection_id)
        emit('ssh_disconnected', {'connection_id': connection_id})
    except Exception as e:
        emit('ssh_error', {'message': str(e)})

if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Run the application
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 