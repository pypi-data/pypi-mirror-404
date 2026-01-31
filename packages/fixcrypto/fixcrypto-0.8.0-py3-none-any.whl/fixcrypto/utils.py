import hashlib
import zlib
import json
import mimetypes
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from .errors import ValidationError

def detect_content_type(data: Any) -> Dict[str, Any]:
    if isinstance(data, str):
        sample = data[:1000]
        text_chars = sum(1 for c in sample if 32 <= ord(c) <= 126 or c in '\n\r\t')
        ratio = text_chars / max(len(sample), 1)

        if ratio > 0.9:
            if any(keyword in data.lower() for keyword in ['def ', 'class ', 'import ', 'function ', 'var ', 'const ']):
                return {'type': 'code', 'language': 'auto', 'confidence': 0.85}
            elif any(tag in data.lower() for tag in ['<html>', '<div>', '<body>', '<script>']):
                return {'type': 'html', 'confidence': 0.9}
            elif data.strip().startswith('{') or data.strip().startswith('['):
                try:
                    json.loads(data)
                    return {'type': 'json', 'confidence': 0.95}
                except:
                    pass
            return {'type': 'text', 'confidence': ratio}
        else:
            return {'type': 'binary_text', 'confidence': 1 - ratio}

    elif isinstance(data, bytes):
        try:
            decoded = data[:1000].decode('utf-8', errors='ignore')
            text_chars = sum(1 for c in decoded if 32 <= ord(c) <= 126 or c in '\n\r\t')
            ratio = text_chars / max(len(decoded), 1)

            if ratio > 0.8:
                return {'type': 'text_bytes', 'confidence': ratio}
            else:
                signatures = {
                    b'\x89PNG': 'image_png',
                    b'\xff\xd8': 'image_jpeg',
                    b'GIF': 'image_gif',
                    b'BM': 'image_bmp',
                    b'%PDF': 'pdf',
                    b'PK\x03\x04': 'zip',
                    b'\x1f\x8b': 'gzip',
                    b'\x7fELF': 'executable'
                }

                for sig, filetype in signatures.items():
                    if data[:len(sig)] == sig:
                        return {'type': filetype, 'confidence': 0.99}

                return {'type': 'binary', 'confidence': 0.95}
        except:
            return {'type': 'unknown_binary', 'confidence': 0.5}

    return {'type': 'unknown', 'confidence': 0.0}

def compress_data(data: str, level: int = 6) -> Tuple[bytes, Dict[str, Any]]:
    if not isinstance(data, str):
        raise ValidationError("Data must be a string")

    original_bytes = data.encode('utf-8')
    original_size = len(original_bytes)

    compressed = zlib.compress(original_bytes, level=level)
    compressed_size = len(compressed)

    ratio = compressed_size / max(original_size, 1)

    info = {
        'original_size': original_size,
        'compressed_size': compressed_size,
        'compression_ratio': round(ratio, 3),
        'space_saved': round(1 - ratio, 3),
        'algorithm': 'zlib',
        'level': level
    }

    if ratio >= 1:
        info['note'] = 'Compression increased size, using original'
        return original_bytes, info

    return compressed, info

def decompress_data(compressed: bytes) -> Tuple[str, Dict[str, Any]]:
    try:
        decompressed = zlib.decompress(compressed)
        text = decompressed.decode('utf-8')

        info = {
            'decompressed_size': len(decompressed),
            'success': True,
            'encoding': 'utf-8'
        }

        return text, info
    except zlib.error as e:
        raise ValidationError(f"Decompression failed: {str(e)}")
    except UnicodeDecodeError:
        raise ValidationError("Decompressed data is not valid UTF-8")

def add_metadata(data: str, metadata: Dict[str, Any]) -> str:
    if not metadata:
        return data

    metadata_str = json.dumps(metadata, separators=(',', ':'))

    combined = {
        'metadata': metadata,
        'data': data,
        'hash': hashlib.sha256(data.encode()).hexdigest()[:16],
        'version': '1.0'
    }

    return json.dumps(combined)

