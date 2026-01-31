"""Token string helpers and BOS detection."""

from typing import List, Optional

import torch
from transformers import PreTrainedTokenizer

from .beam import BeamPath, BeamState
from .utils import normalize_score


def get_token_strings(
    input_ids: torch.LongTensor,
    tokenizer: PreTrainedTokenizer,
) -> List[str]:
    """
    Convert input IDs to token strings.

    Args:
        input_ids: Input token IDs [batch_size, seq_len] or [seq_len]
        tokenizer: Tokenizer for decoding

    Returns:
        List of token strings
    """
    # Handle batch dimension
    if input_ids.dim() == 2:
        input_ids = input_ids[0]

    tokens = []
    for token_id in input_ids.tolist():
        # Decode individual token
        token_str = tokenizer.decode([token_id])
        tokens.append(token_str)

    return tokens


def get_bos_positions(
    input_ids: torch.LongTensor,
    tokenizer: PreTrainedTokenizer,
    bos_token_id: Optional[int] = None,
) -> List[int]:
    """
    Find positions of BOS tokens in the sequence.

    Args:
        input_ids: Input token IDs [batch_size, seq_len] or [seq_len]
        tokenizer: Tokenizer for BOS token ID
        bos_token_id: Override BOS token ID (uses tokenizer's if None)

    Returns:
        List of positions where BOS tokens occur
    """
    # Handle batch dimension
    if input_ids.dim() == 2:
        input_ids = input_ids[0]

    # Get BOS token ID
    if bos_token_id is None:
        bos_token_id = tokenizer.bos_token_id

    if bos_token_id is None:
        return []

    # Find all BOS positions
    positions = (input_ids == bos_token_id).nonzero(as_tuple=True)[0].tolist()

    return positions


def beam_state_to_path(
    beam: BeamState,
    input_ids: torch.LongTensor,
    tokenizer: PreTrainedTokenizer,
    length_norm: str = "avg_logprob",
) -> BeamPath:
    """
    Convert a BeamState to a BeamPath with token information.

    Args:
        beam: Completed beam state
        input_ids: Input token IDs [batch_size, seq_len] or [seq_len]
        tokenizer: Tokenizer for decoding
        length_norm: Score normalization mode

    Returns:
        BeamPath with full token information
    """
    # Handle batch dimension
    if input_ids.dim() == 2:
        input_ids = input_ids[0]

    ids_list = input_ids.tolist()

    # Get token IDs and strings for each position
    token_ids = [ids_list[pos] for pos in beam.positions]
    tokens = [tokenizer.decode([tid]) for tid in token_ids]

    # Compute normalized score
    score_norm = normalize_score(beam.log_score, beam.num_edges, length_norm)

    return BeamPath(
        positions=beam.positions,
        tokens=tokens,
        token_ids=token_ids,
        edge_attns=beam.edge_attns,
        score_raw=beam.log_score,
        score_norm=score_norm,
    )


def format_path_text(path: BeamPath, include_score: bool = True) -> str:
    """
    Format a beam path as human-readable text.

    Args:
        path: Beam path to format
        include_score: Whether to include the score

    Returns:
        Formatted string like: "token1 <- token2 <- token3 (score: -2.34)"
    """
    # Reverse so it reads left-to-right (earlier tokens first)
    tokens_reversed = path.tokens[::-1]

    # Clean up tokens for display (escape special chars, handle whitespace)
    display_tokens = []
    for tok in tokens_reversed:
        # Replace newlines and tabs with visible representations
        tok = tok.replace('\n', '\\n').replace('\t', '\\t')
        # Add quotes around tokens with spaces
        if ' ' in tok or tok == '':
            tok = f'"{tok}"'
        display_tokens.append(tok)

    path_str = " -> ".join(display_tokens)

    if include_score:
        path_str += f" (score: {path.score_norm:.4f})"

    return path_str
