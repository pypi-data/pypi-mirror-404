"""Sankey diagram generation and HTML rendering."""

import json
import os
import shutil
import sys
import warnings
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

from .beam import BeamPath, SankeyData, SankeyLink, SankeyNode
from .utils import exp_normalize

if TYPE_CHECKING:
    from .beam import TraceResult

# Use importlib.resources for Python 3.9+
if sys.version_info >= (3, 9):
    from importlib.resources import files as importlib_files
else:
    from importlib_resources import files as importlib_files


def compute_beam_weights(beams: List[BeamPath]) -> List[float]:
    """
    Compute softmax weights for beams based on normalized scores.

    Args:
        beams: List of beam paths

    Returns:
        List of weights (sum to 1)
    """
    scores = [b.score_norm for b in beams]
    return exp_normalize(scores)


def beams_to_sankey(
    beams: List[BeamPath],
    tokens: List[str],
    layer: int = 0,
    aggregate: bool = True,
) -> SankeyData:
    """
    Convert beam paths to Sankey diagram data.

    Args:
        beams: List of beam paths
        tokens: All tokens in the sequence
        layer: Layer index for node IDs
        aggregate: Whether to aggregate edges across beams

    Returns:
        SankeyData with nodes and links
    """
    if not beams:
        return SankeyData(nodes=[], links=[])

    # Collect all unique positions
    positions_set = set()
    for beam in beams:
        positions_set.update(beam.positions)

    # Create nodes for each position
    nodes = []
    node_ids = {}
    for pos in sorted(positions_set):
        node_id = f"L{layer}_P{pos}"
        node_ids[pos] = node_id

        # Check for position mismatch (indicates bug elsewhere)
        if pos >= len(tokens):
            warnings.warn(
                f"Beam position {pos} exceeds token list length {len(tokens)}. "
                "This may indicate a bug in beam search or tokenization."
            )
            token_name = f"[{pos}]"
        else:
            token_name = tokens[pos]

        nodes.append(SankeyNode(
            id=node_id,
            name=token_name,
            position=pos,
            layer=layer,
        ))

    # Compute beam weights for aggregation
    beam_weights = compute_beam_weights(beams)

    # Collect edges
    # For Sankey, links go from source to target in the forward direction
    # Our beams go backward, so we reverse: position[i+1] -> position[i]
    edge_map: Dict[tuple, Dict] = {}  # (source, target) -> {value, beam_indices, attns}

    for beam_idx, beam in enumerate(beams):
        beam_weight = beam_weights[beam_idx]

        # Validate invariant: positions should have one more element than edge_attns
        if len(beam.positions) != len(beam.edge_attns) + 1:
            raise ValueError(
                f"Beam {beam_idx} invariant violated: "
                f"len(positions)={len(beam.positions)} != len(edge_attns)+1={len(beam.edge_attns)+1}"
            )

        # Iterate through edges (reversed positions)
        for i, edge_attn in enumerate(beam.edge_attns):
            # positions[i] attends to positions[i+1]
            # So the Sankey link is: positions[i+1] -> positions[i]
            source_pos = beam.positions[i + 1]
            target_pos = beam.positions[i]

            source_id = node_ids[source_pos]
            target_id = node_ids[target_pos]
            key = (source_id, target_id)

            if key not in edge_map:
                edge_map[key] = {
                    'value': 0.0,
                    'beam_indices': [],
                    'attns': [],
                }

            if aggregate:
                # Weighted sum of attention values
                edge_map[key]['value'] += beam_weight * edge_attn
            else:
                edge_map[key]['value'] += edge_attn

            edge_map[key]['beam_indices'].append(beam_idx)
            edge_map[key]['attns'].append(edge_attn)

    # Create links
    links = []
    for (source_id, target_id), data in edge_map.items():
        links.append(SankeyLink(
            source=source_id,
            target=target_id,
            value=data['value'],
            beam_indices=sorted(set(data['beam_indices'])),
        ))

    return SankeyData(nodes=nodes, links=links)


def sankey_to_dict(sankey: SankeyData) -> dict:
    """Convert SankeyData to dictionary for JSON serialization."""
    return {
        'nodes': [
            {
                'id': n.id,
                'name': n.name,
                'position': n.position,
                'layer': n.layer,
            }
            for n in sankey.nodes
        ],
        'links': [
            {
                'source': l.source,
                'target': l.target,
                'value': l.value,
                'beam_indices': l.beam_indices,
            }
            for l in sankey.links
        ],
    }


def trace_result_to_json(trace_result: "TraceResult") -> str:
    """
    Convert TraceResult to JSON for visualization.

    Args:
        trace_result: Complete trace result

    Returns:
        JSON string
    """
    data = {
        'metadata': {
            'seq_len': trace_result.seq_len,
            'target_pos': trace_result.target_pos,
            'layer': trace_result.layer,
            'top_beam': trace_result.top_beam,
            'top_k': trace_result.top_k,
        },
        'tokens': trace_result.tokens,
        'beams': [
            {
                'positions': b.positions,
                'tokens': b.tokens,
                'token_ids': b.token_ids,
                'edge_attns': b.edge_attns,
                'score_raw': b.score_raw,
                'score_norm': b.score_norm,
            }
            for b in trace_result.beams
        ],
        'sankey': sankey_to_dict(trace_result.sankey),
        'paths_text': trace_result.paths_text,
    }
    return json.dumps(data, indent=2)


def get_html_template_dir() -> Path:
    """
    Get the path to the HTML template directory.

    Uses importlib.resources for reliable access in installed packages.
    Falls back to file-relative path if importlib access fails.
    """
    try:
        # Try importlib.resources first (works in installed packages)
        template_dir = importlib_files('reverse_attention') / 'html'
        # Verify it exists by trying to access it
        if hasattr(template_dir, 'is_dir') and template_dir.is_dir():
            return Path(str(template_dir))
    except (TypeError, AttributeError):
        pass

    # Fallback to file-relative path (works in development)
    return Path(__file__).parent / 'html'


def render_html(
    trace_result: "TraceResult",
    out_dir: str,
    open_browser: bool = False,
) -> str:
    """
    Render trace result as interactive HTML visualization.

    Args:
        trace_result: Complete trace result
        out_dir: Output directory for HTML files
        open_browser: Whether to open the result in a browser

    Returns:
        Path to the generated index.html

    Raises:
        RuntimeError: If output directory cannot be created or files cannot be written
    """
    out_path = Path(out_dir)

    try:
        out_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RuntimeError(f"Cannot create output directory '{out_dir}': {e}") from e

    template_dir = get_html_template_dir()

    # Verify template files exist
    template_html = template_dir / 'sankey_template.html'
    embed_js = template_dir / 'embed.js'

    if not template_html.exists():
        raise RuntimeError(
            f"HTML template not found at {template_html}. "
            "Package may be incorrectly installed."
        )
    if not embed_js.exists():
        raise RuntimeError(
            f"JavaScript file not found at {embed_js}. "
            "Package may be incorrectly installed."
        )

    try:
        # Copy HTML template
        index_html = out_path / 'index.html'
        shutil.copy(template_html, index_html)

        # Copy JS file
        out_js = out_path / 'embed.js'
        shutil.copy(embed_js, out_js)

        # Write trace data as JSON
        trace_json = out_path / 'trace.json'
        with open(trace_json, 'w') as f:
            f.write(trace_result_to_json(trace_result))
    except OSError as e:
        raise RuntimeError(f"Failed to write output files to '{out_dir}': {e}") from e

    if open_browser:
        webbrowser.open(f'file://{index_html.absolute()}')

    return str(index_html)
