"""
Encryption utilities for secure data storage
"""

import base64
import os
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


class EncryptionManager:
    def __init__(self, key_file: str = "encryption.key"):
        self.key_file = key_file
        self.fernet = None
        self._load_or_generate_key()
        
    def _load_or_generate_key(self):
        """Load existing key or generate a new one"""
        try:
            if os.path.exists(self.key_file):
                # Load existing key
                with open(self.key_file, 'rb') as f:
                    key = f.read()
                logger.info("Loaded existing encryption key")
            else:
                # Generate new key
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                logger.info("Generated new encryption key")
                
            self.fernet = Fernet(key)
            
        except Exception as e:
            logger.error(f"Error with encryption key: {e}")
            raise
            
    def encrypt(self, data: str) -> str:
        """Encrypt a string"""
        if not self.fernet:
            raise Exception("Encryption not initialized")
            
        try:
            encrypted_data = self.fernet.encrypt(data.encode('utf-8'))
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise
            
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a string"""
        if not self.fernet:
            raise Exception("Encryption not initialized")
            
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise
            
    def encrypt_dict(self, data: dict) -> dict:
        """Encrypt sensitive fields in a dictionary"""
        encrypted_data = data.copy()
        
        # Fields to encrypt
        sensitive_fields = ['password', 'key_path']
        
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))
                
        return encrypted_data
        
    def decrypt_dict(self, data: dict) -> dict:
        """Decrypt sensitive fields in a dictionary"""
        decrypted_data = data.copy()
        
        # Fields to decrypt
        sensitive_fields = ['password', 'key_path']
        
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = self.decrypt(decrypted_data[field])
                except Exception as e:
                    logger.warning(f"Failed to decrypt {field}: {e}")
                    # Keep encrypted value if decryption fails
                    
        return decrypted_data


def generate_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    """Generate encryption key from password"""
    if salt is None:
        salt = os.urandom(16)
        
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt


def hash_password(password: str) -> str:
    """Hash a password for storage"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(password) == hashed 