"""Configuration module for T-MLA attack framework.

This module contains default configuration parameters for the T-MLA
(Targeted Multi-scale Log-Exponential Attack) framework.
"""

from typing import Any, Dict

CONFIG: Dict[str, Any] = {
    "datasets": {
        "kodak": {
            "path": "data/kodak",
            "size": (768, 512),
            "format": "png",
        },
        "clic": {
            "path": "data/clic",
            "size": (768, 512),
            "format": "png",
        },
        "div2k": {
            "path": "data/div2k",
            "size": (768, 512),
            "format": "png",
        },
    },
    "models": {
        "cheng2020_anchor": {
            "type": "compressai",
            "quality": 6, # [1, 2, 3, 4, 5, 6]
            "checkpoint": None,
        },
        "cheng2020_attention": {
            "type": "compressai",
            "quality": 6, # [1, 2, 3, 4, 5, 6]
            "checkpoint": None,
        },
        "tcm": {
            "type": "tcm",
            "p": 128, # 64, 128
            "checkpoint": None,
        },
    },
    "attack": {
        "method": "tmla",
        "scales": 3, # [1, 2, 3]
        "wavelet": "haar",
        "iterations": 1000,
        "learning_rate": 0.01,
        # Noise bounds
        "delta": 0.1,
        # Options: "const", "scale", "intensity"
        "noise_mode": "scale",
        "scale_factor": 1.8,
        # Target PSNR values
        "target_psnr_in": 45.0,
        "target_psnr_out": 15.0,
        # Regularization
        "l1_lambda": 0.001,
        # Optimization
        "clip_gradients": True,
        "gradient_clip_value": 1.0,
    },
    "metrics": {
        "psnr": True,
        "ssim": True,
        "vif": True,
        "lpips": True,
        "entropy": True,
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": "logs/safenic.log",
        "console": True,
    },
    "output": {
        "save_perturbed": True,
        "save_reconstructed": True,
        "save_entropy_maps": True,
        "save_metrics": True,
        "results_dir": "results",
    },
    "random_seed": 42,
    "device": "cuda",
    "num_workers": 4,
}

QUALITY: int = 6
SCALES: int = CONFIG["attack"]["scales"]
WAVELET: str = CONFIG["attack"]["wavelet"]

def get_attack_config() -> Dict[str, Any]:
    return CONFIG["attack"]
