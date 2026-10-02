"""PSNR (Peak Signal to Noise Ratio) metric implementation."""

import numpy as np
from PIL import Image


def compute_psnr(reference: Image.Image, candidate: Image.Image) -> float:
    """Compute PSNR in dB."""
    if reference.size != candidate.size:
        candidate = candidate.resize(reference.size, Image.Resampling.BILINEAR)

    ref_arr = np.array(reference.convert("RGB"), dtype=np.float32) / 255.0
    cand_arr = np.array(candidate.convert("RGB"), dtype=np.float32) / 255.0

    mse = float(np.mean((ref_arr - cand_arr) ** 2))
    if mse < 1e-10:
        return 99.0

    score = 10.0 * np.log10(1.0 / mse)
    return float(max(0.0, score))
