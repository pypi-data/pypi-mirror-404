"""Image preprocessing utilities for T-MLA framework.

This module provides functions for loading, cropping, and preprocessing
images for compression models.
"""

import matplotlib.pyplot as plt
import numpy as np
import torch
from PIL import Image
from skimage.util import img_as_float
from torchvision import transforms


def load_and_preprocess_image(
    img_path, target_width=768, target_height=512, device='cpu'
):
    """Load, crop and preprocess image for compression model.

    Args:
        img_path (str): Path to input image
        target_width (int): Width for cropping
        target_height (int): Height for cropping
        device (str): Device to put tensor on

    Returns:
        tuple: (tensor, original PIL image, RGB numpy array, pixel count)

    """
    # Load and convert image
    img = Image.open(img_path).convert('RGB')

    # Get original dimensions
    original_width, original_height = img.size
    print(f"Original size: {original_width}x{original_height}")

    # Swap dimensions if needed based on orientation
    if original_width > original_height:
        target_w, target_h = target_width, target_height
    else:
        target_w, target_h = target_height, target_width

    # Calculate center crop coordinates
    left = (original_width - target_w) // 2
    top = (original_height - target_h) // 2
    right = left + target_w
    bottom = top + target_h

    # Crop the image
    img = img.crop((left, top, right, bottom))
    print(f"Cropped size: {img.size}")

    # Convert to tensor
    preprocess = transforms.Compose([transforms.ToTensor()])
    x = preprocess(img).unsqueeze(0)

    # Only move to specified device if it's available
    if device == 'cuda' and torch.cuda.is_available():
        x = x.to(device)

    # Convert to normalized numpy array
    img_rgb = img_as_float(np.array(img))

    # Calculate number of pixels
    num_pixels = x.shape[0] * x.shape[2] * x.shape[3]
    print(f"Size of the image: {x.shape[2]} × {x.shape[3]}")

    # Display image
    plt.figure(figsize=(9, 6))
    plt.axis('off')
    plt.imshow(img)
    plt.show()

    return x, img, img_rgb, num_pixels