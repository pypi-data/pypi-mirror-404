"""Tests for beam search algorithm."""

import math

import pytest
import torch

from reverse_attention.beam import (
    BeamState,
    beam_search_backward,
    extend_beam,
    get_top_k_predecessors,
    prune_beams,
)
from reverse_attention.utils import normalize_score, safe_log


class TestGetTopKPredecessors:
    """Tests for get_top_k_predecessors function."""

    def test_basic_top_k(self):
        """Test basic top-k extraction."""
        # Create a simple attention matrix
        # Position 3 attends to positions 0, 1, 2
        attn = torch.tensor([
            [1.0, 0.0, 0.0, 0.0],  # pos 0
            [0.3, 0.7, 0.0, 0.0],  # pos 1
            [0.1, 0.2, 0.7, 0.0],  # pos 2
            [0.1, 0.5, 0.3, 0.1],  # pos 3 (query)
        ])

        result = get_top_k_predecessors(attn, query_pos=3, k=2, min_attn=0.0, attention_mask=None)

        assert len(result) == 2
        # Should return positions with highest attention
        assert result[0] == (1, 0.5)  # pos 1 has attention 0.5
        assert result[1] == (2, 0.3)  # pos 2 has attention 0.3

    def test_causal_masking(self):
        """Test that only positions < query_pos are considered."""
        attn = torch.tensor([
            [1.0, 0.8, 0.0, 0.0],  # pos 0 - high attention at pos 1 shouldn't matter
            [0.3, 0.7, 0.0, 0.0],
            [0.1, 0.2, 0.7, 0.0],
            [0.1, 0.5, 0.3, 0.1],
        ])

        result = get_top_k_predecessors(attn, query_pos=2, k=5, min_attn=0.0, attention_mask=None)

        # Should only include positions 0 and 1
        positions = [r[0] for r in result]
        assert all(p < 2 for p in positions)

    def test_min_attn_threshold(self):
        """Test minimum attention threshold."""
        attn = torch.tensor([
            [1.0, 0.0, 0.0, 0.0],
            [0.3, 0.7, 0.0, 0.0],
            [0.1, 0.2, 0.7, 0.0],
            [0.05, 0.5, 0.3, 0.15],  # pos 0 has 0.05, below threshold
        ])

        result = get_top_k_predecessors(attn, query_pos=3, k=5, min_attn=0.1, attention_mask=None)

        # Position 0 should be excluded (0.05 < 0.1)
        positions = [r[0] for r in result]
        assert 0 not in positions
        assert len(result) == 2  # Only positions 1 and 2

    def test_attention_mask(self):
        """Test that attention mask is applied."""
        attn = torch.tensor([
            [1.0, 0.0, 0.0, 0.0],
            [0.3, 0.7, 0.0, 0.0],
            [0.1, 0.2, 0.7, 0.0],
            [0.1, 0.5, 0.3, 0.1],
        ])
        # Mask out position 1
        mask = torch.tensor([1, 0, 1, 1])

        result = get_top_k_predecessors(attn, query_pos=3, k=5, min_attn=0.0, attention_mask=mask)

        # Position 1 should be excluded
        positions = [r[0] for r in result]
        assert 1 not in positions

    def test_empty_result_at_position_0(self):
        """Test that position 0 has no predecessors."""
        attn = torch.ones(4, 4)

        result = get_top_k_predecessors(attn, query_pos=0, k=5, min_attn=0.0, attention_mask=None)

        assert len(result) == 0


class TestExtendBeam:
    """Tests for extend_beam function."""

    def test_extend_beam(self):
        """Test basic beam extension."""
        beam = BeamState(positions=[5], edge_attns=[], log_score=0.0)
        new_beam = extend_beam(beam, pred_pos=3, attn_weight=0.5)

        assert new_beam.positions == [5, 3]
        assert len(new_beam.edge_attns) == 1
        assert new_beam.edge_attns[0] == 0.5
        assert abs(new_beam.log_score - safe_log(0.5)) < 1e-6
        assert not new_beam.is_terminal

    def test_extend_multiple_times(self):
        """Test extending beam multiple times."""
        beam = BeamState(positions=[5], edge_attns=[], log_score=0.0)
        beam = extend_beam(beam, 3, 0.5)
        beam = extend_beam(beam, 1, 0.3)

        assert beam.positions == [5, 3, 1]
        assert len(beam.edge_attns) == 2
        assert beam.current_pos == 1
        assert beam.num_edges == 2


