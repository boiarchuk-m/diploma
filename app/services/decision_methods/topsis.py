import numpy as np

def topsis(matrix, weights, cost_cols=None):
    """
    Vectorized TOPSIS implementation using NumPy.

    Parameters:
        matrix (list[list]]): Decision matrix, numeric values only.
        weights (list): Weight vector with same length as matrix columns.
        cost_cols (list[int]): Column indices to be treated as cost criteria.

    Returns:
        scores (np.ndarray): Relative closeness to ideal solution.
        ranks (np.ndarray): Ranking indexes (1 = best).
    """

    matrix = np.array(matrix, dtype=float)
    weights = np.array(weights, dtype=float)
    n_alternatives, n_criteria = matrix.shape

    # Step 1: Invert cost criteria
    if cost_cols:
         matrix[:, cost_cols] = 1 / (matrix[:, cost_cols] + 1e-12)  # avoid division by zero
    
    # Step 2: Normalize the decision matrix
    norm = np.linalg.norm(matrix, axis=0)
    norm = np.where(norm == 0, 1, norm)  # avoid division by zero
    norm_matrix = matrix / norm

    # Step 3: Apply weights
    weighted_matrix = norm_matrix * weights

    # Step 4: Compute ideal and negative-ideal solutions

    ideal = np.max(weighted_matrix, axis=0)
    anti_ideal = np.min(weighted_matrix, axis=0)

    # Step 5: Calculate distances to ideal and anti-ideal solutions

    d_plus = np.linalg.norm(weighted_matrix - ideal, axis=1)
    d_minus = np.linalg.norm(weighted_matrix - anti_ideal, axis=1)

    # Step 6: Calculate scores

    scores = d_minus / (d_plus + d_minus + 1e-12)

    # Step 7: Determine ranks
    ranks = (-scores).argsort().argsort() + 1 
    print("Topsis scores:", scores, "ranks:", ranks)
    return scores, ranks