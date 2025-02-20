from dataclasses import dataclass
from typing import List

@dataclass
class NLPMetadata:
    """Metadata for NLP-processed text spans"""
    text: str
    vector: List[float]
    start_char: int
    end_char: int
    sentiment: float 