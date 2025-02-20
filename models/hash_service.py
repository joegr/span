from hashlib import sha256
from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Block:
    """Represents a block in the chain"""
    index: int
    timestamp: str
    data: str
    previous_hash: str
    hash: str

class HashService:
    """Dedicated service for block hashing and verification"""
    
    def __init__(self):
        """Initialize the hash service"""
        self.blocks: List[Block] = []
        logger.info("Initialized hash service")

    def calculate_hash(self, index: int, timestamp: str, data: str, previous_hash: str) -> str:
        """Calculate SHA-256 hash of block data"""
        value = str(index) + timestamp + data + previous_hash
        return sha256(value.encode()).hexdigest()

    def create_block(self, data: str) -> Block:
        """Create a new block and add it to the chain"""
        try:
            index = len(self.blocks)
            timestamp = datetime.utcnow().isoformat()
            previous_hash = self.blocks[-1].hash if self.blocks else "0" * 64
            
            # Calculate block hash
            block_hash = self.calculate_hash(index, timestamp, data, previous_hash)
            
            # Create new block
            block = Block(
                index=index,
                timestamp=timestamp,
                data=data,
                previous_hash=previous_hash,
                hash=block_hash
            )
            
            self.blocks.append(block)
            logger.info(f"Created block {index} with hash {block_hash[:8]}...")
            return block
            
        except Exception as e:
            logger.error(f"Failed to create block: {str(e)}")
            raise

    def verify_chain(self) -> Dict[str, Any]:
        """Verify the integrity of the entire chain"""
        try:
            for i in range(1, len(self.blocks)):
                current = self.blocks[i]
                previous = self.blocks[i-1]
                
                # Verify previous hash reference
                if current.previous_hash != previous.hash:
                    return {
                        "valid": False,
                        "error": f"Block {i} has invalid previous hash reference"
                    }
                
                # Verify current block hash
                calculated_hash = self.calculate_hash(
                    current.index,
                    current.timestamp,
                    current.data,
                    current.previous_hash
                )
                if calculated_hash != current.hash:
                    return {
                        "valid": False,
                        "error": f"Block {i} has invalid hash"
                    }
            
            return {
                "valid": True,
                "block_count": len(self.blocks)
            }
            
        except Exception as e:
            logger.error(f"Chain verification failed: {str(e)}")
            raise

    def get_block(self, index: int) -> Optional[Block]:
        """Get a block by index"""
        try:
            if 0 <= index < len(self.blocks):
                return self.blocks[index]
            return None
        except Exception as e:
            logger.error(f"Failed to get block {index}: {str(e)}")
            raise

    def calculate_merkle_root(self, data_list: List[str]) -> str:
        """Calculate Merkle root hash for a list of data"""
        if not data_list:
            return sha256("".encode()).hexdigest()
            
        # Hash all data items
        hashes = [sha256(data.encode()).hexdigest() for data in data_list]
        
        # Build Merkle tree
        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])
            
            next_level = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i+1]
                next_level.append(sha256(combined.encode()).hexdigest())
            hashes = next_level
            
        return hashes[0]

    def health_check(self) -> Dict[str, Any]:
        """Check if the hash service is healthy"""
        try:
            # Test hash generation
            test_hash = self.calculate_hash(0, datetime.utcnow().isoformat(), "test", "0"*64)
            
            return {
                "status": "healthy",
                "block_count": len(self.blocks),
                "test_hash_valid": len(test_hash) == 64 and all(c in "0123456789abcdef" for c in test_hash)
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            } 