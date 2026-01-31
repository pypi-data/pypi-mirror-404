"""Main tracer API for reverse attention beam search."""

import warnings
from typing import List, Optional, Union

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer

from .attn_extract import extract_attention, get_attention_mask
from .beam import BeamPath, TraceResult, beam_search_backward
from .sankey import beams_to_sankey, render_html as _render_html
from .tokenize import (
    beam_state_to_path,
    format_path_text,
    get_bos_positions,
    get_token_strings,
)


class ReverseAttentionTracer:
    """
    Trace attention paths backward through a transformer model.

    This class provides the main API for extracting attention weights,
    running beam search backward through the attention matrix, and
    visualizing the results as an interactive Sankey diagram.

    Example:
        >>> from transformers import AutoModelForCausalLM, AutoTokenizer
        >>> model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2-0.5B")
        >>> tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2-0.5B")
        >>> tracer = ReverseAttentionTracer(model, tokenizer)
        >>> input_ids = tokenizer("Hello world", return_tensors="pt").input_ids
        >>> result = tracer.trace(input_ids)
        >>> tracer.render_html(result, "output/")
    """

    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer,
        device: Optional[Union[str, torch.device]] = None,
        dtype: Optional[torch.dtype] = None,
    ):
        """
        Initialize the tracer.

        Args:
            model: HuggingFace transformer model
            tokenizer: Corresponding tokenizer
            device: Device to run on (defaults to model's device)
            dtype: Data type for computation (defaults to model's dtype)
        """
        self.model = model
        self.tokenizer = tokenizer

        # Set model to eval mode
        self.model.eval()

        # Store device/dtype
        self.device = device or next(model.parameters()).device
        self.dtype = dtype or next(model.parameters()).dtype

    def trace(
        self,
        input_ids: torch.LongTensor,
        target_pos: Optional[int] = None,
        attention_mask: Optional[torch.LongTensor] = None,
        layer: int = -1,
        top_beam: int = 5,
        top_k: int = 5,
        min_attn: float = 0.0,
        agg_heads: str = "mean",
        length_norm: str = "avg_logprob",
        stop_at_bos: bool = True,
        bos_token_id: Optional[int] = None,
    ) -> TraceResult:
        """
        Trace attention paths backward from a target position.

        Args:
            input_ids: Input token IDs [1, seq_len]
            target_pos: Position to trace from (default: -1, last token).
                        Supports negative indexing.
            attention_mask: Optional attention mask [1, seq_len]
            layer: Layer index to extract attention from (default: -1, last layer).
                   Supports negative indexing.
            top_beam: Number of beams to keep at each step
            top_k: Number of top predecessors to consider at each step
            min_attn: Minimum attention threshold for considering a predecessor
            agg_heads: Head aggregation mode ("mean", "max", "none")
            length_norm: Score normalization mode
                         ("none", "avg_logprob", "sqrt", "pow:α")
            stop_at_bos: Whether to stop at BOS positions
            bos_token_id: Override BOS token ID (uses tokenizer's if None)

        Returns:
            TraceResult with beams, sankey data, and metadata

        Raises:
            ValueError: If parameters are invalid
        """
        # Validate parameters
        if top_beam < 1:
            raise ValueError(f"top_beam must be >= 1, got {top_beam}")
        if top_k < 1:
            raise ValueError(f"top_k must be >= 1, got {top_k}")
        if agg_heads == "none":
            raise ValueError(
                "agg_heads='none' is not supported for beam search. "
                "Use 'mean' or 'max' to aggregate attention heads."
            )

        # Validate input shape
        if input_ids.dim() == 1:
            input_ids = input_ids.unsqueeze(0)

        if input_ids.dim() != 2 or input_ids.size(0) != 1:
            raise ValueError(f"Expected input_ids shape [1, seq_len], got {input_ids.shape}")

        seq_len = input_ids.size(1)

        # Resolve target position (support negative indexing)
        if target_pos is None:
            target_pos = -1

        if target_pos < 0:
            resolved_target = seq_len + target_pos
        else:
            resolved_target = target_pos

        if resolved_target < 0 or resolved_target >= seq_len:
            raise ValueError(f"Target position {target_pos} out of range for sequence length {seq_len}")

        # Get/create attention mask
        attention_mask = get_attention_mask(input_ids, self.tokenizer, attention_mask)

        # Extract attention for specified layer
        attn, resolved_layer = extract_attention(
            self.model,
            input_ids,
            attention_mask,
            layer,
            agg_heads,
        )

        # Get BOS positions for stopping
        bos_positions = []
        if stop_at_bos:
            bos_positions = get_bos_positions(input_ids, self.tokenizer, bos_token_id)
            if not bos_positions:
                warnings.warn(
                    "stop_at_bos=True but no BOS token found in sequence. "
                    "Beam search will run until position 0."
                )

        # Flatten attention mask for beam search
        flat_mask = attention_mask[0] if attention_mask is not None else None

        # Run beam search backward
        beam_states = beam_search_backward(
            attn,
            resolved_target,
            top_beam=top_beam,
            top_k=top_k,
            min_attn=min_attn,
            length_norm=length_norm,
            stop_at_bos=stop_at_bos,
            bos_positions=bos_positions,
            attention_mask=flat_mask,
        )

        # Convert to BeamPaths
        beams = [
            beam_state_to_path(state, input_ids, self.tokenizer, length_norm)
            for state in beam_states
        ]

        # Get all token strings
        tokens = get_token_strings(input_ids, self.tokenizer)

        # Generate Sankey data
        sankey = beams_to_sankey(beams, tokens, layer=resolved_layer)

        # Generate path text descriptions
        paths_text = [format_path_text(beam) for beam in beams]

        return TraceResult(
            seq_len=seq_len,
            target_pos=resolved_target,
            layer=resolved_layer,
            top_beam=top_beam,
            top_k=top_k,
            tokens=tokens,
            beams=beams,
            sankey=sankey,
            paths_text=paths_text,
        )

    def render_html(
        self,
        trace_result: TraceResult,
        out_dir: str,
        open_browser: bool = False,
    ) -> str:
        """
        Render trace result as interactive HTML visualization.

        Args:
            trace_result: Result from trace()
            out_dir: Output directory for HTML files
            open_browser: Whether to open the result in a browser

        Returns:
            Path to the generated index.html
        """
        return _render_html(trace_result, out_dir, open_browser)

    def trace_text(
        self,
        text: str,
        target_pos: Optional[int] = None,
        **kwargs,
    ) -> TraceResult:
        """
        Convenience method to trace from text input.

        Args:
            text: Input text to tokenize and trace
            target_pos: Position to trace from (default: -1, last token)
            **kwargs: Additional arguments passed to trace()

        Returns:
            TraceResult with beams, sankey data, and metadata
        """
        encoded = self.tokenizer(text, return_tensors="pt")
        input_ids = encoded.input_ids
        attention_mask = encoded.get("attention_mask")

        return self.trace(
            input_ids,
            target_pos=target_pos,
            attention_mask=attention_mask,
            **kwargs,
        )
