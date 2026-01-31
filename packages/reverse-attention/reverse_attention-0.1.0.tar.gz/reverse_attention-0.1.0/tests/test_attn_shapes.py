"""Tests for attention extraction shapes."""

import pytest
import torch
from unittest.mock import MagicMock, patch


class MockAttentionOutput:
    """Mock attention output from a transformer model."""

    def __init__(self, batch_size=1, num_heads=8, seq_len=10, num_layers=4):
        self.attentions = tuple(
            torch.rand(batch_size, num_heads, seq_len, seq_len)
            for _ in range(num_layers)
        )


class TestAttentionExtraction:
    """Tests for attention extraction functionality."""

    def test_mean_aggregation_shape(self):
        """Test that mean aggregation produces [seq_len, seq_len]."""
        from reverse_attention.attn_extract import extract_attention

        # Create mock model
        model = MagicMock()
        model.parameters.return_value = iter([torch.zeros(1)])

        batch_size, num_heads, seq_len, num_layers = 1, 8, 10, 4
        mock_output = MockAttentionOutput(batch_size, num_heads, seq_len, num_layers)
        model.return_value = mock_output

        input_ids = torch.randint(0, 1000, (1, seq_len))

        attn, layer = extract_attention(model, input_ids, None, layer=-1, agg_heads="mean")

        assert attn.shape == (seq_len, seq_len)
        assert layer == num_layers - 1

    def test_max_aggregation_shape(self):
        """Test that max aggregation produces [seq_len, seq_len]."""
        from reverse_attention.attn_extract import extract_attention

        model = MagicMock()
        model.parameters.return_value = iter([torch.zeros(1)])

        batch_size, num_heads, seq_len, num_layers = 1, 8, 10, 4
        mock_output = MockAttentionOutput(batch_size, num_heads, seq_len, num_layers)
        model.return_value = mock_output

        input_ids = torch.randint(0, 1000, (1, seq_len))

        attn, layer = extract_attention(model, input_ids, None, layer=-1, agg_heads="max")

        assert attn.shape == (seq_len, seq_len)

    def test_none_aggregation_shape(self):
        """Test that none aggregation produces [heads, seq_len, seq_len]."""
        from reverse_attention.attn_extract import extract_attention

        model = MagicMock()
        model.parameters.return_value = iter([torch.zeros(1)])

        batch_size, num_heads, seq_len, num_layers = 1, 8, 10, 4
        mock_output = MockAttentionOutput(batch_size, num_heads, seq_len, num_layers)
        model.return_value = mock_output

        input_ids = torch.randint(0, 1000, (1, seq_len))

        attn, layer = extract_attention(model, input_ids, None, layer=-1, agg_heads="none")

        assert attn.shape == (num_heads, seq_len, seq_len)

    def test_negative_layer_indexing(self):
        """Test negative layer indexing."""
        from reverse_attention.attn_extract import extract_attention

        model = MagicMock()
        model.parameters.return_value = iter([torch.zeros(1)])

        batch_size, num_heads, seq_len, num_layers = 1, 8, 10, 4
        mock_output = MockAttentionOutput(batch_size, num_heads, seq_len, num_layers)
        model.return_value = mock_output

        input_ids = torch.randint(0, 1000, (1, seq_len))

        # Test -1 (last layer)
        _, layer = extract_attention(model, input_ids, None, layer=-1, agg_heads="mean")
        assert layer == 3

        # Test -2 (second to last)
        _, layer = extract_attention(model, input_ids, None, layer=-2, agg_heads="mean")
        assert layer == 2

    def test_positive_layer_indexing(self):
        """Test positive layer indexing."""
        from reverse_attention.attn_extract import extract_attention

        model = MagicMock()
        model.parameters.return_value = iter([torch.zeros(1)])

        batch_size, num_heads, seq_len, num_layers = 1, 8, 10, 4
        mock_output = MockAttentionOutput(batch_size, num_heads, seq_len, num_layers)
        model.return_value = mock_output

        input_ids = torch.randint(0, 1000, (1, seq_len))

        # Test layer 0
        _, layer = extract_attention(model, input_ids, None, layer=0, agg_heads="mean")
        assert layer == 0

        # Test layer 2
        _, layer = extract_attention(model, input_ids, None, layer=2, agg_heads="mean")
        assert layer == 2

    def test_layer_out_of_range(self):
        """Test that out-of-range layer raises error."""
        from reverse_attention.attn_extract import extract_attention

        model = MagicMock()
        model.parameters.return_value = iter([torch.zeros(1)])

        batch_size, num_heads, seq_len, num_layers = 1, 8, 10, 4
        mock_output = MockAttentionOutput(batch_size, num_heads, seq_len, num_layers)
        model.return_value = mock_output

        input_ids = torch.randint(0, 1000, (1, seq_len))

        with pytest.raises(ValueError, match="out of range"):
            extract_attention(model, input_ids, None, layer=10, agg_heads="mean")

    def test_invalid_agg_heads(self):
        """Test invalid agg_heads mode raises error."""
        from reverse_attention.attn_extract import extract_attention

        model = MagicMock()
        model.parameters.return_value = iter([torch.zeros(1)])

        batch_size, num_heads, seq_len, num_layers = 1, 8, 10, 4
        mock_output = MockAttentionOutput(batch_size, num_heads, seq_len, num_layers)
        model.return_value = mock_output

        input_ids = torch.randint(0, 1000, (1, seq_len))

        with pytest.raises(ValueError, match="Unknown agg_heads"):
            extract_attention(model, input_ids, None, layer=-1, agg_heads="invalid")


class TestAttentionMask:
    """Tests for attention mask handling."""

    def test_get_attention_mask_passthrough(self):
        """Test that provided mask is returned unchanged."""
        from reverse_attention.attn_extract import get_attention_mask

        input_ids = torch.randint(0, 1000, (1, 10))
        mask = torch.ones(1, 10)

        tokenizer = MagicMock()

        result = get_attention_mask(input_ids, tokenizer, mask)

        assert torch.equal(result, mask)

    def test_get_attention_mask_from_pad_token(self):
        """Test mask creation from pad token."""
        from reverse_attention.attn_extract import get_attention_mask

        # Input with pad tokens at the end
        input_ids = torch.tensor([[1, 2, 3, 0, 0]])  # 0 is pad token

        tokenizer = MagicMock()
        tokenizer.pad_token_id = 0

        result = get_attention_mask(input_ids, tokenizer, None)

        expected = torch.tensor([[1, 1, 1, 0, 0]])
        assert torch.equal(result, expected)

    def test_get_attention_mask_no_pad_token(self):
        """Test mask creation when no pad token defined."""
        from reverse_attention.attn_extract import get_attention_mask

        input_ids = torch.tensor([[1, 2, 3, 4, 5]])

        tokenizer = MagicMock()
        tokenizer.pad_token_id = None

        result = get_attention_mask(input_ids, tokenizer, None)

        expected = torch.ones_like(input_ids)
        assert torch.equal(result, expected)
