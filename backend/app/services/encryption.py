"""
Encryption service for sensitive data
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from typing import Union

from app.config import settings

class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self):
        self.key = self._derive_key(settings.DATABASE_ENCRYPTION_KEY)
        self.cipher = Fernet(self.key)
    
    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password"""
        password_bytes = password.encode()
        salt = b'sipcall_salt_2025'  # In production, use random salt per installation
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return key
    
    def encrypt(self, data: str) -> bytes:
        """Encrypt string data"""
        if not data:
            return b''
        return self.cipher.encrypt(data.encode())
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt data back to string"""
        if not encrypted_data:
            return ''
        return self.cipher.decrypt(encrypted_data).decode()
    
    def encrypt_phone_number(self, phone_number: str) -> bytes:
        """Encrypt phone number with validation"""
        # Basic phone number validation
        cleaned = ''.join(filter(str.isdigit, phone_number.replace('+', '')))
        if len(cleaned) < 7 or len(cleaned) > 15:
            raise ValueError("Invalid phone number format")
        return self.encrypt(phone_number)
    
    def decrypt_phone_number(self, encrypted_data: bytes) -> str:
        """Decrypt phone number"""
        return self.decrypt(encrypted_data)

# Global encryption service instance
encryption_service = EncryptionService()