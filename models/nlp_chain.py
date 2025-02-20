import json
from datetime import datetime
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import asdict
import logging
import asyncio

from models.nlp_metadata import NLPMetadata
from models.embedding_service import EmbeddingService
from models.solana_client import SolanaNLPChain

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NLPChain:
    """
    NLP chain with Solana storage capabilities
    Uses embedding service for text processing and Solana for data integrity
    """
    
    def __init__(self, 
                 rpc_url: str = "http://localhost:8899",
                 keypair_path: Optional[str] = None):
        """
        Initialize chain with Solana client and embedding service
        
        Args:
            rpc_url: Solana RPC URL
            keypair_path: Path to keypair file
        """
        # Initialize services
        self.embedding_service = EmbeddingService()
        self.solana = SolanaNLPChain(rpc_url, keypair_path)
        self.chain_state = None
        logger.info("Initialized NLP chain with Solana storage")

    async def initialize(self) -> None:
        """Initialize the chain state on Solana"""
        self.chain_state = await self.solana.initialize()
        logger.info(f"Initialized chain state at: {self.chain_state}")

    def _process_text(self, text: str, start_char: int = 0) -> NLPMetadata:
        """
        Process text using embedding service
        
        Args:
            text: Text to process
            start_char: Starting character position in the original text
            
        Returns:
            NLPMetadata with vector representation and span information
        """
        # Skip empty text
        if not text.strip():
            return NLPMetadata(
                text=text,
                vector=[0.0] * self.embedding_service.vector_size,
                start_char=start_char,
                end_char=start_char + len(text),
                sentiment=0.0
            )

        # Generate embedding
        vector = self.embedding_service.generate_embedding(text)
        
        # For now, use a simple sentiment approximation
        sentiment = 0.0
        
        return NLPMetadata(
            text=text,
            vector=vector,
            start_char=start_char,
            end_char=start_char + len(text),
            sentiment=sentiment
        )

    def _process_text_spans(self, text: str, span_length: int = 100, 
                          overlap: int = 50) -> List[NLPMetadata]:
        """
        Process text in overlapping spans
        
        Args:
            text: Text to process
            span_length: Length of each text span
            overlap: Number of characters to overlap between spans
            
        Returns:
            List of NLPMetadata for each span
        """
        if len(text) <= span_length:
            return [self._process_text(text)]
            
        spans = []
        start = 0
        
        while start < len(text):
            end = min(start + span_length, len(text))
            span_text = text[start:end]
            
            # Only process spans that are not just whitespace
            if span_text.strip():
                spans.append(self._process_text(span_text, start))
            
            start += span_length - overlap
            
        return spans

    async def add_block(self, text: str, metadata: Dict[str, Any], 
                     span_length: int = 100, overlap: int = 50) -> str:
        """
        Add a new block with processed text to Solana
        
        Args:
            text: Text to process and store
            metadata: Additional metadata to store
            span_length: Length of each text span
            overlap: Number of characters to overlap between spans
            
        Returns:
            Block account address
        """
        try:
            if not self.chain_state:
                raise ValueError("Chain not initialized. Call initialize() first.")
                
            # Process text in spans
            nlp_data = self._process_text_spans(text, span_length, overlap)
            
            # Calculate average vector for storage
            vectors = [span.vector for span in nlp_data]
            avg_vector = np.mean(vectors, axis=0).tolist()
            
            # Store block on Solana
            block_address = await self.solana.add_block(
                text=text,
                vector=avg_vector,
                metadata={
                    **metadata,
                    'spans': [asdict(span) for span in nlp_data]
                },
                chain_state=self.chain_state
            )
            
            logger.info(f"Added block: {block_address}")
            return block_address
            
        except Exception as e:
            logger.error(f"Error adding block: {str(e)}")
            raise

    async def get_block(self, block_address: str) -> Dict[str, Any]:
        """
        Retrieve block data from Solana
        
        Args:
            block_address: Block account address
            
        Returns:
            Block data including NLP metadata
        """
        try:
            return await self.solana.get_block(block_address)
        except Exception as e:
            logger.error(f"Error getting block {block_address}: {str(e)}")
            raise

    async def search_similar(self, query: str, 
                         threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Search for text spans with similar vector representations
        
        Args:
            query: Search query
            threshold: Minimum similarity threshold
            
        Returns:
            List of matching spans with similarity scores
        """
        try:
            # Generate query embedding
            query_vector = self.embedding_service.generate_embedding(query)
            matches = []
            
            # Get chain state
            state = await self.solana.get_chain_state(self.chain_state)
            
            # Search through blocks
            for i in range(state['block_count']):
                # Get block PDA
                block_address = self.solana.derive_block_address(i)
                block_data = await self.get_block(block_address)
                
                # Search through each span in the block
                metadata = block_data['metadata']
                for span_data in metadata.get('spans', []):
                    similarity = self.embedding_service.compute_similarity(
                        query_vector, 
                        span_data['vector']
                    )
                    
                    if similarity >= threshold:
                        matches.append({
                            'text': span_data['text'],
                            'similarity': float(similarity),
                            'timestamp': block_data['timestamp'],
                            'metadata': metadata,
                            'span': {
                                'start': span_data['start_char'],
                                'end': span_data['end_char']
                            },
                            'context': block_data['text']
                        })
            
            # Sort matches by similarity score
            matches.sort(key=lambda x: x['similarity'], reverse=True)
            return matches
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            raise

    async def close(self):
        """Close the Solana client connection"""
        await self.solana.close() 