class TestPruneBeams:
    """Tests for prune_beams function."""

    def test_prune_beams(self):
        """Test beam pruning to top_beam."""
        beams = [
            BeamState([5, 3], [0.5], safe_log(0.5)),
            BeamState([5, 2], [0.8], safe_log(0.8)),
            BeamState([5, 1], [0.3], safe_log(0.3)),
        ]

        pruned = prune_beams(beams, top_beam=2, length_norm="none")

        assert len(pruned) == 2
        # Higher score should be first
        assert pruned[0].positions == [5, 2]  # 0.8 has highest log
        assert pruned[1].positions == [5, 3]  # 0.5 is second

    def test_no_pruning_needed(self):
        """Test when fewer beams than top_beam."""
        beams = [
            BeamState([5, 3], [0.5], safe_log(0.5)),
        ]

        pruned = prune_beams(beams, top_beam=5, length_norm="none")

        assert len(pruned) == 1


class TestBeamSearchBackward:
    """Tests for beam_search_backward function."""

    def test_simple_path(self):
        """Test finding a simple path with clear winner."""
        # Create attention that clearly leads: 3 -> 2 -> 1 -> 0
        attn = torch.tensor([
            [1.0, 0.0, 0.0, 0.0],
            [0.9, 0.1, 0.0, 0.0],  # pos 1 strongly attends to 0
            [0.1, 0.8, 0.1, 0.0],  # pos 2 strongly attends to 1
            [0.1, 0.1, 0.7, 0.1],  # pos 3 strongly attends to 2
        ])

        beams = beam_search_backward(
            attn,
            target_pos=3,
            top_beam=1,
            top_k=2,
            min_attn=0.0,
        )

        assert len(beams) >= 1
        # Best path should be 3 -> 2 -> 1 -> 0
        best = beams[0]
        assert best.positions == [3, 2, 1, 0]

    def test_stop_at_bos(self):
        """Test stopping at BOS positions."""
        attn = torch.tensor([
            [1.0, 0.0, 0.0, 0.0],
            [0.5, 0.5, 0.0, 0.0],
            [0.3, 0.4, 0.3, 0.0],
            [0.2, 0.3, 0.4, 0.1],
        ])

        beams = beam_search_backward(
            attn,
            target_pos=3,
            top_beam=5,
            top_k=3,
            stop_at_bos=True,
            bos_positions=[1],  # Position 1 is BOS
        )

        # All beams should stop at position 0 or 1 (BOS)
        for beam in beams:
            assert beam.current_pos in [0, 1]

    def test_attention_mask(self):
        """Test attention mask excludes positions."""
        attn = torch.tensor([
            [1.0, 0.0, 0.0, 0.0],
            [0.5, 0.5, 0.0, 0.0],
            [0.3, 0.4, 0.3, 0.0],
            [0.2, 0.5, 0.2, 0.1],  # pos 1 has highest attention
        ])
        # Mask out position 1
        mask = torch.tensor([1, 0, 1, 1])

        beams = beam_search_backward(
            attn,
            target_pos=3,
            top_beam=5,
            top_k=3,
            attention_mask=mask,
        )

        # No beam should include position 1
        for beam in beams:
            assert 1 not in beam.positions

    def test_determinism(self):
        """Test that beam search is deterministic."""
        torch.manual_seed(42)
        attn = torch.rand(10, 10)
        # Make it causal
        attn = torch.tril(attn)

        result1 = beam_search_backward(attn, target_pos=9, top_beam=5, top_k=3)
        result2 = beam_search_backward(attn, target_pos=9, top_beam=5, top_k=3)

        assert len(result1) == len(result2)
        for b1, b2 in zip(result1, result2):
            assert b1.positions == b2.positions
            assert abs(b1.log_score - b2.log_score) < 1e-6


class TestNormalizeScore:
    """Tests for score normalization."""

    def test_normalize_none(self):
        """Test no normalization."""
        assert normalize_score(-5.0, 3, "none") == -5.0

    def test_normalize_avg_logprob(self):
        """Test average log probability normalization."""
        assert abs(normalize_score(-6.0, 3, "avg_logprob") - (-2.0)) < 1e-6

    def test_normalize_sqrt(self):
        """Test sqrt normalization."""
        expected = -6.0 / math.sqrt(3)
        assert abs(normalize_score(-6.0, 3, "sqrt") - expected) < 1e-6

    def test_normalize_pow(self):
        """Test power normalization."""
        expected = -6.0 / (3 ** 0.7)
        assert abs(normalize_score(-6.0, 3, "pow:0.7") - expected) < 1e-6

    def test_normalize_zero_length(self):
        """Test normalization with zero length."""
        assert normalize_score(-5.0, 0, "avg_logprob") == -5.0

    def test_invalid_mode(self):
        """Test invalid normalization mode raises error."""
        with pytest.raises(ValueError):
            normalize_score(-5.0, 3, "invalid")
