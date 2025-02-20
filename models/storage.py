import json
import os
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class LocalStorage:
    """Local JSON file storage for block data"""
    
    def __init__(self, storage_path: str):
        """
        Initialize storage with file path
        
        Args:
            storage_path: Path to JSON storage file
        """
        self.storage_path = storage_path
        self._ensure_storage_file()
        logger.info(f"Initialized storage at: {storage_path}")

    def _ensure_storage_file(self):
        """Ensure storage file exists with valid JSON array"""
        try:
            if not os.path.exists(self.storage_path):
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
                # Create empty JSON array file
                with open(self.storage_path, 'w') as f:
                    json.dump([], f)
        except Exception as e:
            logger.error(f"Failed to initialize storage file: {str(e)}")
            raise

    def _read_data(self) -> List[Dict[str, Any]]:
        """Read all data from storage"""
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read storage file: {str(e)}")
            raise

    def _write_data(self, data: List[Dict[str, Any]]):
        """Write data to storage"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write to storage file: {str(e)}")
            raise

    def store_data(self, data: Dict[str, Any]) -> int:
        """
        Store new data and return its ID
        
        Args:
            data: Data to store
            
        Returns:
            Block ID (index in storage)
        """
        try:
            current_data = self._read_data()
            block_id = len(current_data)
            current_data.append(data)
            self._write_data(current_data)
            return block_id
        except Exception as e:
            logger.error(f"Failed to store data: {str(e)}")
            raise

    def get_data(self, block_id: int) -> Dict[str, Any]:
        """
        Retrieve data by ID
        
        Args:
            block_id: ID of block to retrieve
            
        Returns:
            Block data
        """
        try:
            current_data = self._read_data()
            if 0 <= block_id < len(current_data):
                return current_data[block_id]
            raise ValueError(f"Invalid block ID: {block_id}")
        except Exception as e:
            logger.error(f"Failed to get data for block {block_id}: {str(e)}")
            raise

    def get_data_count(self) -> int:
        """
        Get total number of stored blocks
        
        Returns:
            Number of blocks in storage
        """
        try:
            return len(self._read_data())
        except Exception as e:
            logger.error(f"Failed to get data count: {str(e)}")
            raise 