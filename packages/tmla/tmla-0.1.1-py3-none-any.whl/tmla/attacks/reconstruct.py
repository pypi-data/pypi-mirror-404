"""Wavelet reconstruction and perturbation generation modules.

This module provides classes for reconstructing images from wavelet coefficients
and generating adversarial perturbations.
"""

import pytorch_wavelets


class Reconstruction:
    """Class for reconstructing images from wavelet coefficients.
    
    Args:
        wavelet: Wavelet type to use (default 'haar')
        device: Device for computation (default 'cpu')
    """
    
    def __init__(self, wavelet='haar', device='cpu'):
        """Initialize the reconstruction module."""
        self.idwt = pytorch_wavelets.DWTInverse(wave=wavelet).to(device)
        self.device = device

    def reconstruct(self, low, perturbed_details):
        """Reconstruct image from low and high frequency components.
        
        Args:
            low: Low frequency component
            perturbed_details: List of high frequency components
            
        Returns:
            torch.Tensor: Reconstructed image
        """
        # Ensure inputs are on the correct device
        low = low.to(self.device)
        perturbed_details = [d.to(self.device) for d in perturbed_details]
        # Reconstruct image
        return self.idwt((low, perturbed_details))
