"""
Graph Neural Networks Suite

This module implements various Graph Neural Network (GNN) architectures for processing
graph-structured data. GNNs learn node embeddings by aggregating information from
neighboring nodes through message passing.

Implemented GNN Types:
1. GCN - Graph Convolutional Network
2. GAT - Graph Attention Network
3. GraphSAGE - Graph Sample and Aggregate
4. GIN - Graph Isomorphism Network
5. MessagePassing - Base message passing framework

Key Benefits:
- Process graph-structured data (social networks, molecules, knowledge graphs)
- Node classification, link prediction, graph classification
- Capture relational information
- Scalable to large graphs
- Inductive learning on unseen graphs

References:
- GCN: Kipf & Welling, "Semi-Supervised Classification with Graph Convolutional Networks" (2017)
- GAT: Veličković et al., "Graph Attention Networks" (2018)
- GraphSAGE: Hamilton et al., "Inductive Representation Learning on Large Graphs" (2017)
- GIN: Xu et al., "How Powerful are Graph Neural Networks?" (2019)

Author: Ali Mehdi
Date: January 31, 2026
"""

import numpy as np
from typing import Optional, Tuple, List


# ============================================================================
# GRAPH CONVOLUTIONAL NETWORK (GCN)
# ============================================================================

class GCN:
    """
    Graph Convolutional Network.
    
    Aggregates neighbor features with equal weights using normalized adjacency matrix.
    
    Formula:
        H^(l+1) = σ(D^(-1/2) A D^(-1/2) H^(l) W^(l))
        
        where:
        - A: Adjacency matrix with self-loops (A + I)
        - D: Degree matrix
        - H^(l): Node features at layer l
        - W^(l): Learnable weight matrix
        - σ: Activation function
    
    Args:
        in_features: Input feature dimension
        hidden_features: Hidden feature dimension
        out_features: Output feature dimension (optional, defaults to hidden_features)
        num_layers: Number of GCN layers (default: 2)
        dropout: Dropout rate (default: 0.5)
    
    Example:
        >>> gcn = GCN(in_features=128, hidden_features=256, out_features=64)
        >>> node_features = np.random.randn(100, 128)  # 100 nodes, 128 features
        >>> adj_matrix = np.random.randint(0, 2, (100, 100))  # Adjacency matrix
        >>> output = gcn.forward(node_features, adj_matrix)
        >>> print(output.shape)  # (100, 64)
    
    Use Case:
        Node classification, semi-supervised learning, citation networks
    
    Reference:
        Kipf & Welling, "Semi-Supervised Classification with GCN" (2017)
    """
    
    def __init__(self, in_features: int, hidden_features: int, 
                 out_features: Optional[int] = None,
                 num_layers: int = 2, dropout: float = 0.5):
        self.in_features = in_features
        self.hidden_features = hidden_features
        self.out_features = out_features or hidden_features
        self.num_layers = num_layers
        self.dropout = dropout
        
        # Initialize weights for each layer
        self.weights = []
        
        # First layer
        self.weights.append(
            np.random.randn(in_features, hidden_features) * np.sqrt(2.0 / in_features)
        )
        
        # Hidden layers
        for _ in range(num_layers - 2):
            self.weights.append(
                np.random.randn(hidden_features, hidden_features) * np.sqrt(2.0 / hidden_features)
            )
        
        # Output layer
        if num_layers > 1:
            self.weights.append(
                np.random.randn(hidden_features, self.out_features) * np.sqrt(2.0 / hidden_features)
            )
    
    def normalize_adjacency(self, adj_matrix: np.ndarray) -> np.ndarray:
        """
        Normalize adjacency matrix with self-loops.
        
        Formula:
            A_norm = D^(-1/2) (A + I) D^(-1/2)
        """
        # Add self-loops
        adj_with_self_loops = adj_matrix + np.eye(adj_matrix.shape[0])
        
        # Compute degree matrix
        degree = np.sum(adj_with_self_loops, axis=1)
        degree_inv_sqrt = np.power(degree, -0.5)
        degree_inv_sqrt[np.isinf(degree_inv_sqrt)] = 0.0
        
        # D^(-1/2)
        D_inv_sqrt = np.diag(degree_inv_sqrt)
        
        # Normalize: D^(-1/2) A D^(-1/2)
        adj_normalized = D_inv_sqrt @ adj_with_self_loops @ D_inv_sqrt
        
        return adj_normalized
    
    def forward(self, node_features: np.ndarray, adj_matrix: np.ndarray, 
                training: bool = True) -> np.ndarray:
        """
        Forward pass.
        
        Args:
            node_features: Node feature matrix (num_nodes, in_features)
            adj_matrix: Adjacency matrix (num_nodes, num_nodes)
            training: Whether in training mode (apply dropout)
        
        Returns:
            Node embeddings (num_nodes, out_features)
        """
        # Normalize adjacency matrix
        adj_norm = self.normalize_adjacency(adj_matrix)
        
        h = node_features
        
        # Apply GCN layers
        for i, weight in enumerate(self.weights):
            # Graph convolution: A_norm @ H @ W
            h = adj_norm @ h @ weight
            
            # Apply ReLU activation (except last layer)
            if i < len(self.weights) - 1:
                h = np.maximum(0, h)  # ReLU
                
                # Apply dropout
                if training and self.dropout > 0:
                    mask = np.random.binomial(1, 1 - self.dropout, size=h.shape)
                    h = h * mask / (1 - self.dropout)
        
        return h
    
    def __call__(self, node_features: np.ndarray, adj_matrix: np.ndarray, 
                 training: bool = True) -> np.ndarray:
        return self.forward(node_features, adj_matrix, training)


