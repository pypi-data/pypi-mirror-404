# Proposal: Ensemble-ENN with Randomized Sparse Embeddings

This proposal outlines a scalable architecture for `EpistemicNearestNeighbors` to handle both large $N$ (number of observations) and large $D$ (dimension of search space) by using an ensemble of randomized embeddings and KD-Trees.

## Core Concept

Instead of a single index in the original $D$-dimensional space, we maintain an ensemble of $B$ independent learners. Each learner operates in a fixed, low-dimensional projected space.

### 1. Randomized Sparse Projections
For each learner $b \in \{1, \dots, B\}$:
- Generate a sparse random projection matrix $A^{(b)} \in \mathbb{R}^{D_e \times D}$.
- The embedding dimension $D_e$ is small (e.g., $D_e \in [5, 20]$).
- Sparse matrices ensure that the projection $x^{(b)} = A^{(b)}x$ is $O(\text{nnz})$ rather than $O(D \cdot D_e)$.

### 2. Low-D KD-Trees
- Each learner $b$ maintains its own `scipy.spatial.cKDTree` (or similar) in its $D_e$-dimensional space.
- KD-Trees provide exact, $O(\log N)$ KNN lookups in low dimensions, avoiding the $O(N)$ scaling of flat indices and the graph overhead of HNSW.

### 3. MVUE Combination
For a query point $x$:
1. Project $x$ into each embedding space: $x^{(b)} = A^{(b)}x$.
2. Perform KNN lookup in each KD-Tree to get local neighbors.
3. Apply standard ENN formulae to compute $\mu_b$ and $\sigma_b^2$ for each learner.
4. Combine the $B$ estimates using the Minimum-Variance Unbiased Estimator (MVUE):

$$\sigma_{total}^2 = \left( \sum_{b=1}^B \frac{1}{\sigma_b^2} \right)^{-1}$$
$$\mu_{total} = \sigma_{total}^2 \sum_{b=1}^B \frac{\mu_b}{\sigma_b^2}$$

## Scaling Benefits

| Metric | Flat (Current) | HNSW (Current) | Ensemble-ENN (Proposed) |
| :--- | :--- | :--- | :--- |
| **Insertion** | $O(N \cdot D)$ | $O(M \cdot \log N \cdot D)$ | $O(B \cdot (\text{nnz} + \log N))$ |
| **Search** | $O(N \cdot D)$ | $O(\log N \cdot D)$ | $O(B \cdot (\text{nnz} + \log N))$ |
| **Memory** | $O(N \cdot D)$ | $O(N \cdot D + \text{graph})$ | $O(N \cdot B \cdot D_e)$ |

## Statistical Integrity
- **Johnson-Lindenstrauss Lemma**: Randomized projections preserve pairwise distances with high probability, ensuring the "nearest neighbor" concept remains valid.
- **Ensemble Diversity**: Randomizing $D_e$ and the sparse masks across $B$ learners captures multi-scale features and reduces the impact of information loss in any single projection.
- **Epistemic Robustness**: The MVUE combination naturally handles varying confidence levels across different projections.

## Implementation Steps
1. Define `ENNIndexDriver.ENSEMBLE` in `enums.py`.
2. Implement `SparseRandomProjection` helper.
3. Create `EnsembleENNIndex` that manages $B$ KD-Trees.
4. Update `EpistemicNearestNeighbors` to handle the ensemble combination logic.
