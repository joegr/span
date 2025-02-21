"""
Proof of Hash Generator
"""
import hashlib
from typing import Tuple, Optional
import time
from dataclasses import dataclass
import struct

@dataclass
class Proof:
    data: bytes
    nonce: int
    hash: bytes
    timestamp: int

class ProofGenerator:
    def __init__(self, difficulty: int = 3):
        """Initialize with difficulty (number of leading zeros required)."""
        self.difficulty = difficulty
        self.target = bytes([0] * difficulty) + bytes([255] * (32 - difficulty))
        
    def _hash(self, data: bytes, nonce: int) -> bytes:
        """Generate SHA256 hash of data and nonce."""
        return hashlib.sha256(data + struct.pack(">Q", nonce)).digest()
        
    def generate_proof(self, data: bytes, max_attempts: int = 1000000) -> Optional[Proof]:
        """Generate proof of work for given data."""
        nonce = 0
        start_time = int(time.time())
        
        while nonce < max_attempts:
            hash_result = self._hash(data, nonce)
            
            # Check if hash meets difficulty requirement
            if hash_result < self.target:
                return Proof(
                    data=data,
                    nonce=nonce,
                    hash=hash_result,
                    timestamp=start_time
                )
                
            nonce += 1
            
        return None
        
    def verify_proof(self, proof: Proof) -> bool:
        """Verify a proof meets difficulty requirement."""
        hash_result = self._hash(proof.data, proof.nonce)
        return hash_result == proof.hash and hash_result < self.target
        
    def verify_chain(self, proof1: Proof, proof2: Proof) -> bool:
        """Verify two proofs form a valid chain."""
        # Verify chronological order
        if proof1.timestamp >= proof2.timestamp:
            return False
            
        # Verify individual proofs
        if not (self.verify_proof(proof1) and self.verify_proof(proof2)):
            return False
            
        # Verify chain hash
        chain_hash = hashlib.sha256(proof1.hash + proof2.hash).digest()
        chain_target = bytes([0] * (self.difficulty - 1)) + bytes([255] * (33 - self.difficulty))
        
        return chain_hash < chain_target
        
    def find_next_proof(self, previous_proof: Proof, data: bytes) -> Optional[Proof]:
        """Find next proof that forms valid chain with previous proof."""
        nonce = 0
        start_time = int(time.time())
        
        while True:
            hash_result = self._hash(data, nonce)
            
            # Create candidate proof
            candidate = Proof(
                data=data,
                nonce=nonce,
                hash=hash_result,
                timestamp=start_time
            )
            
            # Check if it forms valid chain
            if self.verify_chain(previous_proof, candidate):
                return candidate
                
            nonce += 1
            if nonce >= 1000000:  # Prevent infinite loop
                return None 