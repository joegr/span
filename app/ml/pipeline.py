"""
Minimal ML Pipeline for text processing.
Optimized for ARM64 architecture and minimal memory footprint.
"""
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import spacy
from functools import lru_cache

class MLPipeline:
    def __init__(self):
        """Initialize the ML pipeline with minimal models."""
        # Load lightweight models
        self.nlp = spacy.load("en_core_web_sm")  # Lightweight model for basic NLP
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')  # Small, efficient model
        
    @lru_cache(maxsize=1000)
    def get_embedding(self, text: str) -> np.ndarray:
        """Get text embedding with caching for efficiency."""
        return self.encoder.encode(text, convert_to_tensor=False)
    
    def batch_process(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """Process texts in batches for memory efficiency."""
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.encoder.encode(batch, convert_to_tensor=False)
            embeddings.extend(batch_embeddings)
        return embeddings
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute semantic similarity between two texts."""
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    
    def extract_key_info(self, text: str) -> Dict[str, str]:
        """Extract essential information from text."""
        doc = self.nlp(text)
        return {
            'entities': [(ent.text, ent.label_) for ent in doc.ents],
            'key_phrases': [chunk.text for chunk in doc.noun_chunks],
            'summary': ' '.join([sent.text for sent in doc.sents][:2])  # First 2 sentences
        }
    
    def classify_text(self, text: str, categories: List[str]) -> str:
        """Simple zero-shot classification using similarity."""
        text_emb = self.get_embedding(text)
        cat_embs = [self.get_embedding(cat) for cat in categories]
        
        similarities = [
            np.dot(text_emb, cat_emb) / (np.linalg.norm(text_emb) * np.linalg.norm(cat_emb))
            for cat_emb in cat_embs
        ]
        return categories[np.argmax(similarities)]

    def cleanup(self):
        """Clean up resources."""
        self.get_embedding.cache_clear() 