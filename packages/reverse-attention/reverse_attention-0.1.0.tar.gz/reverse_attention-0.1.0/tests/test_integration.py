"""Integration tests for reverse_attention package."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import torch

from reverse_attention import ReverseAttentionTracer, BeamPath, TraceResult
from reverse_attention.beam import SankeyData, SankeyNode, SankeyLink


class MockTokenizer:
    """Mock tokenizer for testing."""

    def __init__(self):
        self.bos_token_id = 0
        self.eos_token_id = 1
        self.pad_token_id = 2
        self.vocab = {
            0: "<bos>",
            1: "<eos>",
            2: "<pad>",
            3: "The",
            4: " quick",
            5: " brown",
            6: " fox",
        }

    def decode(self, token_ids):
        return "".join(self.vocab.get(tid, f"[{tid}]") for tid in token_ids)

    def __call__(self, text, return_tensors=None):
        # Simple mock tokenization
        result = {"input_ids": torch.tensor([[0, 3, 4, 5, 6, 1]])}
        if return_tensors == "pt":
            result["attention_mask"] = torch.ones_like(result["input_ids"])
        return result


class MockAttentionOutput:
    """Mock model output with attention."""

    def __init__(self, num_layers=4, num_heads=8, seq_len=6):
        # Create causal attention patterns
        self.attentions = []
        for _ in range(num_layers):
            attn = torch.rand(1, num_heads, seq_len, seq_len)
            # Apply causal mask
            causal_mask = torch.tril(torch.ones(seq_len, seq_len))
            attn = attn * causal_mask.unsqueeze(0).unsqueeze(0)
            # Normalize
            attn = attn / (attn.sum(dim=-1, keepdim=True) + 1e-10)
            self.attentions.append(attn)
        self.attentions = tuple(self.attentions)


class MockModel:
    """Mock transformer model for testing."""

    def __init__(self, num_layers=4, num_heads=8):
        self.num_layers = num_layers
        self.num_heads = num_heads
        self._params = [torch.zeros(1)]

    def parameters(self):
        return iter(self._params)

    def eval(self):
        return self

    def __call__(self, input_ids, attention_mask=None, output_attentions=False, use_cache=True):
        seq_len = input_ids.shape[1]
        return MockAttentionOutput(self.num_layers, self.num_heads, seq_len)


class TestReverseAttentionTracer:
    """Tests for ReverseAttentionTracer class."""

    def test_init(self):
        """Test tracer initialization."""
        model = MockModel()
        tokenizer = MockTokenizer()

        tracer = ReverseAttentionTracer(model, tokenizer)

        assert tracer.model is model
        assert tracer.tokenizer is tokenizer

    def test_trace_basic(self):
        """Test basic trace functionality."""
        model = MockModel()
        tokenizer = MockTokenizer()
        tracer = ReverseAttentionTracer(model, tokenizer)

        input_ids = torch.tensor([[0, 3, 4, 5, 6, 1]])

        result = tracer.trace(input_ids)

        assert isinstance(result, TraceResult)
        assert result.seq_len == 6
        assert result.target_pos == 5  # Last position
        assert len(result.beams) > 0
        assert len(result.tokens) == 6

    def test_trace_with_target_pos(self):
        """Test trace with specific target position."""
        model = MockModel()
        tokenizer = MockTokenizer()
        tracer = ReverseAttentionTracer(model, tokenizer)

        input_ids = torch.tensor([[0, 3, 4, 5, 6, 1]])

        result = tracer.trace(input_ids, target_pos=3)

        assert result.target_pos == 3

    def test_trace_negative_target_pos(self):
        """Test trace with negative target position."""
        model = MockModel()
        tokenizer = MockTokenizer()
        tracer = ReverseAttentionTracer(model, tokenizer)

        input_ids = torch.tensor([[0, 3, 4, 5, 6, 1]])

        result = tracer.trace(input_ids, target_pos=-2)

        assert result.target_pos == 4  # -2 from length 6

    def test_trace_text(self):
        """Test trace_text convenience method."""
        model = MockModel()
        tokenizer = MockTokenizer()
        tracer = ReverseAttentionTracer(model, tokenizer)

        result = tracer.trace_text("The quick brown fox")

        assert isinstance(result, TraceResult)
        assert result.seq_len > 0

    def test_trace_invalid_input_shape(self):
        """Test that invalid input shape raises error."""
        model = MockModel()
        tokenizer = MockTokenizer()
        tracer = ReverseAttentionTracer(model, tokenizer)

        # Batch size > 1
        input_ids = torch.tensor([[0, 3, 4], [0, 3, 4]])

        with pytest.raises(ValueError, match="Expected input_ids shape"):
            tracer.trace(input_ids)

    def test_trace_target_out_of_range(self):
        """Test that out-of-range target position raises error."""
        model = MockModel()
        tokenizer = MockTokenizer()
        tracer = ReverseAttentionTracer(model, tokenizer)

        input_ids = torch.tensor([[0, 3, 4, 5, 6, 1]])

        with pytest.raises(ValueError, match="out of range"):
            tracer.trace(input_ids, target_pos=10)


class TestSankeyGeneration:
    """Tests for Sankey diagram generation."""

    def test_beams_to_sankey(self):
        """Test Sankey data generation from beams."""
        from reverse_attention.sankey import beams_to_sankey

        beams = [
            BeamPath(
                positions=[5, 3, 1],
                tokens=["fox", "quick", "The"],
                token_ids=[6, 4, 3],
                edge_attns=[0.5, 0.3],
                score_raw=-1.5,
                score_norm=-0.75,
            ),
            BeamPath(
                positions=[5, 4, 2],
                tokens=["fox", "brown", "quick"],
                token_ids=[6, 5, 4],
                edge_attns=[0.4, 0.6],
                score_raw=-1.2,
                score_norm=-0.6,
            ),
        ]
        tokens = ["<bos>", "The", "quick", "brown", "fox", "<eos>"]

        sankey = beams_to_sankey(beams, tokens)

        assert isinstance(sankey, SankeyData)
        assert len(sankey.nodes) > 0
        assert len(sankey.links) > 0

        # Check that all positions are represented as nodes
        node_positions = {n.position for n in sankey.nodes}
        expected_positions = {1, 2, 3, 4, 5}  # All positions from beams
        assert node_positions == expected_positions

    def test_sankey_to_json(self):
        """Test Sankey data serialization."""
        from reverse_attention.sankey import sankey_to_dict

        sankey = SankeyData(
            nodes=[
                SankeyNode(id="L0_P0", name="hello", position=0),
                SankeyNode(id="L0_P1", name="world", position=1),
            ],
            links=[
                SankeyLink(source="L0_P0", target="L0_P1", value=0.5, beam_indices=[0]),
            ],
        )

        data = sankey_to_dict(sankey)

        assert "nodes" in data
        assert "links" in data
        assert len(data["nodes"]) == 2
        assert len(data["links"]) == 1


class TestHTMLRendering:
    """Tests for HTML visualization rendering."""

    def test_render_html_creates_files(self):
        """Test that render_html creates expected files."""
        model = MockModel()
        tokenizer = MockTokenizer()
        tracer = ReverseAttentionTracer(model, tokenizer)

        input_ids = torch.tensor([[0, 3, 4, 5, 6, 1]])
        result = tracer.trace(input_ids)

        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = tracer.render_html(result, tmpdir)

            # Check files exist
            assert os.path.exists(html_path)
            assert os.path.exists(os.path.join(tmpdir, "embed.js"))
            assert os.path.exists(os.path.join(tmpdir, "trace.json"))

    def test_trace_json_valid(self):
        """Test that generated trace.json is valid JSON."""
        model = MockModel()
        tokenizer = MockTokenizer()
        tracer = ReverseAttentionTracer(model, tokenizer)

        input_ids = torch.tensor([[0, 3, 4, 5, 6, 1]])
        result = tracer.trace(input_ids)

        with tempfile.TemporaryDirectory() as tmpdir:
            tracer.render_html(result, tmpdir)

            json_path = os.path.join(tmpdir, "trace.json")
            with open(json_path) as f:
                data = json.load(f)

            # Check structure
            assert "metadata" in data
            assert "tokens" in data
            assert "beams" in data
            assert "sankey" in data
            assert "paths_text" in data


class TestTokenization:
    """Tests for tokenization helpers."""

    def test_get_token_strings(self):
        """Test token string extraction."""
        from reverse_attention.tokenize import get_token_strings

        tokenizer = MockTokenizer()
        input_ids = torch.tensor([[0, 3, 4, 5, 6, 1]])

        tokens = get_token_strings(input_ids, tokenizer)

        assert len(tokens) == 6
        assert tokens[0] == "<bos>"
        assert tokens[1] == "The"

    def test_get_bos_positions(self):
        """Test BOS position detection."""
        from reverse_attention.tokenize import get_bos_positions

        tokenizer = MockTokenizer()
        input_ids = torch.tensor([[0, 3, 4, 0, 5, 6]])  # BOS at 0 and 3

        positions = get_bos_positions(input_ids, tokenizer)

        assert positions == [0, 3]

    def test_format_path_text(self):
        """Test path text formatting."""
        from reverse_attention.tokenize import format_path_text

        path = BeamPath(
            positions=[5, 3, 1],
            tokens=["fox", "quick", "The"],
            token_ids=[6, 4, 3],
            edge_attns=[0.5, 0.3],
            score_raw=-1.5,
            score_norm=-0.75,
        )

        text = format_path_text(path)

        # Should be reversed (earlier tokens first)
        assert "The" in text
        assert "fox" in text
        assert "-0.75" in text


class TestImports:
    """Test that public API is correctly exported."""

    def test_public_imports(self):
        """Test that main classes can be imported."""
        from reverse_attention import (
            ReverseAttentionTracer,
            BeamPath,
            BeamState,
            TraceResult,
            SankeyData,
            SankeyNode,
            SankeyLink,
        )

        assert ReverseAttentionTracer is not None
        assert BeamPath is not None
        assert TraceResult is not None
