import sqlite3
import os
import json
from datetime import datetime
from cryptography.fernet import Fernet
import base64

class Database:
    def __init__(self, db_path="ssh_client.db"):
        self.db_path = db_path
        self.cipher = None
        self.init_encryption()
        self.init_database()
    
    def init_encryption(self):
        """Инициализация шифрования"""
        key_file = "encryption.key"
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
        
        self.cipher = Fernet(key)
    
    def encrypt(self, data):
        """Шифрование данных"""
        if data:
            return self.cipher.encrypt(data.encode()).decode()
        return None
    
    def decrypt(self, encrypted_data):
        """Расшифровка данных"""
        if encrypted_data:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
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
                connection_id INTEGER,
                name TEXT NOT NULL,
                command TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (connection_id) REFERENCES connections (id) ON DELETE CASCADE
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
        
        conn.commit()
        conn.close()
    
    def add_connection(self, name, host, port, username, password=None, 
                      private_key=None, passphrase=None, group=None, tags=None, notes=None):
        """Добавление нового подключения"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO connections (name, host, port, username, password_encrypted, 
                                   private_key_encrypted, passphrase_encrypted, group_name, tags, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name, host, port, username,
            self.encrypt(password),
            self.encrypt(private_key),
            self.encrypt(passphrase),
            group,
            json.dumps(tags) if tags else None,
            notes
        ))
        
        connection_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return connection_id
    
    def get_connections(self):
        """Получение всех подключений"""
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
                'has_password': bool(row[5]),
                'has_private_key': bool(row[6]),
                'group': row[8],
                'tags': json.loads(row[9]) if row[9] else [],
                'notes': row[10],
                'created_at': row[11]
            })
        
        conn.close()
        return connections
    
    def get_connection(self, connection_id):
        """Получение подключения по ID"""
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
                'password': self.decrypt(row[5]),
                'private_key': self.decrypt(row[6]),
                'passphrase': self.decrypt(row[7]),
                'group': row[8],
                'tags': json.loads(row[9]) if row[9] else [],
                'notes': row[10]
            }
        else:
            connection = None
        
        conn.close()
        return connection
    
    def update_connection(self, connection_id, **kwargs):
        """Обновление подключения"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Подготавливаем данные для обновления
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
            values.append(self.encrypt(kwargs['password']))
        
        if 'private_key' in kwargs:
            update_fields.append('private_key_encrypted = ?')
            values.append(self.encrypt(kwargs['private_key']))
        
        if 'passphrase' in kwargs:
            update_fields.append('passphrase_encrypted = ?')
            values.append(self.encrypt(kwargs['passphrase']))
        
        if 'group' in kwargs:
            update_fields.append('group_name = ?')
            values.append(kwargs['group'])
        
        if 'tags' in kwargs:
            update_fields.append('tags = ?')
            values.append(json.dumps(kwargs['tags']))
        
        if 'notes' in kwargs:
            update_fields.append('notes = ?')
            values.append(kwargs['notes'])
        
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        values.append(connection_id)
        
        if update_fields:
            query = f"UPDATE connections SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
        
        conn.close()
    
    def delete_connection(self, connection_id):
        """Удаление подключения"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM connections WHERE id = ?', (connection_id,))
        conn.commit()
        conn.close()
    
    def add_command(self, connection_id, name, command, description=None):
        """Добавление команды"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO commands (connection_id, name, command, description)
            VALUES (?, ?, ?, ?)
        ''', (connection_id, name, command, description))
        
        command_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return command_id
    
    def get_commands(self, connection_id=None):
        """Получение команд"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if connection_id:
            cursor.execute('SELECT * FROM commands WHERE connection_id = ? ORDER BY name', (connection_id,))
        else:
            cursor.execute('SELECT * FROM commands ORDER BY name')
        
        rows = cursor.fetchall()
        
        commands = []
        for row in rows:
            commands.append({
                'id': row[0],
                'connection_id': row[1],
                'name': row[2],
                'command': row[3],
                'description': row[4],
                'created_at': row[5]
            })
        
        conn.close()
        return commands
    
    def delete_command(self, command_id):
        """Удаление команды"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM commands WHERE id = ?', (command_id,))
        conn.commit()
        conn.close() 