"""
File operations for FixCrypto library
"""

import os
import shutil
import struct
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from .errors import FileError, CryptoError
from .core import encrypt, decrypt

try:
    from PIL import Image, ImageDraw
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

def encrypt_file(input_path: str, output_path: str, key1: int, key2: int,
                 chunk_size: int = 1024) -> Dict[str, Any]:
    """
    Encrypts a file using Double XOR Cipher

    Args:
        input_path: Path to input file
        output_path: Path for encrypted output
        key1: First encryption key
        key2: Second encryption key
        chunk_size: Size of chunks to process (bytes)

    Returns:
        Dictionary with encryption info

    Raises:
        FileError: If file operations fail
        CryptoError: If encryption fails
    """
    try:
        input_path = Path(input_path)
        output_path = Path(output_path)

        if not input_path.exists():
            raise FileError(f"Input file not found: {input_path}")

        # Get file info
        file_size = input_path.stat().st_size
        file_type = _detect_file_type(input_path)

        # Read and encrypt
        with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
            # Write header
            header = struct.pack('!I', 0xF1C0C0DE)
            f_out.write(header)

            # Write metadata
            metadata = f"TYPE:{file_type},SIZE:{file_size},KEYS:{key1}:{key2}"
            metadata_encoded = metadata.encode('utf-8')
            f_out.write(struct.pack('!I', len(metadata_encoded)))
            f_out.write(metadata_encoded)

            # Process file in chunks
            total_chunks = 0
            while True:
                chunk = f_in.read(chunk_size)
                if not chunk:
                    break

                # Convert bytes to string for encryption
                try:
                    chunk_text = chunk.decode('utf-8', errors='replace')
                except:
                    # For binary data, encode as hex
                    chunk_text = chunk.hex()

                # Encrypt chunk
                encrypted_chunk = encrypt(chunk_text, key1, key2)

                # Write encrypted chunk
                chunk_encoded = encrypted_chunk.encode('utf-8')
                f_out.write(struct.pack('!I', len(chunk_encoded)))
                f_out.write(chunk_encoded)
                total_chunks += 1

        return {
            'input_file': str(input_path),
            'output_file': str(output_path),
            'original_size': file_size,
            'encrypted_size': output_path.stat().st_size,
            'chunks_processed': total_chunks,
            'file_type': file_type,
            'compression_ratio': round(output_path.stat().st_size / max(file_size, 1), 2)
        }

    except Exception as e:
        raise FileError(f"File encryption failed: {str(e)}")

def decrypt_file(input_path: str, output_path: str, key1: int, key2: int) -> Dict[str, Any]:
    """
    Decrypts a file encrypted with FixCrypto

    Args:
        input_path: Path to encrypted file
        output_path: Path for decrypted output
        key1: First encryption key
        key2: Second encryption key

    Returns:
        Dictionary with decryption info

    Raises:
        FileError: If file operations fail
        CryptoError: If decryption fails
    """
    try:
        input_path = Path(input_path)
        output_path = Path(output_path)

        if not input_path.exists():
            raise FileError(f"Input file not found: {input_path}")

        with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
            # Read and verify header
            header = f_in.read(4)
            if len(header) < 4 or struct.unpack('!I', header)[0] != 0xF1C0C0DE:
                raise CryptoError("Invalid file format or corrupted")

            # Read metadata
            metadata_len = struct.unpack('!I', f_in.read(4))[0]
            metadata = f_in.read(metadata_len).decode('utf-8')

            # Parse metadata to verify keys
            metadata_parts = dict(part.split(':') for part in metadata.split(','))
            stored_key1 = int(metadata_parts.get('KEYS', '0:0').split(':')[0])
            stored_key2 = int(metadata_parts.get('KEYS', '0:0').split(':')[1])

            if stored_key1 != key1 or stored_key2 != key2:
                raise CryptoError("Keys do not match file metadata")

            # Decrypt chunks
            chunks_processed = 0
            while True:
                # Read chunk length
                length_bytes = f_in.read(4)
                if not length_bytes:
                    break

                chunk_len = struct.unpack('!I', length_bytes)[0]
                if chunk_len == 0:
                    break

                # Read encrypted chunk
                encrypted_chunk = f_in.read(chunk_len).decode('utf-8')

                # Decrypt chunk
                decrypted_chunk = decrypt(encrypted_chunk, key1, key2)

                # Determine if it's hex or text
                try:
                    if all(c in '0123456789abcdefABCDEF' for c in decrypted_chunk):
                        # Hex encoded binary data
                        chunk_bytes = bytes.fromhex(decrypted_chunk)
                    else:
                        # Text data
                        chunk_bytes = decrypted_chunk.encode('utf-8')
                except:
                    chunk_bytes = decrypted_chunk.encode('utf-8', errors='replace')

                f_out.write(chunk_bytes)
                chunks_processed += 1

        return {
            'input_file': str(input_path),
            'output_file': str(output_path),
            'chunks_processed': chunks_processed,
            'restored_size': output_path.stat().st_size
        }

    except Exception as e:
        raise FileError(f"File decryption failed: {str(e)}")

