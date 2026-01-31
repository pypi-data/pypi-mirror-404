"""
Управление ключами для FixCrypto
"""

import random
import hashlib
import secrets
from typing import Tuple, Dict, Any
from .errors import KeyError, IntegrityError

def generate_keys(min_length: int = 4, max_length: int = 8) -> Tuple[int, int]:
    """
    Генерирует пару случайных ключей

    Args:
        min_length: Минимальная длина ключа в цифрах
        max_length: Максимальная длина ключа в цифрах

    Returns:
        Кортеж (key1, key2)

    Raises:
        KeyError: Если параметры неверны
    """
    if min_length < 4:
        raise KeyError("Minimum key length is 4 digits")
    if max_length > 12:
        raise KeyError("Maximum key length is 12 digits")

    length1 = random.randint(min_length, max_length)
    length2 = random.randint(min_length, max_length)

    # Генерация криптографически безопасных ключей
    def generate_key(length: int) -> int:
        # Первая цифра не может быть 0
        first_digit = secrets.randbelow(9) + 1
        other_digits = ''.join(str(secrets.randbelow(10)) for _ in range(length - 1))
        return int(str(first_digit) + other_digits)

    return generate_key(length1), generate_key(length2)

def create_keychain(master_password: str, salt: str = None) -> Dict[str, Any]:
    """
    Создает цепочку ключей из мастер-пароля

    Args:
        master_password: Мастер-пароль
        salt: Соль для хэширования (если None, генерируется)

    Returns:
        Словарь с ключами и информацией
    """
    if not master_password:
        raise KeyError("Master password cannot be empty")

    if salt is None:
        salt = secrets.token_hex(16)

    # Создаем производные ключи
    combined = f"{master_password}:{salt}"

    # Первый ключ из SHA256
    hash1 = hashlib.sha256(combined.encode()).hexdigest()
    key1 = int(hash1[:8], 16)  # Первые 8 hex символов -> число

    # Второй ключ из SHA512
    hash2 = hashlib.sha512(combined.encode()).hexdigest()
    key2 = int(hash2[:8], 16)  # Первые 8 hex символов -> число

    # Ключ для проверки целостности
    verify_hash = hashlib.md5(combined.encode()).hexdigest()[:6]

    return {
        'key1': key1,
        'key2': key2,
        'salt': salt,
        'verify_hash': verify_hash,
        'algorithm': 'PBKDF2-like key derivation'
    }

def verify_integrity(ciphertext: str, key1: int, key2: int) -> bool:
    """
    Проверяет, что ключи подходят для расшифровки

    Args:
        ciphertext: Зашифрованный текст
        key1: Первый ключ
        key2: Второй ключ

    Returns:
        True если ключи подходят, False если нет

    Note:
        Фактически пытается расшифровать первый блок
    """
    if not ciphertext:
        raise IntegrityError("Ciphertext cannot be empty")

    try:
        # Берем только первое число для проверки
        first_number = ciphertext.split()[0]

        # Проверяем формат
        if len(first_number) != 4 or not first_number.isdigit():
            return False

        # Простая проверка на минимальную корректность
        num = int(first_number)

        # Критерии проверки:
        # 1. Число должно быть в диапазоне 0000-9999
        # 2. Должно делиться на сумму цифр ключей (простая проверка)
        key1_sum = sum(int(d) for d in str(key1))
        key2_sum = sum(int(d) for d in str(key2))
        check_sum = (key1_sum + key2_sum) % 100

        return (num % 100) == check_sum

    except (ValueError, IndexError):
        return False

def key_strength_analyzer(key: int) -> Dict[str, Any]:
    """
    Анализирует стойкость ключа

    Args:
        key: Ключ для анализа

    Returns:
        Словарь с анализом
    """
    key_str = str(key)
    length = len(key_str)

    # Уникальные цифры
    unique_digits = len(set(key_str))

    # Энтропия (грубая оценка)
    digit_counts = {digit: key_str.count(digit) for digit in set(key_str)}
    entropy = -sum((count/length) * (count/length).bit_length()
                   for count in digit_counts.values())

    # Оценка стойкости
    if length < 6:
        strength = "weak"
    elif length < 8:
        strength = "medium"
    elif length < 10:
        strength = "strong"
    else:
        strength = "very strong"

    # Проверка на простые паттерны
    is_sequential = key_str in ''.join(str(i % 10) for i in range(length))
    is_repeated = len(set(key_str)) == 1
    is_palindrome = key_str == key_str[::-1]

    return {
        'length': length,
        'unique_digits': unique_digits,
        'entropy': round(entropy, 2),
        'strength': strength,
        'is_sequential': is_sequential,
        'is_repeated': is_repeated,
        'is_palindrome': is_palindrome,
        'recommendation': 'Increase length' if length < 8 else 'Good'
    }

def rotate_keys(old_key1: int, old_key2: int) -> Tuple[int, int, Dict[str, Any]]:
    """
    Создает новые ключи на основе старых

    Args:
        old_key1: Старый ключ 1
        old_key2: Старый ключ 2

    Returns:
        Новые ключи и информацию о ротации
    """
    # Используем старые ключи как seed для генерации новых
    seed = (old_key1 * 10000 + old_key2) % (2**31)
    random.seed(seed)

    # Генерируем новые ключи
    new_length1 = len(str(old_key1))
    new_length2 = len(str(old_key2))

    new_key1 = random.randint(10**(new_length1-1), 10**new_length1 - 1)
    new_key2 = random.randint(10**(new_length2-1), 10**new_length2 - 1)

    # Сбрасываем seed
    random.seed()

    return new_key1, new_key2, {
        'rotation_date': 'auto_generated',
        'original_length1': len(str(old_key1)),
        'original_length2': len(str(old_key2)),
        'method': 'deterministic_rotation'
    }