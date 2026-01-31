"""
Embedding Layers Suite

This module implements various embedding layers for neural networks.
Embeddings convert discrete tokens (words, characters) into dense continuous vectors.

Implemented Embedding Types:
1. Embedding - Standard learned embedding layer
2. PositionalEncoding - Sinusoidal positional encoding for Transformers
3. LearnedPositionalEmbedding - Learned positional embeddings
4. TokenTypeEmbedding - Segment/token type embeddings (BERT-style)
5. CharacterEmbedding - Character-level embeddings

Key Benefits:
- Dense vector representations
- Semantic similarity capture
- Dimensionality reduction (vocab_size → embedding_dim)
- Learned from data
- Transfer learning support

References:
- Word2Vec: Mikolov et al., "Efficient Estimation of Word Representations in Vector Space" (2013)
- GloVe: Pennington et al., "GloVe: Global Vectors for Word Representation" (2014)
- Positional Encoding: Vaswani et al., "Attention Is All You Need" (2017)
- FastText: Bojanowski et al., "Enriching Word Vectors with Subword Information" (2017)

Author: Ali Mehdi
Date: January 22, 2026
"""

import numpy as np
from typing import Optional, Tuple


# ============================================================================
# STANDARD EMBEDDING LAYER
# ============================================================================

class Embedding:
    """
    Standard Embedding Layer.
    
    Converts token indices to dense vectors via lookup table.
    
    Formula:
        output = embedding_matrix[token_indices]
    
    Args:
        vocab_size: Size of vocabulary (number of unique tokens)
        embedding_dim: Dimension of embedding vectors
        padding_idx: Index for padding token (optional, won't be updated during training)
        max_norm: If given, embeddings are normalized to have max L2 norm
        scale_grad_by_freq: Scale gradients by token frequency (default: False)
    
    Example:
        >>> emb = Embedding(vocab_size=10000, embedding_dim=300)
        >>> tokens = np.array([[1, 2, 3, 4], [5, 6, 7, 8]])  # (batch, seq_len)
        >>> output = emb.forward(tokens)
        >>> print(output.shape)  # (2, 4, 300)
    
    Use Case:
        Word embeddings, token embeddings, any discrete to continuous mapping
    
    Reference:
        Mikolov et al., "Efficient Estimation of Word Representations" (2013)
    """
    
    def __init__(self, vocab_size: int, embedding_dim: int, 
                 padding_idx: Optional[int] = None,
                 max_norm: Optional[float] = None,
                 scale_grad_by_freq: bool = False):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.padding_idx = padding_idx
        self.max_norm = max_norm
        self.scale_grad_by_freq = scale_grad_by_freq
        
        # Initialize embedding matrix (Xavier/Glorot initialization)
        self.weight = np.random.randn(vocab_size, embedding_dim) * np.sqrt(2.0 / (vocab_size + embedding_dim))
        
        # Set padding embedding to zeros
        if padding_idx is not None:
            self.weight[padding_idx] = 0.0
        
        self.cache = None
    
    def forward(self, indices: np.ndarray) -> np.ndarray:
        """
        Forward pass.
        
        Args:
            indices: Token indices, shape (batch, seq_len) or (batch, seq_len, ...)
        
        Returns:
            Embedded vectors, shape (*indices.shape, embedding_dim)
        """
        # Lookup embeddings
        output = self.weight[indices]
        
        # Apply max norm if specified
        if self.max_norm is not None:
            norms = np.linalg.norm(output, axis=-1, keepdims=True)
            output = output * np.minimum(1.0, self.max_norm / (norms + 1e-8))
        
        self.cache = indices
        return output
    
    def load_pretrained(self, pretrained_embeddings: np.ndarray):
        """
        Load pretrained embeddings.
        
        Args:
            pretrained_embeddings: Pretrained embedding matrix (vocab_size, embedding_dim)
        """
        if pretrained_embeddings.shape != self.weight.shape:
            raise ValueError(f"Shape mismatch: expected {self.weight.shape}, got {pretrained_embeddings.shape}")
        
        self.weight = pretrained_embeddings.copy()
        
        # Reset padding embedding
        if self.padding_idx is not None:
            self.weight[self.padding_idx] = 0.0
    
    def freeze(self):
        """Freeze embeddings (don't update during training)."""
        self.frozen = True
    
    def unfreeze(self):
        """Unfreeze embeddings (allow updates during training)."""
        self.frozen = False
    
    def __call__(self, indices: np.ndarray) -> np.ndarray:
        return self.forward(indices)


# ============================================================================
# POSITIONAL ENCODING (SINUSOIDAL)
# ============================================================================

