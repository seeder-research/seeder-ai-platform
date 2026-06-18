from cryptography.fernet import Fernet
from app.config import settings

_fernet = Fernet(settings.connector_encryption_key.encode())


def encrypt_api_key(plaintext: str) -> bytes:
    return _fernet.encrypt(plaintext.encode())


def decrypt_api_key(ciphertext: bytes) -> str:
    return _fernet.decrypt(ciphertext).decode()
