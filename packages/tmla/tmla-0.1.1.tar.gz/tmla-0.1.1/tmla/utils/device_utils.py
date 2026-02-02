"""
This module provides functions for:
- selecting optimal GPUs based on memory usage and temperature
- setting seeds for reproducible experiments
"""

import os
import random
import numpy as np
import torch


def set_random_seed(seed: int, deterministic: bool = True) -> None:
    """Set random seeds for Python, NumPy and PyTorch.
    
    Args:
        seed: Base integer seed value.
        deterministic: If True, enable deterministic CuDNN behavior.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if deterministic:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        # Recommended for deterministic cuBLAS
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")