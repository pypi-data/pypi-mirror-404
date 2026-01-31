import random
import struct
from typing import Tuple, Dict, Any
from .errors import CryptoError

class _CryptoCore:
    def __init__(self):
        self._setup_alphabet()

    def _setup_alphabet(self):
        """Расширенный алфавит: все символы UTF-8"""
        self.alphabet = {}
        self.reverse_alphabet = {}

        # Базовые символы (0-255)
        for i in range(256):
            char = chr(i)
            self.alphabet[char] = i + 1000  # Смещение для безопасности
            self.reverse_alphabet[i + 1000] = char

        # Дополнительные символы Unicode
        extra_chars = "©®™€£¥¢§¶†‡•…≠≈≤≥±÷×∞π√∆∏∑"
        for i, char in enumerate(extra_chars, 3000):
            self.alphabet[char] = i
            self.reverse_alphabet[i] = char

    def _double_xor_encrypt(self, text: str, key1: int, key2: int) -> str:
        if not isinstance(key1, int) or not isinstance(key2, int):
            raise CryptoError("Keys must be integers")

        key1_digits = [int(d) for d in str(key1)]
        key2_digits = [int(d) for d in str(key2)]
        key1_len = len(key1_digits)
        key2_len = len(key2_digits)

        result = []
        for i, char in enumerate(text):
            if char not in self.alphabet:
                raise CryptoError(f"Unsupported character: {repr(char)}")

            num = self.alphabet[char]

            # Первый XOR слой
            key1_part = key1_digits[i % key1_len]
            encrypted1 = num ^ key1_part

            # Второй XOR слой
            key2_part = key2_digits[i % key2_len]
            encrypted2 = encrypted1 ^ key2_part

            # Модульная арифметика
            encrypted_final = (encrypted2 + key1_part + key2_part) % 10000

            result.append(f'{encrypted_final:04d}')

        return ' '.join(result)

    def _double_xor_decrypt(self, ciphertext: str, key1: int, key2: int) -> str:
        numbers = ciphertext.split()
        key1_digits = [int(d) for d in str(key1)]
        key2_digits = [int(d) for d in str(key2)]
        key1_len = len(key1_digits)
        key2_len = len(key2_digits)

        result = []
        for i, num_str in enumerate(numbers):
            try:
                encrypted_final = int(num_str)

                # Обратная модульная арифметика
                key1_part = key1_digits[i % key1_len]
                key2_part = key2_digits[i % key2_len]
                encrypted2 = (encrypted_final - key1_part - key2_part) % 10000

                # Второй XOR слой обратно
                encrypted1 = encrypted2 ^ key2_part

                # Первый XOR слой обратно
                original_num = encrypted1 ^ key1_part

                if original_num not in self.reverse_alphabet:
                    raise CryptoError(f"Invalid ciphertext at position {i}")

                result.append(self.reverse_alphabet[original_num])
            except ValueError:
                raise CryptoError(f"Invalid number format: {num_str}")

        return ''.join(result)

# Глобальный экземпляр для синглтона
_core = _CryptoCore()

def encrypt(text: str, key1: int, key2: int) -> str:
    return _core._double_xor_encrypt(text, key1, key2)

def decrypt(ciphertext: str, key1: int, key2: int) -> str:
    return _core._double_xor_decrypt(ciphertext, key1, key2)

def quick_encrypt(text: str) -> Dict[str, Any]:
    """
    Быстрое шифрование с автоматической генерацией ключей

    Args:
        text: Текст для шифрования

    Returns:
        Словарь с ключами и зашифрованным текстом
    """
    from .key_manager import generate_keys
    from datetime import datetime

    key1, key2 = generate_keys()
    ciphertext = encrypt(text, key1, key2)

    return {
        'ciphertext': ciphertext,
        'key1': key1,
        'key2': key2,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'method': 'Double XOR Cipher'
    }