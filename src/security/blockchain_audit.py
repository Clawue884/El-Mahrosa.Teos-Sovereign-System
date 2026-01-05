import hashlib
import json
import time
import logging
from typing import List, Dict

# Optional: For real Ethereum integration (uncomment and install web3)
# from web3 import Web3
# w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))  # Connect to local node

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SovereignBlockchainAudit:
    """
    Lightweight blockchain module for Teos Sovereign System.
    Creates an immutable audit trail for actions like file encryption/decryption.
    Uses proof-of-work for consensus, ensuring tamper-proof logs.
    Can be extended to Ethereum for decentralized storage.
    """
    
    def __init__(self, difficulty: int = 4):
        """
        Initialize blockchain with genesis block.
        Difficulty: Number of leading zeros for proof-of-work (adjust for performance).
        """
        self.chain: List[Dict] = []
        self.pending_actions: List[str] = []
        self.difficulty = difficulty
        self.create_genesis_block()
        logging.info("Blockchain audit initialized with genesis block.")

    def create_genesis_block(self):
        """Create the first block in the chain."""
        genesis_block = {
            'index': 0,
            'timestamp': time.time(),
            'actions': ['Genesis: Sovereign System Initialized'],
            'previous_hash': '0',
            'hash': self.calculate_hash(0, time.time(), ['Genesis: Sovereign System Initialized'], '0'),
            'nonce': 0
        }
        self.chain.append(genesis_block)

    def calculate_hash(self, index: int, timestamp: float, actions: List[str], previous_hash: str, nonce: int = 0) -> str:
        """Calculate SHA-256 hash for a block."""
        block_string = json.dumps({
            'index': index,
            'timestamp': timestamp,
            'actions': actions,
            'previous_hash': previous_hash,
            'nonce': nonce
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, index: int, timestamp: float, actions: List[str], previous_hash: str) -> int:
        """Simple proof-of-work: Find nonce that makes hash start with 'difficulty' zeros."""
        nonce = 0
        while True:
            hash_value = self.calculate_hash(index, timestamp, actions, previous_hash, nonce)
            if hash_value[:self.difficulty] == '0' * self.difficulty:
                return nonce
            nonce += 1

    def add_block(self, actions: List[str]):
        """Mine and add a new block with pending actions."""
        if not actions:
            return
        previous_block = self.chain[-1]
        index = previous_block['index'] + 1
        timestamp = time.time()
        nonce = self.proof_of_work(index, timestamp, actions, previous_block['hash'])
        hash_value = self.calculate_hash(index, timestamp, actions, previous_block['hash'], nonce)
        
        new_block = {
            'index': index,
            'timestamp': timestamp,
            'actions': actions,
            'previous_hash': previous_block['hash'],
            'hash': hash_value,
            'nonce': nonce
        }
        self.chain.append(new_block)
        self.pending_actions = []  # Clear pending after mining
        logging.info(f"Block {index} added to audit chain with {len(actions)} actions.")

    def log_action(self, action: str):
        """Log an action to pending list and mine a block if threshold reached."""
        self.pending_actions.append(action)
        if len(self.pending_actions) >= 5:  # Mine every 5 actions for efficiency
            self.add_block(self.pending_actions.copy())

    def verify_chain(self) -> bool:
        """Verify the entire chain's integrity."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            # Check hash consistency
            if current['previous_hash'] != previous['hash']:
                logging.error(f"Chain invalid at block {i}: Previous hash mismatch.")
                return False
            # Recalculate hash
            recalculated = self.calculate_hash(
                current['index'], current['timestamp'], current['actions'], current['previous_hash'], current['nonce']
            )
            if recalculated != current['hash']:
                logging.error(f"Chain invalid at block {i}: Hash mismatch.")
                return False
            # Check proof-of-work
            if not current['hash'].startswith('0' * self.difficulty):
                logging.error(f"Chain invalid at block {i}: Proof-of-work failed.")
                return False
        logging.info("Blockchain audit chain verified successfully.")
        return True

    def get_chain_summary(self) -> str:
        """Return a summary of the chain for debugging."""
        return json.dumps([{'index': b['index'], 'actions': b['actions'], 'hash': b['hash'][:10] + '...'} for b in self.chain], indent=2)

    # Optional: Ethereum Integration (uncomment for real blockchain)
    # def store_on_ethereum(self, action: str):
    #     if not w3.isConnected():
    #         logging.error("Ethereum node not connected.")
    #         return
    #     # Deploy a simple contract or use existing one for logging
    #     # (Requires contract ABI and address)
    #     # Example: contract.functions.logAction(action).transact({'from': w3.eth.accounts[0]})

# Unit Tests (jalankan dengan pytest atau python -m unittest)
import unittest

class TestSovereignBlockchainAudit(unittest.TestCase):
    def setUp(self):
        self.audit = SovereignBlockchainAudit(difficulty=2)  # Lower difficulty for fast tests

    def test_genesis_block(self):
        self.assertEqual(len(self.audit.chain), 1)
        self.assertEqual(self.audit.chain[0]['index'], 0)
        self.assertTrue(self.audit.verify_chain())

    def test_add_block_and_verify(self):
        self.audit.log_action("Test action 1")
        self.audit.log_action("Test action 2")
        self.audit.log_action("Test action 3")
        self.audit.log_action("Test action 4")
        self.audit.log_action("Test action 5")  # Triggers mining
        self.assertEqual(len(self.audit.chain), 2)
        self.assertIn("Test action 1", self.audit.chain[1]['actions'])
        self.assertTrue(self.audit.verify_chain())

    def test_chain_integrity(self):
        self.audit.add_block(["Valid action"])
        self.assertTrue(self.audit.verify_chain())
        # Tamper with chain
        self.audit.chain[1]['actions'] = ["Tampered"]
        self.assertFalse(self.audit.verify_chain())

if __name__ == "__main__":
    unittest.main()
