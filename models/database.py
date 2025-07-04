import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# Import utilities
from utils.encryption import EncryptionManager
from utils.config import app_paths

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = str(app_paths.get_database_path())
        self.db_path = db_path
        self.encryption_manager = EncryptionManager(str(app_paths.get_key_path()))
        self.init_database()
    
    def encrypt(self, data: str) -> Optional[str]:
        """Encrypt data"""
        if data:
            return self.encryption_manager.encrypt(data)
        return None
    
    def decrypt(self, encrypted_data: str) -> Optional[str]:
        """Decrypt data"""
        if encrypted_data:
            return self.encryption_manager.decrypt(encrypted_data)
        return None
    
    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица подключений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER DEFAULT 22,
                username TEXT NOT NULL,
                password_encrypted TEXT,
                private_key_encrypted TEXT,
                passphrase_encrypted TEXT,
                group_name TEXT,
                tags TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица команд
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                command TEXT NOT NULL,
                category TEXT,
                description TEXT,
                arguments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица пользователей (для синхронизации)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                email TEXT,
                sync_enabled BOOLEAN DEFAULT FALSE,
                last_sync TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица групп
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                members TEXT,  -- JSON array of member emails
                connections TEXT,  -- JSON array of connection IDs
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_connection(self, name: str, host: str, port: int = 22, username: Optional[str] = None, 
                      password: Optional[str] = None, key_path: Optional[str] = None, description: Optional[str] = None) -> int:
        """Add a new connection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO connections (name, host, port, username, password_encrypted, 
                                   private_key_encrypted, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            name, host, port, username,
            self.encrypt(password) if password else None,
            self.encrypt(key_path) if key_path else None,
            description
        ))
        
        connection_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Added connection: {name}")
        return connection_id if connection_id is not None else 0
    
    def get_all_connections(self) -> List[Dict[str, Any]]:
        """Get all connections"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM connections ORDER BY name')
        rows = cursor.fetchall()
        
        connections = []
        for row in rows:
            connections.append({
                'id': row[0],
                'name': row[1],
                'host': row[2],
                'port': row[3],
                'username': row[4],
                'password': self.decrypt(row[5]) if row[5] else None,
                'key_path': self.decrypt(row[6]) if row[6] else None,
                'description': row[7],
                'created_at': row[8],
                'updated_at': row[9]
            })
        
        conn.close()
        return connections
    
    def get_connection(self, connection_id: int) -> Optional[Dict[str, Any]]:
        """Get connection by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM connections WHERE id = ?', (connection_id,))
        row = cursor.fetchone()
        
        if row:
            connection = {
                'id': row[0],
                'name': row[1],
                'host': row[2],
                'port': row[3],
                'username': row[4],
                'password': self.decrypt(row[5]) if row[5] else None,
                'key_path': self.decrypt(row[6]) if row[6] else None,
                'description': row[7],
                'created_at': row[8],
                'updated_at': row[9]
            }
        else:
            connection = None
        
        conn.close()
        return connection
    
    def add_command(self, name: str, command: str, category: Optional[str] = None, 
                   description: Optional[str] = None, arguments: Optional[str] = None) -> int:
        """Add a new command"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO commands (name, command, category, description, arguments)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, command, category, description, arguments))
        
        command_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Added command: {name}")
        return command_id if command_id is not None else 0
    
    def get_all_commands(self) -> List[Dict[str, Any]]:
        """Get all commands"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM commands ORDER BY name')
        rows = cursor.fetchall()
        
        commands = []
        for row in rows:
            commands.append({
                'id': row[0],
                'name': row[1],
                'command': row[2],
                'category': row[3],
                'description': row[4],
                'arguments': row[5],
                'created_at': row[6]
            })
        
        conn.close()
        return commands
    
    def get_command(self, command_id: int) -> Optional[Dict[str, Any]]:
        """Get command by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM commands WHERE id = ?', (command_id,))
        row = cursor.fetchone()
        
        if row:
            command = {
                'id': row[0],
                'name': row[1],
                'command': row[2],
                'category': row[3],
                'description': row[4],
                'arguments': row[5],
                'created_at': row[6]
            }
        else:
            command = None
        
        conn.close()
        return command
    
    def update_command(self, command_id: int, **kwargs) -> bool:
        """Update command"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Prepare update fields
        update_fields = []
        values = []
        
        if 'name' in kwargs:
            update_fields.append('name = ?')
            values.append(kwargs['name'])
        
        if 'command' in kwargs:
            update_fields.append('command = ?')
            values.append(kwargs['command'])
        
        if 'category' in kwargs:
            update_fields.append('category = ?')
            values.append(kwargs['category'])
        
        if 'description' in kwargs:
            update_fields.append('description = ?')
            values.append(kwargs['description'])
        
        if 'arguments' in kwargs:
            update_fields.append('arguments = ?')
            values.append(kwargs['arguments'])
        
        values.append(command_id)
        
        if update_fields:
            query = f"UPDATE commands SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
            success = True
        else:
            success = False
        
        conn.close()
        return success
    
    def delete_command(self, command_id: int) -> bool:
        """Delete command"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM commands WHERE id = ?', (command_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted command ID: {command_id}")
        return True
    
    def update_connection(self, connection_id: int, **kwargs) -> bool:
        """Update connection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Prepare update fields
        update_fields = []
        values = []
        
        if 'name' in kwargs:
            update_fields.append('name = ?')
            values.append(kwargs['name'])
        
        if 'host' in kwargs:
            update_fields.append('host = ?')
            values.append(kwargs['host'])
        
        if 'port' in kwargs:
            update_fields.append('port = ?')
            values.append(kwargs['port'])
        
        if 'username' in kwargs:
            update_fields.append('username = ?')
            values.append(kwargs['username'])
        
        if 'password' in kwargs:
            update_fields.append('password_encrypted = ?')
            values.append(self.encrypt(kwargs['password']) if kwargs['password'] else None)
        
        if 'key_path' in kwargs:
            update_fields.append('private_key_encrypted = ?')
            values.append(self.encrypt(kwargs['key_path']) if kwargs['key_path'] else None)
        
        if 'description' in kwargs:
            update_fields.append('notes = ?')
            values.append(kwargs['description'])
        
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        values.append(connection_id)
        
        if update_fields:
            query = f"UPDATE connections SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
            success = True
        else:
            success = False
        
        conn.close()
        return success
    
    def delete_connection(self, connection_id: int) -> bool:
        """Delete connection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM connections WHERE id = ?', (connection_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted connection ID: {connection_id}")
        return True
    
    def add_group(self, group_data: Dict[str, Any]) -> int:
        """Add a new group"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert lists to JSON strings
        members_json = json.dumps(group_data.get('members', []))
        connections_json = json.dumps(group_data.get('connections', []))
        
        cursor.execute('''
            INSERT INTO groups (name, description, members, connections)
            VALUES (?, ?, ?, ?)
        ''', (
            group_data['name'],
            group_data.get('description', ''),
            members_json,
            connections_json
        ))
        
        conn.commit()
        group_id = cursor.lastrowid
        logger.info(f"Added group: {group_data['name']}")
        return group_id
    
    def get_group(self, group_id: int) -> Optional[Dict[str, Any]]:
        """Get a group by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM groups WHERE id = ?', (group_id,))
        row = cursor.fetchone()
        
        if row:
            group = {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'members': json.loads(row[3]) if row[3] else [],
                'connections': json.loads(row[4]) if row[4] else [],
                'created_at': row[5],
                'updated_at': row[6]
            }
        else:
            group = None
        
        conn.close()
        return group
    
    def get_all_groups(self) -> List[Dict[str, Any]]:
        """Get all groups"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM groups ORDER BY name')
        rows = cursor.fetchall()
        
        groups = []
        for row in rows:
            groups.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'members': json.loads(row[3]) if row[3] else [],
                'connections': json.loads(row[4]) if row[4] else [],
                'created_at': row[5],
                'updated_at': row[6]
            })
        
        conn.close()
        return groups
    
    def update_group(self, group_id: int, group_data: Dict[str, Any]):
        """Update a group"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert lists to JSON strings
        members_json = json.dumps(group_data.get('members', []))
        connections_json = json.dumps(group_data.get('connections', []))
        
        cursor.execute('''
            UPDATE groups 
            SET name = ?, description = ?, members = ?, connections = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            group_data['name'],
            group_data.get('description', ''),
            members_json,
            connections_json,
            group_id
        ))
        
        conn.commit()
        logger.info(f"Updated group: {group_data['name']}")
        
        conn.close()
    
    def delete_group(self, group_id: int):
        """Delete a group"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM groups WHERE id = ?', (group_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted group: {group_id}")
    
    def add_user(self, user_data: Dict[str, Any]) -> int:
        """Add a new user (for web app)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, is_admin)
            VALUES (?, ?, ?, ?)
        ''', (
            user_data['username'],
            user_data['email'],
            user_data['password_hash'],
            user_data.get('is_admin', False)
        ))
        
        conn.commit()
        user_id = cursor.lastrowid
        logger.info(f"Added user: {user_data['username']}")
        return user_id
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get a user by username"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        
        if row:
            user = {
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'password_hash': row[3],
                'is_admin': bool(row[4]),
                'created_at': row[5],
                'updated_at': row[6]
            }
        else:
            user = None
        
        conn.close()
        return user
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get a user by email"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        
        if row:
            user = {
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'password_hash': row[3],
                'is_admin': bool(row[4]),
                'created_at': row[5],
                'updated_at': row[6]
            }
        else:
            user = None
        
        conn.close()
        return user
    
    def close(self):
        """Close database connection"""
        # SQLite connections are closed automatically, but we can add cleanup here
        logger.info("Database manager closed") 