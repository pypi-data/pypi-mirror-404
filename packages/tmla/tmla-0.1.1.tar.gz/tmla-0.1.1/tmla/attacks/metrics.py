"""Metrics module for image quality assessment.

This module provides various image quality metrics including PSNR, SSIM, VIF,
DISTS, and BPP calculations for evaluating compression and attack performance.
"""

import math
import piq
import torch
from piq import SSIMLoss
from torchmetrics.image import VisualInformationFidelity

# VIF measures mutual information between reference and distorted image
# Takes into account both linear and non-linear dependencies between pixels
# VIF values range from 0 to 1, where 1 indicates perfect accuracy
vif = VisualInformationFidelity()


def compute_psnr(original_image, compressed_image):
    """Compute Peak Signal-to-Noise Ratio (PSNR) between two images.
    
    Higher PSNR values indicate better image quality.
    
    Args:
        original_image: Reference image tensor
        compressed_image: Compressed/distorted image tensor
        
    Returns:
        float: PSNR value in decibels (dB)
    """
    mean_squared_error = torch.mean(
        (original_image - compressed_image) ** 2
    ).item()

    # PSNR = -10 * log10(MSE)
    psnr_value = -10 * math.log10(mean_squared_error)
    return psnr_value

def ssimloss(input, target, window_size=11):
    """Compute 1 - Structural Similarity Index Measure (SSIM).
    
    Evaluates visual quality by comparing structural similarities.
    
    Args:
        input: Input image tensor
        target: Target image tensor
        window_size: Size of window for computing local statistics
        
    Returns:
        torch.Tensor: SSIM loss value
    """
    ssim_loss = SSIMLoss(window_size)
    return ssim_loss(input, target)

def compute_bpp(network_output):
    """Compute bits per pixel (BPP) for the compressed image.
    
    Lower BPP means stronger compression.
    Higher BPP means better quality but larger file size.
    
    Args:
        network_output: Dictionary with output data containing:
            - x_hat: reconstructed image
            - likelihoods: probabilities for entropy coding
            
    Returns:
        float: Bits per pixel value
    """
    # (batch, channels, height, width)
    image_size = network_output['x_hat'].size()

    # Calculate total number of pixels
    total_pixels = image_size[0] * image_size[2] * image_size[3]

    # Calculate BPP as sum of log probabilities divided by number of pixels
    bits_per_pixel = sum(
        torch.log(prob).sum() / (-math.log(2) * total_pixels)
        for prob in network_output['likelihoods'].values()
    ).item()
    return bits_per_pixel

def dists(input, target):
    """Compute the DISTS metric between input and target images.
    
    Args:
        input: Input image tensor
        target: Target image tensor
        
    Returns:
        torch.Tensor: DISTS metric value
    """
    dists_loss = piq.DISTS(reduction="none")
    return dists_loss(input, target)

def bpp_loss(output, num_pixels):
    """Calculate bits per pixel for compressed image.
    
    Args:
        output: Model output dictionary with likelihoods
        num_pixels: Total number of pixels in the image
        
    Returns:
        torch.Tensor: BPP loss value
    """
    bpp = sum(
        torch.log(likelihoods).sum() / (-math.log(2) * num_pixels)
        for likelihoods in output["likelihoods"].values()
    )
    return bpp

def ssim(input, target, window_size=11):
    """Compute SSIM loss between input and target images.
    
    Args:
        input: Input image tensor
        target: Target image tensor
        window_size: Size of the sliding window (default 11)
        
    Returns:
        torch.Tensor: SSIM loss value
    """
    ssim_loss = SSIMLoss(window_size=window_size)
    return ssim_loss(input, target)