class PositionalEncoding:
    """
    Sinusoidal Positional Encoding for Transformers.
    
    Adds position information to token embeddings using sine and cosine functions.
    
    Formula:
        PE(pos, 2i) = sin(pos / 10000^(2i/d_model))
        PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
    
    Args:
        embedding_dim: Dimension of embeddings (must be even)
        max_len: Maximum sequence length (default: 5000)
        dropout: Dropout rate (default: 0.1)
    
    Example:
        >>> pos_enc = PositionalEncoding(embedding_dim=512, max_len=1000)
        >>> x = np.random.randn(32, 100, 512)  # (batch, seq_len, embedding_dim)
        >>> output = pos_enc.forward(x)
        >>> print(output.shape)  # (32, 100, 512)
    
    Use Case:
        Transformers, attention mechanisms, sequence position encoding
    
    Reference:
        Vaswani et al., "Attention Is All You Need" (2017)
    """
    
    def __init__(self, embedding_dim: int, max_len: int = 5000, dropout: float = 0.1):
        if embedding_dim % 2 != 0:
            raise ValueError(f"embedding_dim must be even, got {embedding_dim}")
        
        self.embedding_dim = embedding_dim
        self.max_len = max_len
        self.dropout = dropout
        
        # Create positional encoding matrix
        pe = np.zeros((max_len, embedding_dim))
        position = np.arange(0, max_len).reshape(-1, 1)
        div_term = np.exp(np.arange(0, embedding_dim, 2) * -(np.log(10000.0) / embedding_dim))
        
        pe[:, 0::2] = np.sin(position * div_term)
        pe[:, 1::2] = np.cos(position * div_term)
        
        self.pe = pe  # (max_len, embedding_dim)
    
    def forward(self, x: np.ndarray, training: bool = True) -> np.ndarray:
        """
        Forward pass.
        
        Args:
            x: Input embeddings (batch, seq_len, embedding_dim)
            training: Whether in training mode (apply dropout)
        
        Returns:
            Embeddings with positional encoding added
        """
        batch_size, seq_len, embedding_dim = x.shape
        
        if seq_len > self.max_len:
            raise ValueError(f"Sequence length {seq_len} exceeds max_len {self.max_len}")
        
        if embedding_dim != self.embedding_dim:
            raise ValueError(f"Expected embedding_dim {self.embedding_dim}, got {embedding_dim}")
        
        # Add positional encoding
        output = x + self.pe[:seq_len, :]
        
        # Apply dropout if training
        if training and self.dropout > 0:
            mask = np.random.binomial(1, 1 - self.dropout, size=output.shape)
            output = output * mask / (1 - self.dropout)
        
        return output
    
    def __call__(self, x: np.ndarray, training: bool = True) -> np.ndarray:
        return self.forward(x, training)


# ============================================================================
# LEARNED POSITIONAL EMBEDDING
# ============================================================================

