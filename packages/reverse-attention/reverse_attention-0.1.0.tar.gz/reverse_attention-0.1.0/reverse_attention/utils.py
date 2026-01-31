"""Utility functions for reverse attention tracing."""

import math
import warnings
from typing import List


def safe_log(x: float, eps: float = 1e-12) -> float:
    """
    Compute log with epsilon to avoid log(0).

    Args:
        x: Value to take log of
        eps: Minimum value to use (values below this are clipped)

    Returns:
        log(max(x, eps))

    Note:
        If x < eps, the value is clipped which may affect score accuracy.
        Zero or negative attention weights indicate potential upstream issues.
    """
    if x < eps:
        if x <= 0:
            warnings.warn(
                f"Attention weight {x} <= 0 encountered. "
                "This may indicate numerical issues in the model."
            )
    return math.log(max(x, eps))


def normalize_score(
    log_score: float,
    path_length: int,
    mode: str = "avg_logprob",
) -> float:
    """
    Normalize cumulative log score by path length.

    Args:
        log_score: Cumulative log probability
        path_length: Number of edges in the path
        mode: Normalization mode
            - "none": No normalization
            - "avg_logprob": Divide by path length (geometric mean)
            - "sqrt": Divide by sqrt(path_length)
            - "pow:α": Divide by path_length^α (e.g., "pow:0.7")

    Returns:
        Normalized score
    """
    if path_length == 0:
        return log_score

    if mode == "none":
        return log_score
    elif mode == "avg_logprob":
        return log_score / path_length
    elif mode == "sqrt":
        return log_score / math.sqrt(path_length)
    elif mode.startswith("pow:"):
        try:
            alpha = float(mode.split(":")[1])
            return log_score / (path_length ** alpha)
        except (IndexError, ValueError):
            raise ValueError(f"Invalid pow mode format: {mode}. Expected 'pow:α' (e.g., 'pow:0.7')")
    else:
        raise ValueError(f"Unknown normalization mode: {mode}. "
                        f"Expected one of: 'none', 'avg_logprob', 'sqrt', 'pow:α'")


def exp_normalize(scores: List[float]) -> List[float]:
    """
    Compute softmax over scores (in log space for numerical stability).

    Args:
        scores: List of log scores

    Returns:
        List of probabilities (sum to 1)
    """
    if not scores:
        return []

    max_score = max(scores)
    exp_scores = [math.exp(s - max_score) for s in scores]
    total = sum(exp_scores)

    # Use tolerance instead of exact equality for float comparison
    if total < 1e-10:
        return [1.0 / len(scores)] * len(scores)

    return [e / total for e in exp_scores]
