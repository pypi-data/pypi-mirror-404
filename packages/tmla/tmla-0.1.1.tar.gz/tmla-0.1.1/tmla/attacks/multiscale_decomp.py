"""Multi-scale wavelet decomposition module.

This module provides a class for performing multi-scale wavelet decomposition
of images using PyTorch Wavelets.
"""

import pytorch_wavelets


class MultiScaleDecomposition:
    """Class for multi-scale wavelet decomposition of an image.

    Parameters:
        wavelet: Wavelet type, defaults to 'haar'
        device: Computation device ('cpu' or 'cuda')
        scales: Number of decomposition levels (default 3)
    """
    def __init__(self, wavelet='haar', device='cpu', scales=3):
        # Initialize forward wavelet transform
        # scales is the number of decomposition levels
        self.wavelet_transform = pytorch_wavelets.DWTForward(
            J=scales, wave=wavelet
        ).to(device)
        self.device = device

    def decompose(self, x):
        """Decompose image into low and high frequency components.

        Args:
            x: Input image tensor

        Returns:
            tuple: (low_freq, high_freq_details) where:
                - low_freq: Low frequency component
                - high_freq_details: List of high frequency components
                  for each level
        """
        x = x.to(self.device)
        low_freq, high_freq_details = self.wavelet_transform(x)
        return low_freq, high_freq_details
