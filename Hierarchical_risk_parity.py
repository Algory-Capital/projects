import pandas as pd
import numpy as np
from scipy.linalg import block_diag
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform
import matplotlib.pyplot as plt
#%matplotlib inline
 
 
nb_alphas = 250#250
nb_observations = int(0.3 * 252)
 
quality = 0.6 * np.ones((nb_alphas // 6, nb_alphas // 6))
value = 2.4 * np.ones((nb_alphas // 2, nb_alphas // 2))
momentum = 2.6 * np.ones((int(nb_alphas * (1 - 1/6 - 1/2) + 1),
                          int(nb_alphas * (1 - 1/6 - 1/2) + 1)))
 
correl_mom_value = -1.2 * np.ones((int(nb_alphas * (1 - 1/6)) + 1,
                                   int(nb_alphas * (1 - 1/6)) + 1))
 
 
correl = (block_diag(quality, correl_mom_value) +
          block_diag(quality, momentum, value)) / 3
np.fill_diagonal(correl, 1)
 
 
 
mean_returns = np.zeros(nb_alphas)
volatilities = ([np.sqrt(0.1 / np.sqrt(252))] * (nb_alphas // 3) +
                [np.sqrt(0.3 / np.sqrt(252))] * (nb_alphas - nb_alphas // 3 - nb_alphas // 6) +
                [np.sqrt(0.5 / np.sqrt(252))] * (nb_alphas // 6))
covar = np.multiply(correl,
                    np.outer(np.array(volatilities),
                             np.array(volatilities)))
covar = pd.DataFrame(covar)
correl
#array([[1. , 0.4, 0.4, ..., 0. , 0. , 0. ],
#       [0.4, 1. , 0.4, ..., 0. , 0. , 0. ],
#       [0.4, 0.4, 1. , ..., 0. , 0. , 0. ],
#       ...,
#       [0. , 0. , 0. , ..., 1. , 0.4, 0.4],
#       [0. , 0. , 0. , ..., 0.4, 1. , 0.4],
#       [0. , 0. , 0. , ..., 0.4, 0.4, 1. ]])
plt.pcolormesh(correl)
plt.colorbar()
plt.title('Correlation matrix')
plt.show()
 
plt.pcolormesh(covar)
plt.colorbar()
plt.title('Covariance matrix')
plt.show()

alphas_returns = np.random.multivariate_normal(
    mean_returns, cov=covar, size=nb_observations)
 
alphas_returns = pd.DataFrame(alphas_returns)
plt.figure(figsize=(20, 10))
plt.plot(alphas_returns.cumsum())
plt.title('Performance of the different alphas', fontsize=24)
plt.show()

estimate_correl = alphas_returns.corr(method='pearson')
estimate_covar = alphas_returns.cov()
plt.pcolormesh(estimate_correl)
plt.colorbar()
plt.title('Estimated correlation matrix')
plt.show()
 
plt.pcolormesh(estimate_covar)
plt.colorbar()
plt.title('Estimated covariance matrix')
plt.show()
distances = np.sqrt((1 - estimate_correl) / 2)

def seriation(Z, N, cur_index):
    """Returns the order implied by a hierarchical tree (dendrogram).
    
       :param Z: A hierarchical tree (dendrogram).
       :param N: The number of points given to the clustering process.
       :param cur_index: The position in the tree for the recursive traversal.
       
       :return: The order implied by the hierarchical tree Z.
    """
    if cur_index < N:
        return [cur_index]
    else:
        left = int(Z[cur_index - N, 0])
        right = int(Z[cur_index - N, 1])
        return (seriation(Z, N, left) + seriation(Z, N, right))
 
    
def compute_serial_matrix(dist_mat, method="ward"):
    """Returns a sorted distance matrix.
    
       :param dist_mat: A distance matrix.
       :param method: A string in ["ward", "single", "average", "complete"].
        
        output:
            - seriated_dist is the input dist_mat,
              but with re-ordered rows and columns
              according to the seriation, i.e. the
              order implied by the hierarchical tree
            - res_order is the order implied by
              the hierarhical tree
            - res_linkage is the hierarhical tree (dendrogram)
        
        compute_serial_matrix transforms a distance matrix into
        a sorted distance matrix according to the order implied
        by the hierarchical tree (dendrogram)
    """
    N = len(dist_mat)
    flat_dist_mat = squareform(dist_mat)
    res_linkage = linkage(flat_dist_mat, method=method)
    res_order = seriation(res_linkage, N, N + N - 2)
    seriated_dist = np.zeros((N, N))
    a,b = np.triu_indices(N, k=1)
    seriated_dist[a,b] = dist_mat[[res_order[i] for i in a], [res_order[j] for j in b]]
    seriated_dist[b,a] = seriated_dist[a,b]
    
    return seriated_dist, res_order, res_linkage
 
 
ordered_dist_mat, res_order, res_linkage = compute_serial_matrix(distances.values, method='single')
plt.pcolormesh(distances)
plt.colorbar()
plt.title('Original order distance matrix')
plt.show()
 
plt.pcolormesh(ordered_dist_mat)
plt.colorbar()
plt.title('Re-ordered distance matrix')
plt.show()
def compute_HRP_weights(covariances, res_order):
    weights = pd.Series(1, index=res_order)
    clustered_alphas = [res_order]
 
    while len(clustered_alphas) > 0:
        clustered_alphas = [cluster[start:end] for cluster in clustered_alphas
                            for start, end in ((0, len(cluster) // 2),
                                               (len(cluster) // 2, len(cluster)))
                            if len(cluster) > 1]
        for subcluster in range(0, len(clustered_alphas), 2):
            left_cluster = clustered_alphas[subcluster]
            right_cluster = clustered_alphas[subcluster + 1]
 
            left_subcovar = covariances[left_cluster].loc[left_cluster]
            inv_diag = 1 / np.diag(left_subcovar.values)
            parity_w = inv_diag * (1 / np.sum(inv_diag))
            left_cluster_var = np.dot(parity_w, np.dot(left_subcovar, parity_w))
 
            right_subcovar = covariances[right_cluster].loc[right_cluster]
            inv_diag = 1 / np.diag(right_subcovar.values)
            parity_w = inv_diag * (1 / np.sum(inv_diag))
            right_cluster_var = np.dot(parity_w, np.dot(right_subcovar, parity_w))
 
            alloc_factor = 1 - left_cluster_var / (left_cluster_var + right_cluster_var)
 
            weights[left_cluster] *= alloc_factor
            weights[right_cluster] *= 1 - alloc_factor
            
    return weights
 
 
def compute_MV_weights(covariances):
    inv_covar = np.linalg.inv(covariances)
    u = np.ones(len(covariances))
    
    return np.dot(inv_covar, u) / np.dot(u, np.dot(inv_covar, u))
 
 
def compute_RP_weights(covariances):
    weights = (1 / np.diag(covariances))
    
    return weights / sum(weights)
 
 
def compute_unif_weights(covariances):
    
    return [1 / len(covariances) for i in range(len(covariances))]
### Hierarchical Risk Parity
 
HRP_weights = compute_HRP_weights(estimate_covar, res_order)
 
print(round((HRP_weights * alphas_returns).sum(axis=1).std() * np.sqrt(252),
            2))
0.38
 
 
HRP_weights = compute_HRP_weights(covar, res_order)
 
print(round((HRP_weights * alphas_returns).sum(axis=1).std() * np.sqrt(252),
            2))
0.34
### 1 / N uniform weighting
 
unif_weights = compute_unif_weights(estimate_covar)
 
print(round((unif_weights * alphas_returns).sum(axis=1).std() * np.sqrt(252),
            2))
0.43
### Naive Risk Parity 1 / volatility
 
RP_weights = compute_RP_weights(estimate_covar)
 
print(round((RP_weights * alphas_returns).sum(axis=1).std() * np.sqrt(252),
      2))
0.29
 
RP_weights = compute_RP_weights(covar)
 
print(round((RP_weights * alphas_returns).sum(axis=1).std() * np.sqrt(252),
            2))
0.29
### Minimum Variance
 
MV_weights = compute_MV_weights(estimate_covar)
 
print(round((MV_weights * alphas_returns).sum(axis=1).std() * np.sqrt(252),
            2))
0.0
 
MV_weights = compute_MV_weights(covar)
 
print(round((MV_weights * alphas_returns).sum(axis=1).std() * np.sqrt(252),
            2))
0.22
nb_observations = int(2 * 252)
 
alphas_returns = np.random.multivariate_normal(
    mean_returns, cov=covar, size=nb_observations)
 
alphas_returns = pd.DataFrame(alphas_returns)
### Hierarchical Risk Parity
 
HRP_weights = compute_HRP_weights(estimate_covar, res_order)
 
print(round((HRP_weights * alphas_returns).sum(axis=1).std() * np.sqrt(252),
            2))
0.43
 
### 1 / N uniform weighting
 
unif_weights = compute_unif_weights(estimate_covar)
 
print(round((unif_weights * alphas_returns).sum(axis=1).std() * np.sqrt(252),
            2))
0.45
 
### Naive Risk Parity 1 / volatility
 
RP_weights = compute_RP_weights(estimate_covar)
 
print(round((RP_weights * alphas_returns).sum(axis=1).std() * np.sqrt(252),
            2))
0.32
 
MV_weights = compute_MV_weights(estimate_covar)
 
print(round((MV_weights * alphas_returns).sum(axis=1).std() * np.sqrt(252),
            2))
7.71
