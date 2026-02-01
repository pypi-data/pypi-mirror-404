"""Reversible Instance Normalization (RIN) for time series."""

import torch
import torch.nn as nn


class RIN(nn.Module):
    """Reversible Instance Normalization.

    Normalizes each instance (sample) independently along the feature dimension,
    storing scale and bias for later denormalization. Commonly used in time series
    forecasting to stabilize training.

    Reference:
        Kim, T., Kim, J., Tae, Y., Park, C., Choi, J. H., & Choo, J. (2022).
        Reversible Instance Normalization for Accurate Time-Series Forecasting
        against Distribution Shift. In International Conference on Learning
        Representations (ICLR 2022).
        https://openreview.net/forum?id=cGDAkQo1C0p

    Args:
        eps (float): Small constant for numerical stability. Default: 1e-5.
        affine (bool): If True, learn affine parameters (scale, shift). Default: False.

    Shape:
        - Input: (batch, seq_len, features) or (batch, features)
        - Output: Same as input

    Example:
        >>> rin = RIN()
        >>> x = torch.randn(32, 100, 64)  # (batch, seq_len, features)
        >>> x_norm = rin(x)
        >>> x_denorm = rin.reverse(x_norm)  # Recover original scale/shift
    """

    def __init__(self, eps: float = 1e-5, affine: bool = False):
        super().__init__()
        self.eps = eps
        self.affine = affine

        if affine:
            self.weight = nn.Parameter(torch.ones(1))
            self.bias = nn.Parameter(torch.zeros(1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Normalize input.

        Args:
            x: Input tensor of shape (batch, seq_len, features) or (batch, features).

        Returns:
            Normalized tensor and stores mean/std for denormalization.
        """
        # Handle 2D and 3D inputs
        if x.dim() == 2:
            # Shape: (batch, features)
            mean = x.mean(dim=1, keepdim=True)
            std = x.std(dim=1, keepdim=True, unbiased=False)
        elif x.dim() == 3:
            # Shape: (batch, seq_len, features)
            mean = x.mean(dim=1, keepdim=True)
            std = x.std(dim=1, keepdim=True, unbiased=False)
        else:
            raise ValueError(f"Expected 2D or 3D input, got {x.dim()}D")

        # Store for denormalization
        self.mean = mean.detach()
        self.std = std.detach()

        # Normalize
        x_norm = (x - mean) / (std + self.eps)

        # Apply affine transformation if enabled
        if self.affine:
            x_norm = x_norm * self.weight + self.bias

        return x_norm

    def reverse(self, x: torch.Tensor) -> torch.Tensor:
        """Reverse normalization.

        Args:
            x: Normalized tensor.

        Returns:
            Denormalized tensor with original scale and shift restored.
        """
        if not hasattr(self, "mean") or not hasattr(self, "std"):
            raise RuntimeError(
                "reverse() called before forward(). "
                "Must call forward() first to store normalization statistics."
            )

        # Reverse affine transformation if it was applied
        if self.affine:
            x = (x - self.bias) / (self.weight + self.eps)

        # Denormalize
        x_denorm = x * (self.std + self.eps) + self.mean

        return x_denorm