# ============================================================================
# GRAPH ATTENTION NETWORK (GAT)
# ============================================================================

class GAT:
    """
    Graph Attention Network.
    
    Uses attention mechanism to weight neighbor contributions dynamically.
    
    Formula:
        α_ij = softmax(LeakyReLU(a^T [W h_i || W h_j]))
        h_i' = σ(Σ_j α_ij W h_j)
        
        where:
        - α_ij: Attention coefficient from node j to node i
        - W: Learnable weight matrix
        - a: Attention vector
        - ||: Concatenation
    
    Args:
        in_features: Input feature dimension
        hidden_features: Hidden feature dimension per head
        out_features: Output feature dimension (optional)
        num_heads: Number of attention heads (default: 8)
        dropout: Dropout rate (default: 0.6)
        alpha: LeakyReLU negative slope (default: 0.2)
    
    Example:
        >>> gat = GAT(in_features=128, hidden_features=256, num_heads=8)
        >>> node_features = np.random.randn(100, 128)
        >>> adj_matrix = np.random.randint(0, 2, (100, 100))
        >>> output = gat.forward(node_features, adj_matrix)
        >>> print(output.shape)  # (100, 256*8) - concatenated heads
    
    Use Case:
        Node classification with varying neighbor importance, citation networks
    
    Reference:
        Veličković et al., "Graph Attention Networks" (2018)
    """
    
    def __init__(self, in_features: int, hidden_features: int,
                 out_features: Optional[int] = None,
                 num_heads: int = 8, dropout: float = 0.6, alpha: float = 0.2):
        self.in_features = in_features
        self.hidden_features = hidden_features
        self.out_features = out_features or (hidden_features * num_heads)
        self.num_heads = num_heads
        self.dropout = dropout
        self.alpha = alpha
        
        # Initialize weights for each attention head
        self.W = []
        self.a = []
        
        for _ in range(num_heads):
            # Weight matrix for features
            self.W.append(
                np.random.randn(in_features, hidden_features) * np.sqrt(2.0 / in_features)
            )
            # Attention vector
            self.a.append(
                np.random.randn(2 * hidden_features) * 0.01
            )
    
    def leaky_relu(self, x: np.ndarray) -> np.ndarray:
        """LeakyReLU activation."""
        return np.where(x > 0, x, self.alpha * x)
    
    def attention(self, h: np.ndarray, adj_matrix: np.ndarray, 
                  W: np.ndarray, a: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute attention coefficients.
        
        Returns:
            Tuple of (attention_weights, aggregated_features)
        """
        num_nodes = h.shape[0]
        
        # Transform features: h' = W @ h
        h_transformed = h @ W  # (num_nodes, hidden_features)
        
        # Compute attention scores
        attention_scores = np.zeros((num_nodes, num_nodes))
        
        for i in range(num_nodes):
            for j in range(num_nodes):
                if adj_matrix[i, j] > 0 or i == j:  # Only for neighbors and self
                    # Concatenate features
                    concat = np.concatenate([h_transformed[i], h_transformed[j]])
                    # Compute attention score
                    attention_scores[i, j] = np.dot(a, concat)
        
        # Apply LeakyReLU
        attention_scores = self.leaky_relu(attention_scores)
        
        # Mask non-neighbors
        mask = (adj_matrix + np.eye(num_nodes)) > 0
        attention_scores = np.where(mask, attention_scores, -1e9)
        
        # Softmax normalization
        attention_weights = np.exp(attention_scores - np.max(attention_scores, axis=1, keepdims=True))
        attention_weights = attention_weights / (np.sum(attention_weights, axis=1, keepdims=True) + 1e-8)
        
        # Aggregate features
        aggregated = attention_weights @ h_transformed
        
        return attention_weights, aggregated
    
    def forward(self, node_features: np.ndarray, adj_matrix: np.ndarray,
                training: bool = True) -> np.ndarray:
        """
        Forward pass.
        
        Args:
            node_features: Node feature matrix (num_nodes, in_features)
            adj_matrix: Adjacency matrix (num_nodes, num_nodes)
            training: Whether in training mode
        
        Returns:
            Node embeddings (num_nodes, out_features)
        """
        # Multi-head attention
        head_outputs = []
        
        for W, a in zip(self.W, self.a):
            _, aggregated = self.attention(node_features, adj_matrix, W, a)
            
            # Apply dropout
            if training and self.dropout > 0:
                mask = np.random.binomial(1, 1 - self.dropout, size=aggregated.shape)
                aggregated = aggregated * mask / (1 - self.dropout)
            
            head_outputs.append(aggregated)
        
        # Concatenate or average heads
        output = np.concatenate(head_outputs, axis=1)  # (num_nodes, hidden_features * num_heads)
        
        # Apply ELU activation
        output = np.where(output > 0, output, np.exp(output) - 1)
        
        return output
    
    def __call__(self, node_features: np.ndarray, adj_matrix: np.ndarray,
                 training: bool = True) -> np.ndarray:
        return self.forward(node_features, adj_matrix, training)


# ============================================================================
# GRAPHSAGE
# ============================================================================

class GraphSAGE:
    """
    Graph Sample and Aggregate.
    
    Samples fixed-size neighborhoods and aggregates features for scalability.
    
    Formula:
        h_N(v) = AGGREGATE({h_u, ∀u ∈ N(v)})
        h_v' = σ(W · CONCAT(h_v, h_N(v)))
        
        where:
        - N(v): Sampled neighborhood of node v
        - AGGREGATE: Mean, max, or LSTM aggregation
        - CONCAT: Concatenation
    
    Args:
        in_features: Input feature dimension
        hidden_features: Hidden feature dimension
        out_features: Output feature dimension (optional)
        num_layers: Number of GraphSAGE layers (default: 2)
        aggregator: Aggregation function ('mean', 'max', 'sum') (default: 'mean')
        num_samples: Number of neighbors to sample per layer (default: 25)
    
    Example:
        >>> sage = GraphSAGE(in_features=128, hidden_features=256, num_samples=10)
        >>> node_features = np.random.randn(100, 128)
        >>> adj_matrix = np.random.randint(0, 2, (100, 100))
        >>> output = sage.forward(node_features, adj_matrix)
        >>> print(output.shape)  # (100, 256)
    
    Use Case:
        Large-scale graphs, inductive learning, unseen nodes
    
    Reference:
        Hamilton et al., "Inductive Representation Learning on Large Graphs" (2017)
    """
    
    def __init__(self, in_features: int, hidden_features: int,
                 out_features: Optional[int] = None,
                 num_layers: int = 2, aggregator: str = 'mean',
                 num_samples: int = 25):
        self.in_features = in_features
        self.hidden_features = hidden_features
        self.out_features = out_features or hidden_features
        self.num_layers = num_layers
        self.aggregator = aggregator
        self.num_samples = num_samples
        
        # Initialize weights
        self.weights = []
        
        # First layer
        self.weights.append(
            np.random.randn(in_features * 2, hidden_features) * np.sqrt(2.0 / (in_features * 2))
        )
        
        # Hidden layers
        for _ in range(num_layers - 2):
            self.weights.append(
                np.random.randn(hidden_features * 2, hidden_features) * np.sqrt(2.0 / (hidden_features * 2))
            )
        
        # Output layer
        if num_layers > 1:
            self.weights.append(
                np.random.randn(hidden_features * 2, self.out_features) * np.sqrt(2.0 / (hidden_features * 2))
            )
    
    def sample_neighbors(self, adj_matrix: np.ndarray, node_idx: int) -> np.ndarray:
        """Sample fixed number of neighbors for a node."""
        neighbors = np.where(adj_matrix[node_idx] > 0)[0]
        
        if len(neighbors) == 0:
            return np.array([node_idx])  # Self-loop if no neighbors
        
        if len(neighbors) <= self.num_samples:
            return neighbors
        
        # Random sampling
        return np.random.choice(neighbors, size=self.num_samples, replace=False)
    
    def aggregate(self, neighbor_features: np.ndarray) -> np.ndarray:
        """Aggregate neighbor features."""
        if self.aggregator == 'mean':
            return np.mean(neighbor_features, axis=0)
        elif self.aggregator == 'max':
            return np.max(neighbor_features, axis=0)
        elif self.aggregator == 'sum':
            return np.sum(neighbor_features, axis=0)
        else:
            raise ValueError(f"Unknown aggregator: {self.aggregator}")
    
    def forward(self, node_features: np.ndarray, adj_matrix: np.ndarray) -> np.ndarray:
        """
        Forward pass.
        
        Args:
            node_features: Node feature matrix (num_nodes, in_features)
            adj_matrix: Adjacency matrix (num_nodes, num_nodes)
        
        Returns:
            Node embeddings (num_nodes, out_features)
        """
        num_nodes = node_features.shape[0]
        h = node_features
        
        for weight in self.weights:
            h_new = np.zeros((num_nodes, weight.shape[1]))
            
            for i in range(num_nodes):
                # Sample neighbors
                neighbors = self.sample_neighbors(adj_matrix, i)
                
                # Aggregate neighbor features
                neighbor_h = h[neighbors]
                aggregated = self.aggregate(neighbor_h)
                
                # Concatenate self and aggregated neighbor features
                concat = np.concatenate([h[i], aggregated])
                
                # Transform
                h_new[i] = concat @ weight
            
            # Apply ReLU
            h = np.maximum(0, h_new)
            
            # L2 normalization
            norms = np.linalg.norm(h, axis=1, keepdims=True)
            h = h / (norms + 1e-8)
        
        return h
    
    def __call__(self, node_features: np.ndarray, adj_matrix: np.ndarray) -> np.ndarray:
        return self.forward(node_features, adj_matrix)


# ============================================================================
# GRAPH ISOMORPHISM NETWORK (GIN)
# ============================================================================

class GIN:
    """
    Graph Isomorphism Network.
    
    Most expressive GNN architecture, uses MLPs to distinguish non-isomorphic graphs.
    
    Formula:
        h_v^(k) = MLP^(k)((1 + ε^(k)) · h_v^(k-1) + Σ_{u∈N(v)} h_u^(k-1))
        
        where:
        - ε: Learnable parameter or fixed scalar
        - MLP: Multi-layer perceptron
        - N(v): Neighbors of node v
    
    Args:
        in_features: Input feature dimension
        hidden_features: Hidden feature dimension
        out_features: Output feature dimension (optional)
        num_layers: Number of GIN layers (default: 5)
        epsilon: Initial epsilon value (default: 0.0)
        learn_epsilon: Whether epsilon is learnable (default: True)
    
    Example:
        >>> gin = GIN(in_features=128, hidden_features=256, num_layers=5)
        >>> node_features = np.random.randn(100, 128)
        >>> adj_matrix = np.random.randint(0, 2, (100, 100))
        >>> output = gin.forward(node_features, adj_matrix)
        >>> print(output.shape)  # (100, 256)
    
    Use Case:
        Graph classification, molecular property prediction, high expressiveness needed
    
    Reference:
        Xu et al., "How Powerful are Graph Neural Networks?" (2019)
    """
    
    def __init__(self, in_features: int, hidden_features: int,
                 out_features: Optional[int] = None,
                 num_layers: int = 5, epsilon: float = 0.0,
                 learn_epsilon: bool = True):
        self.in_features = in_features
        self.hidden_features = hidden_features
        self.out_features = out_features or hidden_features
        self.num_layers = num_layers
        self.epsilon = epsilon if not learn_epsilon else np.random.randn() * 0.01
        self.learn_epsilon = learn_epsilon
        
        # Initialize MLP weights for each layer
        self.mlp_weights = []
        
        for i in range(num_layers):
            layer_in = in_features if i == 0 else hidden_features
            layer_out = self.out_features if i == num_layers - 1 else hidden_features
            
            # Two-layer MLP
            w1 = np.random.randn(layer_in, hidden_features) * np.sqrt(2.0 / layer_in)
            w2 = np.random.randn(hidden_features, layer_out) * np.sqrt(2.0 / hidden_features)
            
            self.mlp_weights.append((w1, w2))
    
    def mlp(self, x: np.ndarray, w1: np.ndarray, w2: np.ndarray) -> np.ndarray:
        """Two-layer MLP."""
        h = np.maximum(0, x @ w1)  # ReLU
        return h @ w2
    
    def forward(self, node_features: np.ndarray, adj_matrix: np.ndarray) -> np.ndarray:
        """
        Forward pass.
        
        Args:
            node_features: Node feature matrix (num_nodes, in_features)
            adj_matrix: Adjacency matrix (num_nodes, num_nodes)
        
        Returns:
            Node embeddings (num_nodes, out_features)
        """
        h = node_features
        
        for w1, w2 in self.mlp_weights:
            # Aggregate neighbors
            neighbor_sum = adj_matrix @ h
            
            # Add self features with epsilon
            h_new = (1 + self.epsilon) * h + neighbor_sum
            
            # Apply MLP
            h = self.mlp(h_new, w1, w2)
            
            # Apply ReLU (except last layer)
            if (w1, w2) != self.mlp_weights[-1]:
                h = np.maximum(0, h)
        
        return h
    
    def __call__(self, node_features: np.ndarray, adj_matrix: np.ndarray) -> np.ndarray:
        return self.forward(node_features, adj_matrix)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_adjacency_matrix(edges: List[Tuple[int, int]], num_nodes: int) -> np.ndarray:
    """
    Create adjacency matrix from edge list.
    
    Args:
        edges: List of (source, target) tuples
        num_nodes: Total number of nodes
    
    Returns:
        Adjacency matrix (num_nodes, num_nodes)
    
    Example:
        >>> edges = [(0, 1), (1, 2), (2, 0)]
        >>> adj = create_adjacency_matrix(edges, num_nodes=3)
        >>> print(adj)
    """
    adj_matrix = np.zeros((num_nodes, num_nodes))
    
    for src, tgt in edges:
        adj_matrix[src, tgt] = 1
        adj_matrix[tgt, src] = 1  # Undirected graph
    
    return adj_matrix


def graph_pooling(node_embeddings: np.ndarray, method: str = 'mean') -> np.ndarray:
    """
    Pool node embeddings to graph-level representation.
    
    Args:
        node_embeddings: Node embeddings (num_nodes, features)
        method: Pooling method ('mean', 'max', 'sum')
    
    Returns:
        Graph embedding (features,)
    
    Example:
        >>> node_emb = np.random.randn(100, 256)
        >>> graph_emb = graph_pooling(node_emb, method='mean')
        >>> print(graph_emb.shape)  # (256,)
    """
    if method == 'mean':
        return np.mean(node_embeddings, axis=0)
    elif method == 'max':
        return np.max(node_embeddings, axis=0)
    elif method == 'sum':
        return np.sum(node_embeddings, axis=0)
    else:
        raise ValueError(f"Unknown pooling method: {method}")


__all__ = [
    'GCN',
    'GAT',
    'GraphSAGE',
    'GIN',
    'create_adjacency_matrix',
    'graph_pooling',
]
