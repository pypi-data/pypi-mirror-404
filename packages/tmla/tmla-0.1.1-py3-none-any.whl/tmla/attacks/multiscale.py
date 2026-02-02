"""Multiscale adversarial attack implementation for neural image compression.

This module implements the T-MLA attack, which performs targeted
adversarial attacks in the wavelet domain.
"""

from typing import List, Optional, Tuple
import torch
import torch.nn.functional as F
# Local imports
from tmla.attacks.metrics import bpp_loss, dists, ssim
from tmla.attacks.multiscale_decomp import MultiScaleDecomposition
from tmla.attacks.reconstruct import Reconstruction


def maxdistortion_logexp_multiscale(
    x: torch.Tensor,
    errbound: float = 0.1,
    smoothfilter: Optional[torch.nn.Module] = None,
    losstype: str = 'psnr',
    l1_lambda: float = 0,
    num_iterations: int = 1000,
    model: Optional[torch.nn.Module] = None,
    device: Optional[torch.device] = None,
    mask: Optional[List[torch.Tensor]] = None,
    initial_noise: Optional[List[torch.Tensor]] = None,
    learningrate: float = 0.1,
    scales: int = 1,
    keep_perturbation_targeted: bool = False,
    keep_low_outcomequality: bool = True,
    target_quality: Optional[List[float]] = None,
    keep_minimum_attack_area: bool = False,
    keep_maximal_defect_area: bool = False,
    noiselevel_control: str = 'scale_adaptive',
    loss_history: Optional[List[float]] = None,
    psnr_history_ai: Optional[List[float]] = None,
    psnr_history_ao: Optional[List[float]] = None,
) -> Tuple[
    torch.Tensor, torch.Tensor, List[torch.Tensor], List[torch.nn.Parameter]
]:
    """Multiscale log-exp adversarial attack for neural image compression.

    This function implements the T-MLA attack from the paper. It performs
    a targeted adversarial attack in the wavelet domain to ensure perceptual
    quality while maximizing distortion in the compressed output.

    The optimization problem is formulated as:
        Loss = |PSNR(hat_x_adv, x_in) - Q_out|
        + |PSNR(x_adv, x_in) - Q_in| + λ ||n||_1
        where x_adv = idwt(logexp(dwt(x_in) + n)),
        hat_x_adv = f(x_adv), |n_ij| ≤ σ

    Args:
        x: Input image tensor (1, C, H, W)
        errbound: Maximum allowed perturbation magnitude
        smoothfilter: Optional smoothing filter for noise patterns
        losstype: Loss type ('psnr', 'ssim', 'dists', 'mse')
        l1_lambda: L1 regularization weight
        num_iterations: Number of optimization iterations
        model: Target compression model
        device: PyTorch device
        mask: List of masks for each wavelet scale
        initial_noise: Initial noise patterns for each scale
        learningrate: Optimization learning rate
        scales: Number of wavelet decomposition scales
        keep_perturbation_targeted: maintain targeted perturbation quality
        keep_low_outcomequality: Whether to maintain low output quality
        target_quality: Target quality [perturbation_quality, output_quality]
        keep_minimum_attack_area: True - penalize large area of the noise
        keep_maximal_defect_area: True - encourage large area defects
        noiselevel_control: 'constant', 'scale_adaptive', 'intensity_adaptive'

    Returns:
        perturbed_image: Adversarially perturbed input image
        perturbed_output: Compressed and reconstructed perturbed image
        smoothed_noise_pattern: List of smoothed noise patterns for each scale
        noise_pattern: List of raw noise patterns for each scale
    """

    # If no device is provided, use the device of the input tensor 'x'
    if device is None:
        device = x.device

    # If no mask is provided, use a scalar value of 1 to apply noise uniformly
    if mask is None:
        mask = [torch.ones(1) for _ in range(scales + 1)]

    # Move mask to the appropriate device
    mask = [m.to(device).detach() for m in mask]

    # Set default learning rate if not provided
    if learningrate is None:
        learningrate = 0.1
        
    # Initialize components
    wavelet = 'haar'
    decomposer = MultiScaleDecomposition(
        wavelet=wavelet, device=device, scales=scales
    )
    reconstructor = Reconstruction(wavelet=wavelet, device=device)

    # Decompose input image
    low, details = decomposer.decompose(x)

    max_details = [torch.max(cx.ravel().abs()) for cx in details]
    max_low = torch.max(low.ravel().abs())  # should be 2**(scales)
    
    # Initialize the noise pattern
    if initial_noise is None:
        # Generate random tensors matching the size of each 'details[k]'
        detail_noise_pattern = [
            torch.nn.Parameter(torch.randn_like(detail) * mask[k + 1])
            for k, detail in enumerate(details)
        ]
        low_noise_pattern = torch.nn.Parameter(torch.randn_like(low))

    else:
        # Use provided initial noise scaled by mask
        detail_noise_pattern = [
            torch.nn.Parameter(
                initial_noise[k + 1].detach().clone() * mask[k + 1]
            )
            for k in range(scales)
        ]
        low_noise_pattern = torch.nn.Parameter(
            initial_noise[0].detach().clone()
        )
        
    # Combine all parameters into a single list
    noise_pattern = [low_noise_pattern] + detail_noise_pattern

    # Move noise_pattern tensors to the appropriate device
    noise_pattern = [param.to(device) for param in noise_pattern]

    # Optional: Print the shapes for verification
    for k, param in enumerate(noise_pattern):
        print(f"Scale {k} - Noise pattern shape: {param.shape}")

    # Define optimizer
    optimizer = torch.optim.SGD(noise_pattern, lr=learningrate)

    # Define the maximum possible pixel value of the image
    MAX_I = 1.0

    # Calculate the number of pixels
    num_pixels = x.shape[0] * x.shape[2] * x.shape[3]

    clamp_input = True
    clamp_output = True
    
    try:
        # Initialize lists to store masked noise patterns
        # and perturbed details
        smoothed_noise_pattern = [None] * (scales + 1)
        perturbed_details = [None] * scales
        for iteration in range(num_iterations):
            optimizer.zero_grad()

            for k in range(scales + 1):

                if noiselevel_control == 'constant':
                    errbound_k = errbound

                elif noiselevel_control == 'scale_adaptive':
                    errbound_k = errbound * (1.8) ** (scales - k)

                elif noiselevel_control == 'intensity_adaptive':
                    if k == 0:
                        errbound_k = errbound * max_low
                    else:
                        errbound_k = errbound * max_details[k - 1]
                    
                # Clamp noise pattern values to ensure
                # they stay within valid range
                noise_pattern[k].data.clamp_(-errbound_k, errbound_k)

                # Apply masks to the clamped noise patterns
                smoothed_noise_pattern[k] = noise_pattern[k] * mask[k]

                # Apply current noise pattern to the details
                if k == 0:
                    perturbed_low = torch.sign(low) * torch.log(
                        torch.max(
                            torch.exp(torch.abs(low))
                            + smoothed_noise_pattern[k],
                            torch.tensor(1e-3)
                        )
                    )
                else:
                    exp_abs = torch.exp(torch.abs(details[k - 1]))
                    perturbed_details[k - 1] = (
                        torch.sign(details[k - 1])
                        * torch.log(
                            torch.max(
                                exp_abs + smoothed_noise_pattern[k],
                                torch.tensor(1e-3)
                            )
                        )
                    )
                    
            # Reconstruct the perturbed image
            perturbed_image = reconstructor.reconstruct(
                perturbed_low, perturbed_details
            )

            # Forward pass through the model
            if clamp_input:
                output = model.forward(torch.clamp(perturbed_image, 0, 1))
            else:
                output = model.forward(perturbed_image)

            # Extract reconstruction
            if clamp_output:
                perturbed_output = torch.clamp(output['x_hat'], 0, 1)
            else:
                perturbed_output = output['x_hat']
                  
            # Quality loss
            if losstype == 'mse':
                mse_loss = F.mse_loss(perturbed_output, x)
                perturbed_quality = 10 * torch.log10((MAX_I ** 2) / mse_loss)
                quality_loss = 1.0 - mse_loss
                perturbed_quality_ai = 0
                quality_loss_ai = 0
            
            elif losstype == 'psnr':
                mse_loss = F.mse_loss(perturbed_output, x)
                perturbed_quality = 10 * torch.log10((MAX_I ** 2) / mse_loss)

                # Compute the difference in PSNR between perturbed and target
                if keep_low_outcomequality:
                    quality_loss = torch.max(
                        (perturbed_quality - target_quality[1]).abs(),
                        torch.tensor(0.0)
                    )
                else:
                    quality_loss = perturbed_quality

                if keep_perturbation_targeted:
                    # Calculate MSE loss
                    mse_loss_ai = F.mse_loss(perturbed_image, x)

                    # Calculate PSNR loss
                    perturbed_quality_ai = 10 * torch.log10(
                        (MAX_I ** 2) / mse_loss_ai
                    )

                    # The difference in PSNR between perturbed and target
                    quality_loss_ai = torch.max(
                        (perturbed_quality_ai - target_quality[0]).abs() - 2,
                        torch.tensor(0.0)
                    )

                else:
                    perturbed_quality_ai = 0
                    quality_loss_ai = 0
                            
            elif losstype == 'ssim':
                # maximize distortion = maximize 1-SSIM
                ssim_perturbed = ssim(perturbed_output, x)
                quality_loss = -ssim_perturbed

            elif losstype == 'dists':
                dists_perturbed = dists(x, perturbed_output)
                quality_loss = -dists_perturbed    
                
            # Sparsity / area regularization
            if l1_lambda > 0:
                l1norm_perturb = 0.0
                l1norm_defect = 0.0

                if keep_minimum_attack_area:
                    # Encourage the attack to occupy a small spatial area
                    additive_noise = perturbed_image - x
                    max_abs = additive_noise.ravel().abs().max()
                    # Avoid division by zero
                    if max_abs > 0:
                        additive_noise = additive_noise / max_abs

                    # Max over channels
                    n_max = torch.max(torch.abs(additive_noise), dim=1).values
                    l1norm_perturb = (
                        torch.sigmoid(10 * (n_max.clamp(0.05, 1) - 0.5)).sum()
                        / num_pixels
                    )

                if keep_maximal_defect_area:
                    # Encourage large visible defect area in the output
                    n_max_defect = 1 - torch.max(
                        torch.abs(perturbed_output.clamp(0, 1) - x), dim=1
                    ).values
                    l1norm_defect = (
                        torch.sigmoid(
                            10 * (n_max_defect.clamp(0.05, 1) - 0.5)
                        ).sum()
                        / num_pixels
                    )

                l1norm = l1norm_perturb + l1norm_defect
            else:
                l1norm = 0.0
                l1norm_perturb = 0.0
                l1norm_defect = 0.0

            # Compute the bpp loss
            # Not for optimization (just to control the change)
            bpploss = bpp_loss(output, num_pixels)

            # Total loss
            combined_loss = (
                quality_loss + quality_loss_ai
            ) + l1_lambda * l1norm

            # Store loss history if requested
            if loss_history is not None:
                loss_history.append(float(combined_loss.detach().cpu()))

            if psnr_history_ai is not None:
                psnr_history_ai.append(float(perturbed_quality_ai))
            
            if psnr_history_ao is not None:
                psnr_history_ao.append(float(perturbed_quality))

            # Perform gradient descent
            combined_loss.backward()
            optimizer.step()

            # Print the loss every 100 iterations
            if iteration % 100 == 0:
                print(
                    f'Iteration {iteration} | {losstype}: '
                    f'(ao,oi) {perturbed_quality:.4f} - Lost '
                    f'{quality_loss:.4f} | '
                    f'(ai,oi) {perturbed_quality_ai:.4f} '
                    f'Lost {quality_loss_ai:.4f} | '
                    f'BPP {bpploss:.4f} | Area {l1norm_perturb:.4f} | '
                    f'Defect {l1norm_defect:.4f} | Loss {combined_loss:.4f}'
                )
 
    except KeyboardInterrupt:
        print("Interrupted, checkpoint saved.")
        return (
            perturbed_image,
            perturbed_output,
            smoothed_noise_pattern,
            noise_pattern
        )

    return (
        perturbed_image,
        perturbed_output,
        smoothed_noise_pattern,
        noise_pattern
    )
