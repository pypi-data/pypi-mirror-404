"""
FixCrypto - библиотека для безопасного шифрования текста
Метод: Double XOR Cipher
"""

from .core import encrypt, decrypt, quick_encrypt  # ← quick_encrypt ДОЛЖНА быть здесь
from .key_manager import generate_keys, create_keychain, verify_integrity
from .file_ops import (
    encrypt_file, decrypt_file, save_keys, load_keys,
    secure_delete, generate_qr
)
from .utils import detect_content_type, compress_data, add_metadata, recover_data, validate_keys
from .errors import CryptoError, KeyError, FileError

__version__ = "1.0.0"
__author__ = "FixCrypto"
__all__ = [
    'encrypt', 'decrypt', 'quick_encrypt',  # ← quick_encrypt здесь
    'generate_keys', 'create_keychain', 'verify_integrity',
    'encrypt_file', 'decrypt_file', 'save_keys', 'load_keys',
    'secure_delete', 'generate_qr',
    'detect_content_type', 'compress_data', 'add_metadata', 'recover_data', 'validate_keys',
    'CryptoError', 'KeyError', 'FileError'
]