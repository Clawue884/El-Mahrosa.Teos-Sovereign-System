import os
import logging
import tempfile
from src.security.file_encryption import SovereignFileEncryptor  # Import enkripsi
from src.security.blockchain_audit import SovereignBlockchainAudit  # Import audit

# IPFS Library
try:
    import ipfshttpclient
    IPFS_AVAILABLE = True
except ImportError:
    IPFS_AVAILABLE = False
    logging.warning("IPFS library not available. Using simulation mode.")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SovereignIPFSStorage:
    """
    Decentralized storage module for Teos Sovereign System using IPFS.
    Encrypts files before uploading to IPFS for privacy and sovereignty.
    Provides immutable, peer-to-peer storage without central servers.
    """
    
    def __init__(self, audit: SovereignBlockchainAudit = None, encryptor: SovereignFileEncryptor = None):
        """
        Initialize IPFS storage.
        audit: Blockchain audit instance.
        encryptor: File encryptor instance.
        """
        self.audit = audit or SovereignBlockchainAudit()
        self.encryptor = encryptor or SovereignFileEncryptor()
        self.client = None
        if IPFS_AVAILABLE:
            try:
                self.client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http')  # Local IPFS daemon
                logging.info("IPFS client connected.")
            except Exception as e:
                logging.error(f"IPFS connection failed: {e}. Switching to simulation.")
                IPFS_AVAILABLE = False
        if not IPFS_AVAILABLE:
            logging.info("Using IPFS simulation for testing.")
            self.simulated_files = {}  # Dict to simulate IPFS storage

    def upload_file(self, file_path: str) -> str or None:
        """
        Encrypt and upload file to IPFS.
        file_path: Path to file to upload.
        Returns IPFS hash (CID) or None if failed.
        """
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return None
        
        # Encrypt file first
        encrypted_path = file_path + ".enc"
        if not self.encryptor.encrypt_file(file_path, encrypted_path):
            logging.error("Encryption failed before upload.")
            return None
        
        try:
            if IPFS_AVAILABLE:
                # Upload encrypted file to IPFS
                res = self.client.add(encrypted_path)
                ipfs_hash = res['Hash']
                logging.info(f"File uploaded to IPFS with hash: {ipfs_hash}")
            else:
                # Simulation: Store file content in dict
                with open(encrypted_path, 'rb') as f:
                    content = f.read()
                ipfs_hash = f"simulated_hash_{hash(content)}"  # Fake hash
                self.simulated_files[ipfs_hash] = content
                logging.info(f"File simulated upload with hash: {ipfs_hash}")
            
            # Log to audit
            self.audit.log_action(f"File uploaded to IPFS: {os.path.basename(file_path)} -> {ipfs_hash}")
            os.unlink(encrypted_path)  # Clean up encrypted temp file
            return ipfs_hash
        except Exception as e:
            logging.error(f"Upload failed: {e}")
            os.unlink(encrypted_path)
            return None

    def download_file(self, ipfs_hash: str, output_path: str) -> bool:
        """
        Download and decrypt file from IPFS.
        ipfs_hash: IPFS content identifier.
        output_path: Path to save decrypted file.
        Returns True on success.
        """
        try:
            if IPFS_AVAILABLE:
                # Download from IPFS
                self.client.get(ipfs_hash, output_path + ".enc")
                encrypted_path = output_path + ".enc"
            else:
                # Simulation: Retrieve from dict
                if ipfs_hash not in self.simulated_files:
                    logging.error(f"Simulated file not found: {ipfs_hash}")
                    return False
                encrypted_path = output_path + ".enc"
                with open(encrypted_path, 'wb') as f:
                    f.write(self.simulated_files[ipfs_hash])
            
            # Decrypt file
            if self.encryptor.decrypt_file(encrypted_path, output_path):
                logging.info(f"File downloaded and decrypted from IPFS: {ipfs_hash}")
                self.audit.log_action(f"File downloaded from IPFS: {ipfs_hash} -> {os.path.basename(output_path)}")
                os.unlink(encrypted_path)  # Clean up
                return True
            else:
                logging.error("Decryption failed after download.")
                os.unlink(encrypted_path)
                return False
        except Exception as e:
            logging.error(f"Download failed: {e}")
            return False

    def get_file_info(self, ipfs_hash: str) -> dict or None:
        """
        Get metadata of file from IPFS.
        ipfs_hash: IPFS hash.
        Returns dict with size, etc., or None if failed.
        """
        try:
            if IPFS_AVAILABLE:
                info = self.client.ls(ipfs_hash)
                return info[0] if info else None
            else:
                # Simulation: Fake info
                return {'Name': 'simulated_file', 'Size': len(self.simulated_files.get(ipfs_hash, b''))}
        except Exception as e:
            logging.error(f"Failed to get file info: {e}")
            return None

# Unit Tests (jalankan dengan pytest atau python -m unittest)
import unittest

class TestSovereignIPFSStorage(unittest.TestCase):
    def setUp(self):
        self.audit = SovereignBlockchainAudit(difficulty=2)
        self.encryptor = SovereignFileEncryptor()
        self.storage = SovereignIPFSStorage(audit=self.audit, encryptor=self.encryptor)

    def test_upload_download_simulation(self):
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"Sovereign decentralized data")
            temp_path = temp_file.name
        
        # Upload
        ipfs_hash = self.storage.upload_file(temp_path)
        self.assertIsNotNone(ipfs_hash)
        
        # Download
        output_path = temp_path + "_downloaded"
        self.assertTrue(self.storage.download_file(ipfs_hash, output_path))
        
        # Verify content
        with open(output_path, 'rb') as f:
            self.assertEqual(f.read(), b"Sovereign decentralized data")
        
        # Check audit
        self.assertIn("uploaded to IPFS", self.audit.chain[-1]['actions'])
        
        # Clean up
        os.unlink(temp_path)
        os.unlink(output_path)

if __name__ == "__main__":
    unittest.main()
