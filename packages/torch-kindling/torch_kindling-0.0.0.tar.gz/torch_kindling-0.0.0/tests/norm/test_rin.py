"""Tests for reversible instance normalization."""

import pytest
import torch

from torch_kindling.norm import RIN


def test_rin_forward_3d():
    """Test RIN forward pass with 3D input (batch, seq_len, features)."""
    rin = RIN()
    x = torch.randn(8, 100, 64)
    x_norm = rin(x)

    assert x_norm.shape == x.shape
    assert torch.allclose(x_norm.mean(dim=1), torch.tensor(0.0), atol=rin.eps)


def test_rin_forward_2d():
    """Test RIN forward pass with 2D input (batch, features)."""
    rin = RIN()
    x = torch.randn(8, 64)
    x_norm = rin(x)

    assert x_norm.shape == x.shape


def test_rin_reverse():
    """Test that reverse recovers original values."""
    rin = RIN()
    x = torch.randn(8, 100, 64)
    x_norm = rin(x)
    x_reverse = rin.reverse(x_norm)

    assert torch.allclose(x, x_reverse, atol=rin.eps)


def test_rin_reverse_without_forward():
    """Test that reverse raises error if forward not called."""
    rin = RIN()
    x = torch.randn(8, 100, 64)

    with pytest.raises(RuntimeError, match="reverse\\(\\) called before forward"):
        rin.reverse(x)


def test_rin_affine():
    """Test RIN with learnable affine parameters."""
    rin = RIN(affine=True)
    x = torch.randn(8, 100, 64)
    x_norm = rin(x)
    x_reverse = rin.reverse(x_norm)

    assert torch.allclose(x, x_reverse, atol=rin.eps)


def test_rin_invalid_shape():
    """Test that invalid input shapes raise error."""
    rin = RIN()
    x = torch.randn(8, 100, 64, 32)  # 4D

    with pytest.raises(ValueError, match="Expected 2D or 3D input"):
        rin(x)
