"""Attention extraction from transformer models."""

from typing import Optional, Tuple

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer


def extract_attention(
    model: PreTrainedModel,
    input_ids: torch.LongTensor,
    attention_mask: Optional[torch.LongTensor],
    layer: int,
    agg_heads: str = "mean",
) -> Tuple[torch.Tensor, int]:
    """
    Extract attention weights from a specific layer.

    Args:
        model: HuggingFace transformer model
        input_ids: Input token IDs [batch_size, seq_len]
        attention_mask: Optional attention mask [batch_size, seq_len]
        layer: Layer index (supports negative indexing)
        agg_heads: Head aggregation mode
            - "mean": Average across all heads
            - "max": Maximum across all heads
            - "none": Return all heads [num_heads, seq_len, seq_len]

    Returns:
        Tuple of:
            - Attention tensor [seq_len, seq_len] (or [heads, seq, seq] if agg_heads="none")
            - Resolved layer index (positive)
    """
    device = next(model.parameters()).device
    input_ids = input_ids.to(device)

    if attention_mask is not None:
        attention_mask = attention_mask.to(device)

    # Run forward pass with attention output
    with torch.no_grad():
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_attentions=True,
            use_cache=False,
        )

    # Get attention from specified layer
    # attentions is a tuple of (batch, num_heads, seq_len, seq_len) for each layer
    attentions = outputs.attentions
    num_layers = len(attentions)

    # Resolve negative layer index
    if layer < 0:
        resolved_layer = num_layers + layer
    else:
        resolved_layer = layer

    if resolved_layer < 0 or resolved_layer >= num_layers:
        raise ValueError(f"Layer {layer} out of range. Model has {num_layers} layers.")

    # Get attention for this layer: [batch, heads, seq, seq]
    attn = attentions[resolved_layer]

    # Remove batch dimension (assume batch_size=1)
    attn = attn[0]  # [heads, seq, seq]

    # Aggregate heads
    if agg_heads == "mean":
        attn = attn.mean(dim=0)  # [seq, seq]
    elif agg_heads == "max":
        attn = attn.max(dim=0).values  # [seq, seq]
    elif agg_heads == "none":
        pass  # Keep [heads, seq, seq]
    else:
        raise ValueError(f"Unknown agg_heads mode: {agg_heads}. "
                        f"Expected one of: 'mean', 'max', 'none'")

    # Move to CPU
    attn = attn.cpu()

    return attn, resolved_layer


def get_attention_mask(
    input_ids: torch.LongTensor,
    tokenizer: PreTrainedTokenizer,
    attention_mask: Optional[torch.Tensor] = None,
) -> torch.LongTensor:
    """
    Get or create attention mask from input IDs.

    Args:
        input_ids: Input token IDs [batch_size, seq_len]
        tokenizer: Tokenizer for pad token detection
        attention_mask: Optional pre-computed mask (any dtype, will be converted to long)

    Returns:
        Attention mask [batch_size, seq_len] where 1 = valid, 0 = masked (LongTensor)
    """
    if attention_mask is not None:
        # Normalize dtype to long (handles bool, float, int tensors)
        return attention_mask.long()

    # Create mask based on pad token
    if tokenizer.pad_token_id is not None:
        attention_mask = (input_ids != tokenizer.pad_token_id).long()
    else:
        # No pad token, assume all tokens are valid
        attention_mask = torch.ones_like(input_ids)

    return attention_mask
