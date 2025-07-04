from cryptography.fernet import Fernet
import os

def generate_key():
    """Generate a new encryption key"""
    return Fernet.generate_key()

def encrypt_data(data: str, key: bytes) -> bytes:
    """Encrypt data using the provided key"""
    f = Fernet(key)
    return f.encrypt(data.encode())

def decrypt_data(encrypted_data: bytes, key: bytes) -> str:
    """Decrypt data using the provided key"""
    f = Fernet(key)
    return f.decrypt(encrypted_data).decode()