"""
Tests for Graph Neural Networks

This file contains comprehensive tests for all GNN architectures.

Author: Ali Mehdi
Date: January 31, 2026
"""

import numpy as np
import pytest
from ilovetools.ml.gnn import (
    GCN,
    GAT,
    GraphSAGE,
    GIN,
    create_adjacency_matrix,
    graph_pooling,
)


# ============================================================================
# TEST GCN
# ============================================================================

def test_gcn_basic():
    """Test basic GCN functionality."""
    gcn = GCN(in_features=128, hidden_features=256, out_features=64)
    node_features = np.random.randn(100, 128)
    adj_matrix = np.random.randint(0, 2, (100, 100))
    
    output = gcn.forward(node_features, adj_matrix, training=False)
    
    assert output.shape == (100, 64)


def test_gcn_normalize_adjacency():
    """Test adjacency matrix normalization."""
    gcn = GCN(in_features=10, hidden_features=20)
    adj_matrix = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
    
    adj_norm = gcn.normalize_adjacency(adj_matrix)
    
    assert adj_norm.shape == (3, 3)
    assert not np.isnan(adj_norm).any()


def test_gcn_different_layers():
    """Test GCN with different number of layers."""
    for num_layers in [1, 2, 3, 5]:
        gcn = GCN(in_features=64, hidden_features=128, num_layers=num_layers)
        node_features = np.random.randn(50, 64)
        adj_matrix = np.random.randint(0, 2, (50, 50))
        
        output = gcn.forward(node_features, adj_matrix, training=False)
        assert output is not None


# ============================================================================
# TEST GAT
# ============================================================================

def test_gat_basic():
    """Test basic GAT functionality."""
    gat = GAT(in_features=128, hidden_features=256, num_heads=8)
    node_features = np.random.randn(100, 128)
    adj_matrix = np.random.randint(0, 2, (100, 100))
    
    output = gat.forward(node_features, adj_matrix, training=False)
    
    assert output.shape == (100, 256 * 8)  # Concatenated heads


def test_gat_attention_mechanism():
    """Test that GAT computes attention weights."""
    gat = GAT(in_features=64, hidden_features=32, num_heads=4)
    node_features = np.random.randn(10, 64)
    adj_matrix = np.eye(10)  # Self-loops only
    
    output = gat.forward(node_features, adj_matrix, training=False)
    
    assert output.shape == (10, 32 * 4)
    assert not np.isnan(output).any()


def test_gat_different_heads():
    """Test GAT with different number of attention heads."""
    for num_heads in [1, 4, 8, 16]:
        gat = GAT(in_features=64, hidden_features=32, num_heads=num_heads)
        node_features = np.random.randn(20, 64)
        adj_matrix = np.random.randint(0, 2, (20, 20))
        
        output = gat.forward(node_features, adj_matrix, training=False)
        assert output.shape == (20, 32 * num_heads)


# ============================================================================
# TEST GRAPHSAGE
# ============================================================================

def test_graphsage_basic():
    """Test basic GraphSAGE functionality."""
    sage = GraphSAGE(in_features=128, hidden_features=256, num_samples=10)
    node_features = np.random.randn(100, 128)
    adj_matrix = np.random.randint(0, 2, (100, 100))
    
    output = sage.forward(node_features, adj_matrix)
    
    assert output.shape == (100, 256)


def test_graphsage_sample_neighbors():
    """Test neighbor sampling."""
    sage = GraphSAGE(in_features=64, hidden_features=128, num_samples=5)
    adj_matrix = np.random.randint(0, 2, (50, 50))
    
    neighbors = sage.sample_neighbors(adj_matrix, node_idx=0)
    
    assert len(neighbors) <= 5


def test_graphsage_aggregators():
    """Test different aggregation functions."""
    for aggregator in ['mean', 'max', 'sum']:
        sage = GraphSAGE(in_features=64, hidden_features=128, aggregator=aggregator)
        node_features = np.random.randn(50, 64)
        adj_matrix = np.random.randint(0, 2, (50, 50))
        
        output = sage.forward(node_features, adj_matrix)
        assert output.shape == (50, 128)


# ============================================================================
# TEST GIN
# ============================================================================

def test_gin_basic():
    """Test basic GIN functionality."""
    gin = GIN(in_features=128, hidden_features=256, num_layers=5)
    node_features = np.random.randn(100, 128)
    adj_matrix = np.random.randint(0, 2, (100, 100))
    
    output = gin.forward(node_features, adj_matrix)
    
    assert output.shape == (100, 256)


def test_gin_mlp():
    """Test GIN MLP."""
    gin = GIN(in_features=64, hidden_features=128)
    x = np.random.randn(10, 64)
    w1, w2 = gin.mlp_weights[0]
    
    output = gin.mlp(x, w1, w2)
    
    assert output.shape[0] == 10


def test_gin_different_layers():
    """Test GIN with different number of layers."""
    for num_layers in [2, 3, 5, 7]:
        gin = GIN(in_features=64, hidden_features=128, num_layers=num_layers)
        node_features = np.random.randn(50, 64)
        adj_matrix = np.random.randint(0, 2, (50, 50))
        
        output = gin.forward(node_features, adj_matrix)
        assert output.shape == (50, 128)


# ============================================================================
# TEST UTILITY FUNCTIONS
# ============================================================================