def extract_metadata(encoded_data: str) -> Tuple[str, Dict[str, Any]]:
    try:
        parsed = json.loads(encoded_data)

        if not isinstance(parsed, dict):
            return encoded_data, {}

        if 'data' in parsed and 'metadata' in parsed:
            data = parsed['data']
            metadata = parsed['metadata']

            stored_hash = parsed.get('hash', '')
            current_hash = hashlib.sha256(data.encode()).hexdigest()[:16]

            if stored_hash and stored_hash != current_hash:
                raise ValidationError("Data integrity check failed")

            return data, metadata
        else:
            return encoded_data, {}
    except json.JSONDecodeError:
        return encoded_data, {}

def recover_data(corrupted_data: str, method: str = 'aggressive') -> Tuple[str, Dict[str, Any]]:
    if method not in ['conservative', 'aggressive', 'bruteforce']:
        raise ValidationError("Invalid recovery method")

    recovery_info = {
        'method': method,
        'original_length': len(corrupted_data),
        'issues_found': 0,
        'repairs_made': 0
    }

    if method == 'conservative':
        recovered = corrupted_data.replace('\x00', '').replace('\ufffd', '?')
        recovery_info['issues_found'] = corrupted_data.count('\x00') + corrupted_data.count('\ufffd')
        recovery_info['repairs_made'] = recovery_info['issues_found']

    elif method == 'aggressive':
        import re
        recovered = corrupted_data

        fixes = [
            (r'[^\x00-\x7F]+', '?'),  # Non-ASCII
            (r'\x00+', ''),           # Null bytes
            (r'\r\n', '\n'),          # Line endings     ← # вместо //
            (r'\s{3,}', '  ')         # Multiple spaces  ← # вместо //
        ]

        for pattern, replacement in fixes:
            before = len(recovered)
            recovered = re.sub(pattern, replacement, recovered)
            recovery_info['repairs_made'] += before - len(recovered)

        recovery_info['issues_found'] = recovery_info['repairs_made']

    else:  # bruteforce
        recovered = ''
        for char in corrupted_data:
            if 32 <= ord(char) <= 126 or char in '\n\r\t':
                recovered += char
            else:
                recovered += '?'
                recovery_info['issues_found'] += 1

        recovery_info['repairs_made'] = recovery_info['issues_found']

    recovery_info['recovered_length'] = len(recovered)
    recovery_info['success_rate'] = round(1 - (recovery_info['issues_found'] / max(len(corrupted_data), 1)), 3)

    return recovered, recovery_info

def calculate_entropy(data: str) -> Dict[str, Any]:
    from collections import Counter
    import math

    if not data:
        return {'entropy': 0.0, 'unique_chars': 0, 'length': 0}

    length = len(data)
    freq = Counter(data)

    entropy = 0.0
    for count in freq.values():
        probability = count / length
        entropy -= probability * math.log2(probability)

    max_entropy = math.log2(min(len(freq), 256))

    return {
        'entropy': round(entropy, 4),
        'max_possible': round(max_entropy, 4),
        'efficiency': round(entropy / max(max_entropy, 0.001), 3),
        'unique_chars': len(freq),
        'total_chars': length,
        'character_diversity': round(len(freq) / min(length, 256), 3)
    }

def validate_keys(key1: int, key2: int) -> Dict[str, Any]:
    key1_str = str(key1)
    key2_str = str(key2)

    issues = []

    if len(key1_str) < 4:
        issues.append(f"Key1 too short ({len(key1_str)} chars)")
    if len(key2_str) < 4:
        issues.append(f"Key2 too short ({len(key2_str)} chars)")

    if key1_str[0] == '0':
        issues.append("Key1 starts with zero")
    if key2_str[0] == '0':
        issues.append("Key2 starts with zero")

    if key1_str == key1_str[::-1]:
        issues.append("Key1 is a palindrome")
    if key2_str == key2_str[::-1]:
        issues.append("Key2 is a palindrome")

    if len(set(key1_str)) == 1:
        issues.append("Key1 has all same digits")
    if len(set(key2_str)) == 1:
        issues.append("Key2 has all same digits")

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'key1_length': len(key1_str),
        'key2_length': len(key2_str),
        'key1_entropy': calculate_entropy(key1_str)['entropy'],
        'key2_entropy': calculate_entropy(key2_str)['entropy']
    }