"""Pure Python clustering algorithms - fully portable, no Cypher dependencies.

This module provides community detection algorithms that work on any graph
represented as nodes + weighted edges. All implementations are pure Python
and do not depend on any specific graph database backend.

Algorithms:
- louvain_partition: Hierarchical Louvain community detection
- greedy_modularity: NetworkX greedy modularity optimization
- cluster_models: Unified interface with algorithm selection
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set, Tuple

import networkx as nx


def louvain_partition(
    nodes: List[str], weighted_edges: List[Tuple[str, str, float]]
) -> Dict[str, int]:
    """Louvain community detection algorithm (pure Python implementation).

    Hierarchical community detection using greedy modularity optimization.
    This is a complete implementation extracted from KuzuAdapter for portability.

    Args:
        nodes: List of node IDs
        weighted_edges: List of (source, target, weight) tuples

    Returns:
        Dictionary mapping node ID -> community ID
    """
    if not nodes:
        return {}

    if not weighted_edges:
        return {node: idx for idx, node in enumerate(nodes)}

    total_weight = sum(w for _, _, w in weighted_edges)
    if total_weight <= 0:
        return {node: idx for idx, node in enumerate(nodes)}

    # Initialize hierarchical clustering
    current_nodes = nodes
    current_edges = weighted_edges
    membership: Dict[int, Set[str]] = {idx: {node} for idx, node in enumerate(nodes)}

    while True:
        partition = _louvain_first_phase(current_nodes, current_edges)
        unique_comms = set(partition.values())

        # Stop if no improvement
        if len(unique_comms) == len(current_nodes):
            break

        # Aggregate graph by communities
        new_edges: Dict[Tuple[int, int], float] = defaultdict(float)
        for u, v, w in current_edges:
            cu = partition[u]
            cv = partition[v]
            new_edges[(cu, cv)] += w

        # Update membership
        new_membership: Dict[int, Set[str]] = defaultdict(set)
        for node, comm in partition.items():
            new_membership[comm].update(membership.get(node, {node}))

        current_nodes = sorted(new_membership.keys())
        current_edges = [(cu, cv, weight) for (cu, cv), weight in new_edges.items()]
        membership = new_membership

    # Compose final partition over original nodes
    groups: List[List[str]] = []
    for members in membership.values():
        groups.append(sorted(members))
    groups.sort(key=lambda m: (m[0] if m else "", len(m)))

    final_partition: Dict[str, int] = {}
    for idx, members in enumerate(groups):
        for member in members:
            final_partition[member] = idx

    return final_partition


def _louvain_first_phase(
    current_nodes: List[str], edges: List[Tuple[str, str, float]]
) -> Dict[str, int]:
    """Single phase of Louvain: greedy modularity optimization.

    This is an internal helper function for louvain_partition.

    Args:
        current_nodes: List of node IDs in current level
        edges: List of (source, target, weight) tuples

    Returns:
        Dictionary mapping node ID -> community ID
    """
    if not current_nodes:
        return {}

    # Build adjacency
    local_adj: Dict[str, Dict[str, float]] = {node: {} for node in current_nodes}
    local_total = 0.0
    for u, v, w in edges:
        if u not in local_adj:
            local_adj[u] = {}
        if v not in local_adj:
            local_adj[v] = {}
        if u == v:
            local_adj[u][u] = local_adj[u].get(u, 0.0) + w
        else:
            local_adj[u][v] = local_adj[u].get(v, 0.0) + w
            local_adj[v][u] = local_adj[v].get(u, 0.0) + w
        local_total += w

    if local_total <= 0:
        return {node: idx for idx, node in enumerate(current_nodes)}

    local_m2 = 2.0 * local_total
    node_degree = {node: sum(neigh.values()) for node, neigh in local_adj.items()}

    # Initialize each node in its own community
    communities: Dict[str, int] = {node: idx for idx, node in enumerate(current_nodes)}
    comm_weight: Dict[int, float] = {
        communities[node]: node_degree[node] for node in current_nodes
    }
    comm_internal: Dict[int, float] = {
        communities[node]: local_adj[node].get(node, 0.0) for node in current_nodes
    }

    # Iterative optimization
    changed = True
    order = list(current_nodes)
    while changed:
        changed = False
        for node in order:
            node_comm = communities[node]
            node_deg = node_degree.get(node, 0.0)
            neighbors = local_adj.get(node, {})

            # Calculate weight to each neighboring community
            neigh_comm_weight: Dict[int, float] = defaultdict(float)
            for neighbor, weight in neighbors.items():
                neighbor_comm = communities.get(neighbor)
                if neighbor_comm is not None:
                    neigh_comm_weight[neighbor_comm] += weight

            self_loop = neighbors.get(node, 0.0)

            # Remove node from current community
            comm_weight[node_comm] -= node_deg
            comm_internal[node_comm] -= (
                2.0 * (neigh_comm_weight.get(node_comm, 0.0) - self_loop) + self_loop
            )
            communities[node] = -1

            # Find best community
            best_comm = node_comm
            best_gain = 0.0

            for candidate_comm, weight_in in neigh_comm_weight.items():
                gain = weight_in - (comm_weight[candidate_comm] * node_deg) / local_m2
                if gain > best_gain + 1e-12:
                    best_gain = gain
                    best_comm = candidate_comm

            # Assign to best community
            communities[node] = best_comm
            comm_weight[best_comm] += node_deg
            weight_to_comm = neigh_comm_weight.get(best_comm, 0.0)
            if best_comm == node_comm:
                weight_to_comm -= self_loop
            comm_internal[best_comm] += 2.0 * weight_to_comm + self_loop

            if best_comm != node_comm:
                changed = True

    # Renumber communities densely
    comm_id_map: Dict[int, int] = {}
    next_id = 0
    for node in current_nodes:
        comm = communities[node]
        if comm not in comm_id_map:
            comm_id_map[comm] = next_id
            next_id += 1
        communities[node] = comm_id_map[comm]

    return communities


def greedy_modularity(
    nodes: List[str], weighted_edges: List[Tuple[str, str, float]]
) -> Dict[str, int]:
    """NetworkX greedy modularity clustering.

    Uses NetworkX's built-in greedy modularity communities algorithm.
    This is generally faster than Louvain but may produce slightly
    lower quality clusters.

    Args:
        nodes: List of node IDs
        weighted_edges: List of (source, target, weight) tuples

    Returns:
        Dictionary mapping node ID -> community ID
    """
    if not nodes:
        return {}

    # Build NetworkX graph
    G = nx.Graph()
    G.add_nodes_from(nodes)
    for u, v, w in weighted_edges:
        if w > 0:  # Only add positive-weight edges
            G.add_edge(u, v, weight=w)

    # Run greedy modularity clustering
    communities = nx.algorithms.community.greedy_modularity_communities(
        G, weight="weight"
    )

    # Convert to partition dict
    partition: Dict[str, int] = {}
    for cluster_id, community in enumerate(communities):
        for node in community:
            partition[node] = cluster_id

    return partition


def cluster_models(
    nodes: List[str],
    weighted_edges: List[Tuple[str, str, float]],
    method: str = "greedy",
    resolution: float = 1.0,
) -> Dict[int, List[str]]:
    """Unified clustering interface with algorithm selection.

    This is the main entry point for clustering. It handles algorithm
    selection, executes clustering, and returns clusters grouped by ID.

    Args:
        nodes: List of model IDs to cluster
        weighted_edges: List of (source, target, weight) tuples representing join edges
        method: Algorithm to use - "greedy" (NetworkX) or "louvain" (pure Python)
        resolution: Resolution parameter (currently only used for Leiden if implemented)

    Returns:
        Dictionary mapping cluster_id -> list of model IDs, sorted by cluster size

    Raises:
        ValueError: If unknown method specified
    """
    if not nodes:
        return {}

    # Select and run algorithm
    if method == "louvain":
        partition = louvain_partition(nodes, weighted_edges)
    elif method == "greedy":
        partition = greedy_modularity(nodes, weighted_edges)
    else:
        raise ValueError(
            f"Unknown clustering method: {method}. Choose 'louvain' or 'greedy'"
        )

    # Group nodes by cluster
    clusters: Dict[int, List[str]] = defaultdict(list)
    for node, cluster_id in partition.items():
        clusters[cluster_id].append(node)

    # Sort clusters by size (descending), then by smallest member ID
    sorted_clusters = {
        new_id: sorted(members)
        for new_id, (_, members) in enumerate(
            sorted(clusters.items(), key=lambda x: (-len(x[1]), min(x[1]) if x[1] else ""))
        )
    }

    return sorted_clusters


__all__ = ["louvain_partition", "greedy_modularity", "cluster_models"]
