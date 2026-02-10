"""
ChronoForge RAG - Embedding Engine

Supports:
- Local: sentence-transformers (all-MiniLM-L6-v2)
- API: OpenAI embeddings, Google Gemini embeddings
"""

from typing import List, Optional
import os

from chronoforge_rag import IEmbeddingEngine, EmbeddingConfig, DEFAULT_EMBEDDING_DIM


class SentenceTransformerEmbedding(IEmbeddingEngine):
    """
    Local embedding using sentence-transformers.
    Default model: all-MiniLM-L6-v2 (384 dimensions)
    """
    
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self._model = None
        self._dimension = config.dimension
    
    @property
    def model(self):
        """Lazy load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.config.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )
        return self._model
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension


class OpenAIEmbedding(IEmbeddingEngine):
    """
    OpenAI API embeddings.
    Model: text-embedding-3-small (1536 dimensions) or text-embedding-3-large (3072)
    """
    
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.api_key = config.api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY env var or pass in config.")
        
        self.model_name = config.model_name if config.model_name != "all-MiniLM-L6-v2" else "text-embedding-3-small"
        self._client = None
        
        # Dimension based on model
        if "large" in self.model_name:
            self._dimension = 3072
        else:
            self._dimension = 1536
    
    @property
    def client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai not installed. Run: pip install openai")
        return self._client
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        response = self.client.embeddings.create(
            model=self.model_name,
            input=text
        )
        return response.data[0].embedding
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        response = self.client.embeddings.create(
            model=self.model_name,
            input=texts
        )
        return [item.embedding for item in response.data]
    
    def get_dimension(self) -> int:
        return self._dimension


class GeminiEmbedding(IEmbeddingEngine):
    """
    Google Gemini API embeddings.
    Model: text-embedding-004 (768 dimensions)
    """
    
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.api_key = config.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key required. Set GEMINI_API_KEY env var or pass in config.")
        
        self.model_name = "text-embedding-004"
        self._dimension = 768
        self._client = None
    
    @property
    def client(self):
        """Lazy load Gemini client."""
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except ImportError:
                raise ImportError("google-genai not installed. Run: pip install google-genai")
        return self._client
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        result = self.client.models.embed_content(
            model=self.model_name,
            contents=text
        )
        return result.embeddings[0].values
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            embeddings.append(self.embed(text))
        return embeddings
    
    def get_dimension(self) -> int:
        return self._dimension


class HashEmbedding(IEmbeddingEngine):
    """
    Fallback: Hash-based embeddings when no model available.
    Uses character n-gram hashing - lightweight but less accurate.
    """
    
    def __init__(self, dimension: int = DEFAULT_EMBEDDING_DIM):
        self._dimension = dimension
    
    def _hash_ngram(self, ngram: str) -> int:
        """FNV-1a hash."""
        h = 14695981039346656037
        for c in ngram:
            h ^= ord(c)
            h *= 1099511628211
            h &= 0xFFFFFFFFFFFFFFFF  # Keep 64-bit
        return h
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding using character n-gram hashing."""
        embedding = [0.0] * self._dimension
        
        # Lowercase and normalize
        text = text.lower()
        
        # Generate character n-grams (n=3,4,5)
        for n in range(3, 6):
            for i in range(len(text) - n + 1):
                ngram = text[i:i+n]
                h = self._hash_ngram(ngram)
                
                idx1 = h % self._dimension
                idx2 = (h >> 16) % self._dimension
                sign = 1.0 if (h >> 32) & 1 else -1.0
                
                embedding[idx1] += sign * 0.1
                embedding[idx2] += sign * 0.1
        
        # Normalize
        norm = sum(x * x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return [self.embed(text) for text in texts]
    
    def get_dimension(self) -> int:
        return self._dimension


def create_embedding_engine(config: EmbeddingConfig) -> IEmbeddingEngine:
    """
    Factory function to create the appropriate embedding engine.
    
    Priority:
    1. If use_api=True and api_provider specified -> Use API
    2. If sentence-transformers available -> Use local model
    3. Fallback to hash embeddings
    """
    
    if config.use_api:
        if config.api_provider == "openai":
            return OpenAIEmbedding(config)
        elif config.api_provider == "gemini":
            return GeminiEmbedding(config)
        else:
            raise ValueError(f"Unknown API provider: {config.api_provider}")
    
    # Try local sentence-transformers
    try:
        return SentenceTransformerEmbedding(config)
    except ImportError:
        print("Warning: sentence-transformers not available, using hash embeddings")
        return HashEmbedding(config.dimension)
