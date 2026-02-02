"""Evaluation utilities for image compression model performance.

This module provides functions for evaluating compression models including
PSNR, BPP, SSIM, and VIF calculations on original and perturbed images.
"""

import os
import math
import numpy as np
import piq
import torch
import torch.nn.functional as F
# Local imports
from tmla.attacks.metrics import ssimloss, vif, dists
from tmla.utils.file_utils import savecompressed


def eval_perf(model, original_image, img_path):
    """Evaluate basic compression model performance.
    
    Calculates:
    - PSNR between original and reconstructed image
    - Bpp (Bits per pixel) - theoretical and actual compressed file size
    - SSIM for visual quality assessment
    
    Args:
        model: Compression model (on GPU)
        original_image: Original input image tensor
        img_path: Path to image file
    
    Returns:
        dict: Dictionary with metrics (PSNR, Bpp, Bpp(fsize), SSIMLoss)
    """
    MAX_PIXEL_VALUE = 1
    num_pixels = original_image.shape[2] * original_image.shape[3]

    with torch.no_grad():
        # Get reconstructed image
        model_output = model.forward(original_image)
        reconstructed_image = model_output["x_hat"].clamp_(0, 1)

        # Calculate PSNR: higher mse means lower psnr and worse image quality
        mse_loss = F.mse_loss(reconstructed_image, original_image)
        psnr_value = 10 * torch.log10((MAX_PIXEL_VALUE**2) / mse_loss)

        # Calculate theoretical Bpp. Two latent code streams: y and z.
        # y is the main image representation, z is hyper-prior.
        # that help better compress y
        bpp_theoretical = (
            torch.log(model_output["likelihoods"]["y"]).sum()
            + torch.log(model_output["likelihoods"]["z"]).sum()
        ) / (-math.log(2) * num_pixels)
        # Theoretical - estimate before actual arithmetic coder

        # Calculate SSIM
        ssimloss_value = ssimloss(reconstructed_image, original_image)

        # Compress the image
        compressed_data = model.compress(original_image)

        bytes_y = sum(len(s) for s in compressed_data['strings'][0])
        bytes_z = sum(len(s) for s in compressed_data['strings'][1])
        size_bytes = bytes_y + bytes_z
        # 8-bit RGB
        raw_bytes = (
            original_image.shape[2]
            * original_image.shape[3]
            * original_image.shape[1]
        )
        compression_ratio = raw_bytes / size_bytes
        print(f'Compression ratio: {compression_ratio:.1f}x')

    # Create unique name for compressed file
    unique_id = np.random.randint(1000, 9999)
    compressed_filename = (
        os.path.splitext(img_path)[0] + "compress" + str(unique_id)
    )

    # Save compressed file and get actual Bpp
    height, width = original_image.size(2), original_image.size(3)
    bpp_actual = savecompressed(
        compressed_filename, compressed_data, bitdepth=8, h=height, w=width
    )

    return {
        "PSNR": psnr_value.cpu().detach().numpy(),
        "Bpp": bpp_theoretical.cpu().detach().numpy(),
        "Bpp(fsize)": bpp_actual,
        "SSIMLoss": ssimloss_value.cpu().detach().numpy(),
    }


def eval_perf_full(model, perturbed_image, original_image, img_path):
    """Extended performance evaluation with additional metrics.
    
    Calculates:
    - PSNR between original image and perturbed input
    - VIF for assessing visual information preservation
    - LPIPS and DISTS to evaluate perceptual similarity
    - All metrics from eval_perf()
    
    Args:
        model: Compression model (on GPU)
        perturbed_image: Perturbed input image tensor
        original_image: Original image tensor
        img_path: Path to image file
    
    Returns:
        dict: Dictionary with extended set of metrics
    """

    MAX_PIXEL_VALUE = 1
    num_pixels = perturbed_image.shape[2] * perturbed_image.shape[3]

    with torch.no_grad():
        # Get reconstructed image from perturbed input
        model_output = model.forward(perturbed_image)
        reconstructed_image = model_output["x_hat"].clamp_(0, 1)

        # PSNR between reconstructed and perturbed
        mse_loss = F.mse_loss(reconstructed_image, perturbed_image)
        psnr_ao = 10 * torch.log10((MAX_PIXEL_VALUE**2) / mse_loss)

        # Theoretical Bpp
        bpp_theoretical = (
            torch.log(model_output["likelihoods"]["y"]).sum()
            + torch.log(model_output["likelihoods"]["z"]).sum()
        ) / (-math.log(2) * num_pixels)

        # SSIM between reconstructed and original
        ssimloss_value = ssimloss(reconstructed_image, original_image)

        # Perceptual metrics
        lpips_metric = piq.LPIPS(reduction="none").to(perturbed_image.device)
        lpips_ai_oi = lpips_metric(perturbed_image, original_image)
        lpips_ao_oi = lpips_metric(reconstructed_image, original_image)

        dists_ai_oi = dists(perturbed_image, original_image)
        dists_ao_oi = dists(reconstructed_image, original_image)

        # Compress perturbed image
        compressed_data = model.compress(perturbed_image)

    # Save the compressed file
    unique_id = np.random.randint(1000, 9999)
    compressed_filename = (
        os.path.splitext(img_path)[0] + "compress" + str(unique_id)
    )
    height, width = perturbed_image.size(2), perturbed_image.size(3)
    bpp_actual = savecompressed(
        compressed_filename, compressed_data, bitdepth=8, h=height, w=width
    )
    
    # Calculate VIF metrics
    vif_score_in = vif(original_image, perturbed_image)
    vif_score_out = vif(original_image, reconstructed_image)

    # PSNR between original and perturbed
    mse_perturbed_original = F.mse_loss(original_image, perturbed_image)
    psnr_ai_oi = 10 * torch.log10(
        (MAX_PIXEL_VALUE ** 2) / mse_perturbed_original
    )

    return {
        # PSNR between perturbed and reconstructed
        "PSNR(ai,ao)": psnr_ao.cpu().detach().numpy(),
        # PSNR between perturbed and original
        "PSNR(ai,oi)": psnr_ai_oi.cpu().detach().numpy(),
        # Theoretical BPP
        "Bpp": bpp_theoretical.cpu().detach().numpy(),
        # Actual BPP
        "Bpp(fsize)": bpp_actual,
        # SSIM Loss = 1 - SSIM
        "SSIMLoss(ao)": ssimloss_value.cpu().detach().numpy(),
        # VIF between perturbed and original
        "VIF(ai,oi)": vif_score_in.cpu().detach().numpy(),
        # VIF between reconstructed and original
        "VIF(ao,oi)": vif_score_out.cpu().detach().numpy(),
        # LPIPS between perturbed and original
        "LPIPS(ai,oi)": lpips_ai_oi.mean().cpu().detach().numpy(),
        # LPIPS between reconstructed and original
        "LPIPS(ao,oi)": lpips_ao_oi.mean().cpu().detach().numpy(),
        # DISTS between perturbed and original
        "DISTS(ai,oi)": dists_ai_oi.mean().cpu().detach().numpy(),
        # DISTS between reconstructed and original
        "DISTS(ao,oi)": dists_ao_oi.mean().cpu().detach().numpy(),
    }
