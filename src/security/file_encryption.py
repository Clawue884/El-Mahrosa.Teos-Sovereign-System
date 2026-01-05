import os
import hashlib
import logging
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag

# Setup logging untuk audit trail
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SovereignFileEncryptor:
    """
    Advanced file encryption module for Teos Sovereign System.
    Uses AES-256-GCM for authenticated encryption, ensuring data integrity and confidentiality.
    Supports passphrase-based key derivation for user-friendly sovereignty.
    """
    
    def __init__(self, passphrase: str = None, salt_length: int = 16):
        """
        Initialize encryptor with optional passphrase.
        If no passphrase, generates a random key (for automated systems).
        """
        self.salt_length = salt_length
        if passphrase:
            self.key = self._derive_key_from_passphrase(passphrase)
        else:
            self.key = os.urandom(32)  # 256-bit random key for maximum security
        logging.info("Encryptor initialized with secure key.")

    def _derive_key_from_passphrase(self, passphrase: str) -> bytes:
        """Derive a 256-bit key from passphrase using PBKDF2."""
        salt = os.urandom(self.salt_length)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # High iteration count for brute-force resistance
            backend=default_backend()
        )
        key = kdf.derive(passphrase.encode())
        # Store salt for decryption (in practice, prepend to encrypted file)
        self.salt = salt
        return key

    def encrypt_file(self, input_file: str, output_file: str) -> bool:
        """
        Encrypt a file with AES-256-GCM.
        Returns True on success, False on failure.
        """
        try:
            with open(input_file, 'rb') as f:
                data = f.read()
            
            iv = os.urandom(12)  # 96-bit IV for GCM
            cipher = Cipher(algorithms.AES(self.key), modes.GCM(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(data) + encryptor.finalize()
            tag = encryptor.tag  # Authentication tag
            
            # Write encrypted data: salt (if passphrase) + IV + tag + ciphertext
            with open(output_file, 'wb') as f:
                if hasattr(self, 'salt'):
                    f.write(self.salt)
                f.write(iv)
                f.write(tag)
                f.write(ciphertext)
            
            logging.info(f"File '{input_file}' encrypted successfully to '{output_file}'.")
            return True
        except Exception as e:
            logging.error(f"Encryption failed: {e}")
            return False

    def decrypt_file(self, input_file: str, output_file: str, passphrase: str = None) -> bool:
        """
        Decrypt a file. Requires passphrase if used during encryption.
        Returns True on success, False on failure (e.g., wrong key or corrupted data).
        """
        try:
            with open(input_file, 'rb') as f:
                if passphrase:
                    salt = f.read(self.salt_length)
                    kdf = PBKDF2HMAC(
                        algorithm=hashes.SHA256(),
                        length=32,
                        salt=salt,
                        iterations=100000,
                        backend=default_backend()
                    )
                    key = kdf.derive(passphrase.encode())
                else:
                    key = self.key
                
                iv = f.read(12)
                tag = f.read(16)
                ciphertext = f.read()
            
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            with open(output_file, 'wb') as f:
                f.write(plaintext)
            
            logging.info(f"File '{input_file}' decrypted successfully to '{output_file}'.")
            return True
        except InvalidTag:
            logging.error("Decryption failed: Invalid key or corrupted file.")
            return False
        except Exception as e:
            logging.error(f"Decryption failed: {e}")
            return False

# Unit Tests (jalankan dengan pytest atau python -m unittest)
import unittest
import tempfile

class TestSovereignFileEncryptor(unittest.TestCase):
    def setUp(self):
        self.encryptor = SovereignFileEncryptor()
        self.pass_encryptor = SovereignFileEncryptor(passphrase="testpass123")

    def test_encrypt_decrypt_random_key(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp_in:
            temp_in.write(b"Hello, Sovereign World!")
            temp_in_path = temp_in.name
        
        temp_out = tempfile.mktemp()
        temp_decrypt = tempfile.mktemp()
        
        self.assertTrue(self.encryptor.encrypt_file(temp_in_path, temp_out))
        self.assertTrue(self.encryptor.decrypt_file(temp_out, temp_decrypt))
        
        with open(temp_decrypt, 'rb') as f:
            self.assertEqual(f.read(), b"Hello, Sovereign World!")
        
        os.unlink(temp_in_path)
        os.unlink(temp_out)
        os.unlink(temp_decrypt)

    def test_encrypt_decrypt_passphrase(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp_in:
            temp_in.write(b"Secret data for sovereignty.")
            temp_in_path = temp_in.name
        
        temp_out = tempfile.mktemp()
        temp_decrypt = tempfile.mktemp()
        
        self.assertTrue(self.pass_encryptor.encrypt_file(temp_in_path, temp_out))
        self.assertTrue(self.pass_encryptor.decrypt_file(temp_out, temp_decrypt, passphrase="testpass123"))
        
        with open(temp_decrypt, 'rb') as f:
            self.assertEqual(f.read(), b"Secret data for sovereignty.")
        
        os.unlink(temp_in_path)
        os.unlink(temp_out)
        os.unlink(temp_decrypt)

if __name__ == "__main__":
    unittest.main()