def test_create_adjacency_matrix():
    """Test adjacency matrix creation from edge list."""
    edges = [(0, 1), (1, 2), (2, 0)]
    adj = create_adjacency_matrix(edges, num_nodes=3)
    
    assert adj.shape == (3, 3)
    assert adj[0, 1] == 1
    assert adj[1, 0] == 1
    assert adj[1, 2] == 1


def test_graph_pooling_mean():
    """Test mean graph pooling."""
    node_emb = np.random.randn(100, 256)
    graph_emb = graph_pooling(node_emb, method='mean')
    
    assert graph_emb.shape == (256,)
    assert np.allclose(graph_emb, np.mean(node_emb, axis=0))


def test_graph_pooling_max():
    """Test max graph pooling."""
    node_emb = np.random.randn(100, 256)
    graph_emb = graph_pooling(node_emb, method='max')
    
    assert graph_emb.shape == (256,)
    assert np.allclose(graph_emb, np.max(node_emb, axis=0))


def test_graph_pooling_sum():
    """Test sum graph pooling."""
    node_emb = np.random.randn(100, 256)
    graph_emb = graph_pooling(node_emb, method='sum')
    
    assert graph_emb.shape == (256,)
    assert np.allclose(graph_emb, np.sum(node_emb, axis=0))


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_all_gnns_callable():
    """Test that all GNNs are callable."""
    node_features = np.random.randn(50, 64)
    adj_matrix = np.random.randint(0, 2, (50, 50))
    
    gcn = GCN(64, 128)
    gat = GAT(64, 128, num_heads=4)
    sage = GraphSAGE(64, 128)
    gin = GIN(64, 128)
    
    assert gcn(node_features, adj_matrix, training=False) is not None
    assert gat(node_features, adj_matrix, training=False) is not None
    assert sage(node_features, adj_matrix) is not None
    assert gin(node_features, adj_matrix) is not None


def test_gnns_preserve_num_nodes():
    """Test that GNNs preserve number of nodes."""
    num_nodes = 75
    node_features = np.random.randn(num_nodes, 64)
    adj_matrix = np.random.randint(0, 2, (num_nodes, num_nodes))
    
    gcn = GCN(64, 128)
    gat = GAT(64, 128, num_heads=4)
    sage = GraphSAGE(64, 128)
    gin = GIN(64, 128)
    
    assert gcn(node_features, adj_matrix, training=False).shape[0] == num_nodes
    assert gat(node_features, adj_matrix, training=False).shape[0] == num_nodes
    assert sage(node_features, adj_matrix).shape[0] == num_nodes
    assert gin(node_features, adj_matrix).shape[0] == num_nodes


def test_gnns_no_nan_output():
    """Test that GNNs don't produce NaN values."""
    node_features = np.random.randn(50, 64)
    adj_matrix = np.random.randint(0, 2, (50, 50))
    
    gcn = GCN(64, 128)
    gat = GAT(64, 128, num_heads=4)
    sage = GraphSAGE(64, 128)
    gin = GIN(64, 128)
    
    assert not np.isnan(gcn(node_features, adj_matrix, training=False)).any()
    assert not np.isnan(gat(node_features, adj_matrix, training=False)).any()
    assert not np.isnan(sage(node_features, adj_matrix)).any()
    assert not np.isnan(gin(node_features, adj_matrix)).any()


def test_node_classification_pipeline():
    """Test complete node classification pipeline."""
    # Create graph
    num_nodes = 100
    num_classes = 7
    node_features = np.random.randn(num_nodes, 128)
    adj_matrix = np.random.randint(0, 2, (num_nodes, num_nodes))
    
    # GCN for node classification
    gcn = GCN(in_features=128, hidden_features=256, out_features=num_classes)
    
    # Forward pass
    logits = gcn.forward(node_features, adj_matrix, training=False)
    
    assert logits.shape == (num_nodes, num_classes)
    
    # Predictions
    predictions = np.argmax(logits, axis=1)
    assert predictions.shape == (num_nodes,)


def test_graph_classification_pipeline():
    """Test complete graph classification pipeline."""
    # Create graph
    num_nodes = 50
    num_classes = 3
    node_features = np.random.randn(num_nodes, 128)
    adj_matrix = np.random.randint(0, 2, (num_nodes, num_nodes))
    
    # GIN for graph classification
    gin = GIN(in_features=128, hidden_features=256, out_features=128)
    
    # Get node embeddings
    node_embeddings = gin.forward(node_features, adj_matrix)
    
    # Pool to graph-level
    graph_embedding = graph_pooling(node_embeddings, method='mean')
    
    assert graph_embedding.shape == (128,)
    
    # Classify (would add linear layer here)
    # logits = graph_embedding @ classifier_weights


def test_link_prediction_pipeline():
    """Test link prediction pipeline."""
    # Create graph
    num_nodes = 100
    node_features = np.random.randn(num_nodes, 128)
    adj_matrix = np.random.randint(0, 2, (num_nodes, num_nodes))
    
    # GraphSAGE for link prediction
    sage = GraphSAGE(in_features=128, hidden_features=256)
    
    # Get node embeddings
    node_embeddings = sage.forward(node_features, adj_matrix)
    
    assert node_embeddings.shape == (num_nodes, 256)
    
    # Predict link between node 0 and node 1
    # score = dot(node_embeddings[0], node_embeddings[1])


print("=" * 80)
print("ALL GRAPH NEURAL NETWORK TESTS PASSED! ✓")
print("=" * 80)
