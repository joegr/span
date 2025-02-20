from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Dedicated service for generating and managing text embeddings"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize with a specific model"""
        try:
            self.model = SentenceTransformer(model_name)
            self.vector_size = self.model.get_sentence_embedding_dimension()
            logger.info(f"Initialized embedding service with model: {model_name}")
            logger.info(f"Vector dimension: {self.vector_size}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {str(e)}")
            raise

    def health_check(self) -> Dict[str, Any]:
        """Check if the embedding service is healthy"""
        try:
            # Test embedding generation
            test_text = "Test embedding generation"
            embedding = self.model.encode([test_text])[0]
            
            return {
                "status": "healthy",
                "model_name": self.model.get_config_dict()['model_name'],
                "vector_size": self.vector_size,
                "test_successful": len(embedding) == self.vector_size
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            if not text.strip():
                return [0.0] * self.vector_size
                
            embedding = self.model.encode([text])[0]
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            # Filter out empty texts
            valid_texts = [text for text in texts if text.strip()]
            if not valid_texts:
                return [[0.0] * self.vector_size] * len(texts)
                
            embeddings = self.model.encode(valid_texts)
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            raise

    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
        except Exception as e:
            logger.error(f"Failed to compute similarity: {str(e)}")
            raise 