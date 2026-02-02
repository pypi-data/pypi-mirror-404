"""Image utilities for visualization and wavelet decomposition.

This module provides functions for visualizing wavelet coefficients,
multiscale decompositions, and attack results.
"""

import matplotlib.pyplot as plt
import numpy as np
import pytorch_wavelets

def visualize_all_wavelet_details(details, channel=0, cmap='bwr'):
    """Visualize wavelet coefficients at all scales and bands.

    Args:
        details (list of torch.Tensor): List of tensors [1, C, 3, H, W]
        channel (int): Which input channel to visualize
        cmap (str): Colormap for display
    """
    num_scales = len(details)
    num_bands = 3  # high-frequency bands (LH, HL, HH)

    _, axes = plt.subplots(
        num_scales, num_bands, figsize=(num_bands * 4, num_scales * 4)
    )
    if num_scales == 1:
        axes = axes[None, :]  # ensure 2D indexing if only one scale

    for scale_idx, detail in enumerate(details):
        for band_idx in range(num_bands):
            ax = axes[scale_idx, band_idx]
            coeff = detail[0, channel, band_idx].detach().cpu().numpy()
            coeff /= (np.max(np.abs(coeff)) + 1e-8)  # normalize for display

            vmax = np.max(np.abs(coeff))
            ax.imshow(coeff, cmap=cmap, vmin=-vmax, vmax=vmax)
            ax.set_title(
                f"Scale {scale_idx+1}, Band {['LH','HL','HH'][band_idx]}"
            )
            ax.axis("off")

    plt.tight_layout()
    plt.show()


def print_decomposition_info(x, decomposer):
    """Print information about multiscale decomposition of an image.

    Args:
        x (torch.Tensor): Input image tensor of shape [B, C, H, W]
        decomposer (MultiScaleDecomposition): Decomposition object
    """
    low, details = decomposer.decompose(x)

    print(f"image shape: {x.shape}")  # [B, C, H, W]

    H0, W0 = x.shape[2], x.shape[3]
    
    print("\nPairs (L, H) by scale")
    for lvl, h in enumerate(details, start=1):
        # low part dimensions: half of original (divided by 2 each step)
        lh, lw = H0 // 2**lvl, W0 // 2**lvl
        print(f"\nScale {lvl}:")
        print(
            f"  L^{lvl}  shape: (B={x.shape[0]}, C={x.shape[1]}, "
            f"H={lh}, W={lw})"
        )
        print(f"  H^{lvl}  shape: {h.shape}")  # h = [B, C, 3, H, W]
    
    # coarsest low frequency L^S = low
    print(f"\nCoarsest L^{len(details)} (low) shape: {low.shape}")
    
    return low, details


def visualize_multiscale_decomposition(
    x, scales=3, wavelet='haar', device='cuda'
):
    """Visualize multiscale wavelet decomposition of an image.

    Args:
        x (torch.Tensor): Input image tensor of shape [B, C, H, W]
        scales (int): Number of decomposition scales
        wavelet (str): Wavelet type to use
        device (str): Device to run computation on
    """
    Ls, Hs = [], []
    x_cur = x  # (1,3,H,W)

    # Display original image
    plt.figure()
    plt.imshow(tensor_to_rgb(x.squeeze(0)))
    print(f'Original image: {x.shape}')
    plt.axis('off')
    plt.show()

    for _ in range(scales):
        # Use single-level DWT to avoid getting same two levels each time
        dwt = pytorch_wavelets.DWTForward(J=1, wave=wavelet).to(device)
        L, H = dwt(x_cur)  # H is list of length 1: [(B,C,3,h,w)]
        Ls.append(L)  # L^(s)
        Hs.append(H[0])  # H^(s)
        x_cur = L  # decompose current L in next iteration

    for s, (L, H) in enumerate(zip(Ls, Hs), start=1):
        H = H.squeeze(0)  # (C, 3, h, w)

        # Aggregate details: mean |H| across color and orientations
        detail_map = H.abs().mean(dim=(0, 1))  # (h, w)
        detail_map = (
            (detail_map - detail_map.min()) /
            (detail_map.max() - detail_map.min() + 1e-8)
        )

        _, ax = plt.subplots(1, 2, figsize=(7, 4))
        ax[0].imshow(tensor_to_rgb(L.squeeze(0)))
        print(f'L^{s} (approx): {L.shape}')
        ax[0].axis('off')

        ax[1].imshow(detail_map.cpu(), cmap='gray')
        print(f'|H|^{s} (all details): {detail_map.shape}')
        ax[1].axis('off')

        plt.tight_layout()
        plt.show()

def vis_results(perturbed_image, perturbed_output, smoothed_noise_pattern):
    """Visualize attack results including perturbed image, output, and noise.
    
    Args:
        perturbed_image: Adversarially perturbed input image
        perturbed_output: Compressed and reconstructed output
        smoothed_noise_pattern: Noise pattern used in attack
    """
    plt.figure(1)
    plt.imshow(
        perturbed_image.squeeze().cpu().detach().numpy().transpose(1, 2, 0)
    )
    plt.axis("off")
    plt.show()

    plt.figure(2)
    plt.imshow(
        perturbed_output.squeeze().cpu().detach().numpy().transpose(1, 2, 0)
    )
    plt.axis("off")
    plt.show()

    plt.figure(3)

    # Handle case where smoothed_noise_pattern is a list
    if isinstance(smoothed_noise_pattern, list):
        # Assuming first element contains the main noise pattern
        noise_pattern = smoothed_noise_pattern[0]
    else:
        noise_pattern = smoothed_noise_pattern

    # Find min and max values for normalization
    noise_array = (
        noise_pattern.squeeze()
        .cpu()
        .detach()
        .numpy()
        .transpose(1, 2, 0)
    )
    minn = np.min(noise_array.ravel())
    maxn = np.max(noise_array.ravel())
    
    # Normalize noise to [0,1] range for visualization
    plt.imshow((noise_array - minn) / (maxn - minn))
    plt.axis("off")
    plt.show()

def tensor_to_rgb(t):
    """Convert tensor (3,H,W) or (H,W) to RGB (H,W,3) in range [0,1].
    
    Args:
        t: Input tensor of shape (3,H,W) or (H,W)
        
    Returns:
        numpy.ndarray: RGB array of shape (H,W,3) in range [0,1]
    """
    if t.dim() == 2:  # gray -> RGB
        t = t.unsqueeze(0).repeat(3, 1, 1)
    return t.permute(1, 2, 0).clamp(0, 1).cpu().numpy()