def save_keys(filename: str, key1: int, key2: int,
              metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Saves encryption keys to a file

    Args:
        filename: Path to save keys
        key1: First key
        key2: Second key
        metadata: Additional metadata to store

    Returns:
        Dictionary with save info
    """
    try:
        import json
        from datetime import datetime

        data = {
            'key1': key1,
            'key2': key2,
            'created': datetime.now().isoformat(),
            'algorithm': 'Double XOR Cipher',
            'version': '0.8.0'
        }

        if metadata:
            data['metadata'] = metadata

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        # Set restrictive permissions (Unix only)
        try:
            os.chmod(filename, 0o600)
        except:
            pass

        return {
            'filename': filename,
            'keys_saved': True,
            'key1_length': len(str(key1)),
            'key2_length': len(str(key2)),
            'backup_advice': 'Store in secure location'
        }

    except Exception as e:
        raise FileError(f"Failed to save keys: {str(e)}")

def load_keys(filename: str) -> Dict[str, Any]:
    """
    Loads encryption keys from a file

    Args:
        filename: Path to key file

    Returns:
        Dictionary with keys and metadata

    Raises:
        FileError: If file doesn't exist or is invalid
    """
    try:
        import json

        if not Path(filename).exists():
            raise FileError(f"Key file not found: {filename}")

        with open(filename, 'r') as f:
            data = json.load(f)

        # Validate required fields
        required = ['key1', 'key2']
        for field in required:
            if field not in data:
                raise FileError(f"Invalid key file: missing {field}")

        return data

    except json.JSONDecodeError:
        raise FileError(f"Invalid JSON in key file: {filename}")
    except Exception as e:
        raise FileError(f"Failed to load keys: {str(e)}")

def secure_delete(filepath: str, passes: int = 7) -> Dict[str, Any]:
    """
    Securely deletes a file by overwriting it multiple times

    Args:
        filepath: Path to file
        passes: Number of overwrite passes

    Returns:
        Dictionary with deletion info

    Note:
        Less effective on SSDs, but provides basic sanitization
    """
    try:
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileError(f"File not found: {filepath}")

        file_size = filepath.stat().st_size

        # Overwrite multiple times with different patterns
        patterns = [
            b'\x00' * 1024,  # Zeroes
            b'\xFF' * 1024,  # Ones
            os.urandom(1024),  # Random
            b'\xAA' * 1024,  # Alternating
            b'\x55' * 1024,  # Alternating
            b'\x92' * 1024,  # Random pattern
            b'\x49' * 1024,  # Random pattern
        ]

        with open(filepath, 'rb+') as f:
            for pass_num in range(min(passes, len(patterns))):
                f.seek(0)
                pattern = patterns[pass_num % len(patterns)]

                bytes_written = 0
                while bytes_written < file_size:
                    chunk_size = min(len(pattern), file_size - bytes_written)
                    f.write(pattern[:chunk_size])
                    bytes_written += chunk_size

        # Delete the file
        filepath.unlink()

        return {
            'file': str(filepath),
            'original_size': file_size,
            'passes': passes,
            'method': 'DoD 5220.22-M-like',
            'warning': 'Not guaranteed on SSDs or journaled filesystems'
        }

    except Exception as e:
        raise FileError(f"Secure deletion failed: {str(e)}")

def generate_qr(ciphertext: str, output_image: str, size: int = 10,
                version: int = 1) -> Dict[str, Any]:
    """
    Generates QR code from encrypted text

    Args:
        ciphertext: Encrypted text
        output_image: Path for QR code image
        size: QR code size multiplier
        version: QR code version (1-40)

    Returns:
        Dictionary with QR code info

    Note:
        Requires Pillow library
    """
    if not QR_AVAILABLE:
        raise FileError("QR generation requires Pillow library. Install with: pip install Pillow")

    try:
        import qrcode

        # Create QR code
        qr = qrcode.QRCode(
            version=version,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=4,
        )

        qr.add_data(ciphertext)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Save image
        output_path = Path(output_image)
        img.save(output_image)

        # Add metadata overlay (optional)
        try:
            img_with_meta = Image.open(output_image)
            draw = ImageDraw.Draw(img_with_meta)

            # Add small watermark
            width, height = img_with_meta.size
            watermark = f"FixCrypto v0.8.0"
            draw.text((10, height - 20), watermark, fill="gray")

            img_with_meta.save(output_image)
        except:
            pass

        return {
            'qr_image': output_image,
            'ciphertext_length': len(ciphertext),
            'qr_version': version,
            'size_pixels': f"{img.size[0]}x{img.size[1]}",
            'data_capacity': 'up to 2953 bytes',
            'note': 'Scan with any QR reader, then decrypt with keys'
        }

    except Exception as e:
        raise FileError(f"QR generation failed: {str(e)}")

def _detect_file_type(filepath: Path) -> str:
    """Detects file type based on extension and content"""
    # Check extension first
    ext = filepath.suffix.lower()

    # Text file extensions
    text_exts = {'.txt', '.py', '.js', '.html', '.css', '.json', '.xml',
                 '.csv', '.md', '.rst', '.yml', '.yaml', '.ini', '.cfg'}

    if ext in text_exts:
        return 'text'
    elif ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}:
        return 'image'
    elif ext in {'.mp3', '.wav', '.ogg', '.flac'}:
        return 'audio'
    elif ext in {'.mp4', '.avi', '.mkv', '.mov'}:
        return 'video'
    elif ext in {'.pdf', '.doc', '.docx', '.xls', '.xlsx'}:
        return 'document'
    elif ext == '.enc':
        return 'encrypted'
    else:
        # Try to read first bytes to determine
        try:
            with open(filepath, 'rb') as f:
                header = f.read(512)
                # Check for common binary signatures
                if header.startswith(b'\x89PNG'):
                    return 'image_png'
                elif header.startswith(b'\xff\xd8'):
                    return 'image_jpeg'
                elif header.startswith(b'%PDF'):
                    return 'pdf'
                elif b'\x00' in header[:100]:
                    return 'binary'
                else:
                    return 'text'
        except:
            return 'unknown'