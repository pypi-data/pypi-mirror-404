"""MST-based clustering for domain classification."""

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import minimum_spanning_tree
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


@dataclass
class Cluster:
    """A cluster of text spans."""

    cluster_id: int
    member_indices: list[int]
    centroid: Optional[np.ndarray] = None

    @property
    def size(self) -> int:
        return len(self.member_indices)

    def __repr__(self) -> str:
        return f"Cluster(id={self.cluster_id}, size={self.size})"


class MSTClustering:
    """Minimum Spanning Tree based clustering.

    This clustering approach:
    1. Computes pairwise cosine similarity matrix
    2. Builds MST on the similarity graph
    3. Cuts edges below threshold to form clusters

    This is more stable than HDBSCAN and doesn't require
    hyperparameter tuning for different documents.
    """

    def __init__(
        self,
        threshold_std_multiplier: float = 1.5,
        min_cluster_size: int = 1,
    ):
        """Initialize MST clustering.

        Args:
            threshold_std_multiplier: Cut edges at mean - multiplier * std
            min_cluster_size: Minimum members per cluster
        """
        self.threshold_std_multiplier = threshold_std_multiplier
        self.min_cluster_size = min_cluster_size

    def cluster(self, embeddings: np.ndarray) -> list[Cluster]:
        """Cluster embeddings using MST approach.

        Args:
            embeddings: Array of shape (n, dim)

        Returns:
            List of Cluster objects
        """
        n = len(embeddings)
        if n == 0:
            return []
        if n == 1:
            return [Cluster(cluster_id=0, member_indices=[0], centroid=embeddings[0])]

        # Step 1: Compute similarity matrix
        similarities = cosine_similarity(embeddings)

        # Convert to distance (1 - similarity)
        distances = 1 - similarities
        np.fill_diagonal(distances, 0)

        # Step 2: Build MST
        # scipy expects a distance matrix for MST
        distance_sparse = csr_matrix(distances)
        mst = minimum_spanning_tree(distance_sparse)

        # Step 3: Compute adaptive threshold
        mst_weights = mst.data
        if len(mst_weights) == 0:
            # All points are identical
            return [
                Cluster(
                    cluster_id=0,
                    member_indices=list(range(n)),
                    centroid=embeddings.mean(axis=0),
                )
            ]

        threshold = np.mean(mst_weights) + self.threshold_std_multiplier * np.std(mst_weights)
        logger.debug(
            f"MST threshold: {threshold:.4f} "
            f"(mean={np.mean(mst_weights):.4f}, std={np.std(mst_weights):.4f})"
        )

        # Step 4: Cut MST at threshold
        mst_dense = mst.toarray()
        mst_dense[mst_dense > threshold] = 0

        # Step 5: Find connected components
        clusters = self._find_connected_components(mst_dense, n)

        # Step 6: Merge small clusters
        clusters = self._merge_small_clusters(clusters, embeddings)

        # Step 7: Compute centroids
        for cluster in clusters:
            cluster_embs = embeddings[cluster.member_indices]
            cluster.centroid = cluster_embs.mean(axis=0)

        logger.info(f"MST clustering: {n} items -> {len(clusters)} clusters")
        return clusters

    def _find_connected_components(
        self,
        adjacency: np.ndarray,
        n: int,
    ) -> list[Cluster]:
        """Find connected components in adjacency matrix."""
        # Make symmetric
        adjacency = adjacency + adjacency.T

        visited: set[int] = set()
        clusters: list[list[int]] = []

        def dfs(node: int, component: list[int]) -> None:
            visited.add(node)
            component.append(node)
            for neighbor in range(n):
                if neighbor not in visited and adjacency[node, neighbor] > 0:
                    dfs(neighbor, component)

        for node in range(n):
            if node not in visited:
                component: list[int] = []
                dfs(node, component)
                clusters.append(component)

        return [
            Cluster(cluster_id=i, member_indices=members)
            for i, members in enumerate(clusters)
        ]

    def _merge_small_clusters(
        self,
        clusters: list[Cluster],
        embeddings: np.ndarray,
    ) -> list[Cluster]:
        """Merge clusters smaller than min_cluster_size into nearest larger cluster."""
        if self.min_cluster_size <= 1:
            return clusters

        small_clusters = [c for c in clusters if c.size < self.min_cluster_size]
        large_clusters = [c for c in clusters if c.size >= self.min_cluster_size]

        if not large_clusters:
            # All clusters are small, merge into one
            all_indices = []
            for c in clusters:
                all_indices.extend(c.member_indices)
            return [Cluster(cluster_id=0, member_indices=all_indices)]

        # Compute centroids for large clusters
        large_centroids = np.array(
            [embeddings[c.member_indices].mean(axis=0) for c in large_clusters]
        )

        # Assign small cluster members to nearest large cluster
        for small in small_clusters:
            for idx in small.member_indices:
                # Find nearest large cluster
                distances = 1 - cosine_similarity(embeddings[idx : idx + 1], large_centroids)[0]
                nearest = np.argmin(distances)
                large_clusters[nearest].member_indices.append(idx)

        # Renumber clusters
        for i, cluster in enumerate(large_clusters):
            cluster.cluster_id = i

        return large_clusters

    def cluster_with_labels(
        self,
        embeddings: np.ndarray,
    ) -> tuple[list[Cluster], np.ndarray]:
        """Cluster and return cluster labels for each embedding.

        Returns:
            Tuple of (clusters, labels) where labels[i] is cluster id for embedding i
        """
        clusters = self.cluster(embeddings)

        labels = np.zeros(len(embeddings), dtype=int)
        for cluster in clusters:
            for idx in cluster.member_indices:
                labels[idx] = cluster.cluster_id

        return clusters, labels


class SimilarityThresholdClustering:
    """Simple threshold-based clustering fallback.

    Groups items with similarity above threshold.
    Used as fallback when MST clustering fails.
    """

    def __init__(self, similarity_threshold: float = 0.75):
        self.similarity_threshold = similarity_threshold

    def cluster(self, embeddings: np.ndarray) -> list[Cluster]:
        """Cluster by similarity threshold."""
        n = len(embeddings)
        if n == 0:
            return []
        if n == 1:
            return [Cluster(cluster_id=0, member_indices=[0], centroid=embeddings[0])]

        similarities = cosine_similarity(embeddings)
        assigned: set[int] = set()
        clusters: list[Cluster] = []

        for i in range(n):
            if i in assigned:
                continue

            # Start new cluster with item i
            cluster_members = [i]
            assigned.add(i)

            # Find all items similar to i
            for j in range(i + 1, n):
                if j not in assigned and similarities[i, j] >= self.similarity_threshold:
                    cluster_members.append(j)
                    assigned.add(j)

            clusters.append(
                Cluster(
                    cluster_id=len(clusters),
                    member_indices=cluster_members,
                    centroid=embeddings[cluster_members].mean(axis=0),
                )
            )

        return clusters