class LearnedPositionalEmbedding:
    """
    Learned Positional Embeddings.
    
    Alternative to sinusoidal encoding, learns position embeddings from data.
    
    Args:
        max_len: Maximum sequence length
        embedding_dim: Dimension of embeddings
    
    Example:
        >>> pos_emb = LearnedPositionalEmbedding(max_len=512, embedding_dim=768)
        >>> x = np.random.randn(32, 100, 768)
        >>> output = pos_emb.forward(x)
        >>> print(output.shape)  # (32, 100, 768)
    
    Use Case:
        BERT-style models, learned position representations
    
    Reference:
        Devlin et al., "BERT: Pre-training of Deep Bidirectional Transformers" (2019)
    """
    
    def __init__(self, max_len: int, embedding_dim: int):
        self.max_len = max_len
        self.embedding_dim = embedding_dim
        
        # Initialize position embeddings
        self.position_embeddings = np.random.randn(max_len, embedding_dim) * 0.02
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass.
        
        Args:
            x: Input embeddings (batch, seq_len, embedding_dim)
        
        Returns:
            Embeddings with learned positional embeddings added
        """
        batch_size, seq_len, embedding_dim = x.shape
        
        if seq_len > self.max_len:
            raise ValueError(f"Sequence length {seq_len} exceeds max_len {self.max_len}")
        
        if embedding_dim != self.embedding_dim:
            raise ValueError(f"Expected embedding_dim {self.embedding_dim}, got {embedding_dim}")
        
        # Add position embeddings
        output = x + self.position_embeddings[:seq_len, :]
        
        return output
    
    def __call__(self, x: np.ndarray) -> np.ndarray:
        return self.forward(x)


# ============================================================================
# TOKEN TYPE EMBEDDING (SEGMENT EMBEDDING)
# ============================================================================

class TokenTypeEmbedding:
    """
    Token Type (Segment) Embeddings.
    
    Used in BERT to distinguish between different segments (e.g., sentence A vs B).
    
    Args:
        num_types: Number of token types (default: 2 for BERT)
        embedding_dim: Dimension of embeddings
    
    Example:
        >>> token_type_emb = TokenTypeEmbedding(num_types=2, embedding_dim=768)
        >>> token_type_ids = np.array([[0, 0, 0, 1, 1, 1]])  # (batch, seq_len)
        >>> output = token_type_emb.forward(token_type_ids)
        >>> print(output.shape)  # (1, 6, 768)
    
    Use Case:
        BERT, sentence pair tasks, multi-segment inputs
    
    Reference:
        Devlin et al., "BERT" (2019)
    """
    
    def __init__(self, num_types: int = 2, embedding_dim: int = 768):
        self.num_types = num_types
        self.embedding_dim = embedding_dim
        
        # Initialize token type embeddings
        self.token_type_embeddings = np.random.randn(num_types, embedding_dim) * 0.02
    
    def forward(self, token_type_ids: np.ndarray) -> np.ndarray:
        """
        Forward pass.
        
        Args:
            token_type_ids: Token type indices (batch, seq_len)
        
        Returns:
            Token type embeddings (batch, seq_len, embedding_dim)
        """
        return self.token_type_embeddings[token_type_ids]
    
    def __call__(self, token_type_ids: np.ndarray) -> np.ndarray:
        return self.forward(token_type_ids)


# ============================================================================
# CHARACTER EMBEDDING
# ============================================================================

class CharacterEmbedding:
    """
    Character-level Embeddings.
    
    Embeds individual characters, useful for handling OOV words.
    
    Args:
        num_chars: Number of unique characters
        embedding_dim: Dimension of character embeddings
        padding_idx: Index for padding character
    
    Example:
        >>> char_emb = CharacterEmbedding(num_chars=128, embedding_dim=50)
        >>> char_ids = np.random.randint(0, 128, (32, 20, 15))  # (batch, words, chars)
        >>> output = char_emb.forward(char_ids)
        >>> print(output.shape)  # (32, 20, 50)
    
    Use Case:
        Character-level models, handling rare words, morphologically rich languages
    
    Reference:
        Kim et al., "Character-Aware Neural Language Models" (2016)
    """
    
    def __init__(self, num_chars: int, embedding_dim: int, padding_idx: Optional[int] = None):
        self.num_chars = num_chars
        self.embedding_dim = embedding_dim
        self.padding_idx = padding_idx
        
        # Initialize character embeddings
        self.weight = np.random.randn(num_chars, embedding_dim) * 0.02
        
        if padding_idx is not None:
            self.weight[padding_idx] = 0.0
    
    def forward(self, char_ids: np.ndarray) -> np.ndarray:
        """
        Forward pass.
        
        Args:
            char_ids: Character indices (batch, num_words, max_word_len)
        
        Returns:
            Word embeddings from characters (batch, num_words, embedding_dim)
        """
        batch_size, num_words, max_word_len = char_ids.shape
        
        # Lookup character embeddings
        char_embeddings = self.weight[char_ids]  # (batch, num_words, max_word_len, embedding_dim)
        
        # Aggregate character embeddings (mean pooling)
        word_embeddings = np.mean(char_embeddings, axis=2)  # (batch, num_words, embedding_dim)
        
        return word_embeddings
    
    def __call__(self, char_ids: np.ndarray) -> np.ndarray:
        return self.forward(char_ids)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    
    Formula:
        cos(θ) = (a · b) / (||a|| ||b||)
    
    Args:
        a: First vector
        b: Second vector
    
    Returns:
        Cosine similarity (-1 to 1)
    
    Example:
        >>> a = np.array([1, 2, 3])
        >>> b = np.array([4, 5, 6])
        >>> sim = cosine_similarity(a, b)
        >>> print(f"Similarity: {sim:.4f}")
    """
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute Euclidean distance between two vectors.
    
    Formula:
        d = ||a - b||
    
    Args:
        a: First vector
        b: Second vector
    
    Returns:
        Euclidean distance
    """
    return np.linalg.norm(a - b)


def most_similar(embedding_matrix: np.ndarray, query_vector: np.ndarray, 
                 top_k: int = 5, exclude_idx: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Find most similar vectors to query vector.
    
    Args:
        embedding_matrix: Matrix of embeddings (vocab_size, embedding_dim)
        query_vector: Query vector (embedding_dim,)
        top_k: Number of most similar vectors to return
        exclude_idx: Index to exclude (e.g., query word itself)
    
    Returns:
        Tuple of (indices, similarities)
    
    Example:
        >>> emb = Embedding(vocab_size=10000, embedding_dim=300)
        >>> query = emb.weight[100]  # Get embedding for word at index 100
        >>> indices, sims = most_similar(emb.weight, query, top_k=5, exclude_idx=100)
        >>> print(f"Most similar indices: {indices}")
        >>> print(f"Similarities: {sims}")
    """
    # Compute cosine similarities
    norms = np.linalg.norm(embedding_matrix, axis=1, keepdims=True)
    query_norm = np.linalg.norm(query_vector)
    
    similarities = np.dot(embedding_matrix, query_vector) / (norms.flatten() * query_norm + 1e-8)
    
    # Exclude specified index
    if exclude_idx is not None:
        similarities[exclude_idx] = -np.inf
    
    # Get top-k
    top_indices = np.argsort(similarities)[::-1][:top_k]
    top_similarities = similarities[top_indices]
    
    return top_indices, top_similarities


__all__ = [
    'Embedding',
    'PositionalEncoding',
    'LearnedPositionalEmbedding',
    'TokenTypeEmbedding',
    'CharacterEmbedding',
    'cosine_similarity',
    'euclidean_distance',
    'most_similar',
]
