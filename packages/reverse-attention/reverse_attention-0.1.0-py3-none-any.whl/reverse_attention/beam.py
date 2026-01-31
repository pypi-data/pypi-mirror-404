"""Beam search data structures and algorithm for reverse attention tracing."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import math

import torch

from .utils import normalize_score, safe_log


@dataclass
class BeamState:
    """State of a single beam during search."""
    positions: List[int]      # [target_pos, ..., current_pos]
    edge_attns: List[float]   # Attention weights along edges
    log_score: float          # Cumulative log(attn)
    is_terminal: bool = False

    @property
    def current_pos(self) -> int:
        """Get the current (most recent) position in the beam."""
        return self.positions[-1]

    @property
    def num_edges(self) -> int:
        """Number of edges traversed."""
        return len(self.edge_attns)


@dataclass
class BeamPath:
    """A completed beam path with token information."""
    positions: List[int]      # Token positions in sequence
    tokens: List[str]         # Token strings
    token_ids: List[int]      # Token IDs
    edge_attns: List[float]   # Attention weights along edges
    score_raw: float          # Raw cumulative log score
    score_norm: float         # Length-normalized score


@dataclass
class SankeyNode:
    """A node in the Sankey diagram."""
    id: str                   # Unique identifier
    name: str                 # Display name (token)
    position: int             # Position in sequence
    layer: int = 0            # Layer index (for multi-layer support)


@dataclass
class SankeyLink:
    """A link in the Sankey diagram."""
    source: str               # Source node ID
    target: str               # Target node ID
    value: float              # Link weight (aggregated attention)
    beam_indices: List[int] = field(default_factory=list)  # Which beams use this link


@dataclass
class SankeyData:
    """Complete Sankey diagram data."""
    nodes: List[SankeyNode]
    links: List[SankeyLink]


@dataclass
class TraceResult:
    """Result of a reverse attention trace."""
    seq_len: int              # Sequence length
    target_pos: int           # Target position traced from
    layer: int                # Layer index
    top_beam: int             # Number of beams kept
    top_k: int                # Top-k predecessors per step
    tokens: List[str]         # All tokens in sequence
    beams: List[BeamPath]     # Completed beam paths
    sankey: SankeyData        # Sankey visualization data
    paths_text: List[str]     # Human-readable path descriptions


def get_top_k_predecessors(
    attn: torch.Tensor,
    query_pos: int,
    k: int,
    min_attn: float,
    attention_mask: Optional[torch.Tensor],
) -> List[Tuple[int, float]]:
    """
    Get top-k predecessor positions with highest attention.

    Args:
        attn: Attention matrix [seq_len, seq_len]
        query_pos: Current position to find predecessors for
        k: Maximum number of predecessors to return
        min_attn: Minimum attention threshold
        attention_mask: Optional mask [seq_len] where 1 = valid, 0 = masked

    Returns:
        List of (position, attention_weight) tuples, sorted by attention descending
    """
    # Get attention weights for all positions attending to query_pos
    # attn[query_pos, :] gives attention from query_pos to all positions
    attn_row = attn[query_pos, :query_pos].clone()  # Only positions < query_pos (causal)

    if attn_row.numel() == 0:
        return []

    # Apply attention mask if provided
    if attention_mask is not None:
        mask = attention_mask[:query_pos]
        attn_row = attn_row * mask.float()

    # Apply minimum attention threshold
    attn_row[attn_row < min_attn] = 0.0

    # Get top-k
    num_valid = (attn_row > 0).sum().item()
    actual_k = min(k, int(num_valid))

    if actual_k == 0:
        return []

    values, indices = torch.topk(attn_row, actual_k)

    return [(int(idx), float(val)) for idx, val in zip(indices, values)]


def extend_beam(
    beam: BeamState,
    pred_pos: int,
    attn_weight: float,
) -> BeamState:
    """Extend a beam with a new predecessor position."""
    return BeamState(
        positions=beam.positions + [pred_pos],
        edge_attns=beam.edge_attns + [attn_weight],
        log_score=beam.log_score + safe_log(attn_weight),
        is_terminal=False,
    )


def prune_beams(
    beams: List[BeamState],
    top_beam: int,
    length_norm: str,
) -> List[BeamState]:
    """Prune beams to keep only top_beam by normalized score."""
    if len(beams) <= top_beam:
        return beams

    # Sort by normalized score (descending)
    scored = [
        (normalize_score(b.log_score, b.num_edges, length_norm), b)
        for b in beams
    ]
    scored.sort(key=lambda x: x[0], reverse=True)

    return [b for _, b in scored[:top_beam]]


def beam_search_backward(
    attn: torch.Tensor,
    target_pos: int,
    top_beam: int = 5,
    top_k: int = 5,
    min_attn: float = 0.0,
    length_norm: str = "avg_logprob",
    stop_at_bos: bool = True,
    bos_positions: Optional[List[int]] = None,
    attention_mask: Optional[torch.Tensor] = None,
) -> List[BeamState]:
    """
    Perform beam search backward through attention.

    Args:
        attn: Attention matrix [seq_len, seq_len]
        target_pos: Starting position (trace backward from here)
        top_beam: Number of beams to keep at each step
        top_k: Number of top predecessors to consider at each step
        min_attn: Minimum attention threshold for considering a predecessor
        length_norm: Score normalization mode ("none", "avg_logprob", "sqrt", "pow:α")
        stop_at_bos: Whether to stop at BOS positions
        bos_positions: List of BOS token positions (if stop_at_bos=True)
        attention_mask: Optional mask [seq_len] where 1 = valid, 0 = masked

    Returns:
        List of terminal BeamStates sorted by normalized score (descending)
    """
    if bos_positions is None:
        bos_positions = []

    bos_set = set(bos_positions)

    # Initialize with single beam at target position
    active_beams = [BeamState(positions=[target_pos], edge_attns=[], log_score=0.0)]
    terminal_beams = []

    # Maximum iterations to prevent infinite loops
    max_iterations = target_pos + 1

    for _ in range(max_iterations):
        if not active_beams:
            break

        new_beams = []

        for beam in active_beams:
            if beam.is_terminal:
                terminal_beams.append(beam)
                continue

            cur = beam.current_pos

            # Check if already at position 0 (can't go further back)
            if cur == 0:
                terminal_beams.append(BeamState(
                    positions=beam.positions,
                    edge_attns=beam.edge_attns,
                    log_score=beam.log_score,
                    is_terminal=True,
                ))
                continue

            # Get top-k predecessors
            candidates = get_top_k_predecessors(
                attn, cur, top_k, min_attn, attention_mask
            )

            if not candidates:
                # No valid predecessors, mark as terminal
                terminal_beams.append(BeamState(
                    positions=beam.positions,
                    edge_attns=beam.edge_attns,
                    log_score=beam.log_score,
                    is_terminal=True,
                ))
                continue

            for pred_pos, attn_weight in candidates:
                new_beam = extend_beam(beam, pred_pos, attn_weight)

                # Check termination conditions
                if pred_pos == 0:
                    new_beam.is_terminal = True
                elif stop_at_bos and pred_pos in bos_set:
                    new_beam.is_terminal = True

                new_beams.append(new_beam)

        # Separate terminal and active beams
        still_active = [b for b in new_beams if not b.is_terminal]
        newly_terminal = [b for b in new_beams if b.is_terminal]
        terminal_beams.extend(newly_terminal)

        # Prune active beams
        active_beams = prune_beams(still_active, top_beam, length_norm)

    # Sort terminal beams by normalized score
    scored = [
        (normalize_score(b.log_score, b.num_edges, length_norm), b)
        for b in terminal_beams
    ]
    scored.sort(key=lambda x: x[0], reverse=True)

    # Return top_beam results
    return [b for _, b in scored[:top_beam]]
