"""
Ошибки библиотеки FixCrypto
"""

class CryptoError(Exception):
    """Базовая ошибка криптографии"""
    pass

class KeyError(CryptoError):
    """Ошибка связанная с ключами"""
    pass

class FileError(CryptoError):
    """Ошибка работы с файлами"""
    pass

class IntegrityError(CryptoError):
    """Ошибка целостности данных"""
    pass

class EncryptionError(CryptoError):
    """Ошибка в процессе шифрования/расшифровки"""
    pass

class ValidationError(CryptoError):
    """Ошибка валидации входных данных"""
    pass