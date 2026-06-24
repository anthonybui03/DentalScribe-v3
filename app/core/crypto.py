"""Encryption helpers — PBKDF2 key derivation + Fernet symmetric encryption."""
import hashlib
import os
import base64
from app.core.config import salt_path


def _get_salt() -> bytes:
    p = salt_path()
    if p.exists():
        return p.read_bytes()
    salt = os.urandom(32)
    p.write_bytes(salt)
    return salt


def derive_key(pin: str) -> bytes:
    salt = _get_salt()
    return base64.urlsafe_b64encode(
        hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 390_000)
    )


def get_fernet(key: bytes):
    from cryptography.fernet import Fernet
    return Fernet(key)


def hash_pin(pin: str) -> str:
    salt = _get_salt()
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 390_000).hex()


def verify_pin(pin: str, pin_hash: str) -> bool:
    return hash_pin(pin) == pin_hash


def encrypt(data: bytes, fernet) -> bytes:
    return fernet.encrypt(data)


def decrypt(data: bytes, fernet) -> bytes:
    return fernet.decrypt(data)
