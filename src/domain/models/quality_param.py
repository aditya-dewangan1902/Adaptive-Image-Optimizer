"""Codec-aware quality parameter representation (Issue #8).

Distinguishes internal normalized search representation from codec-native control parameters.
"""

from dataclasses import dataclass
from typing import Any, List


@dataclass(frozen=True)
class QualityParameter:
    """Represents a quality setting mapped between normalized and codec-native domains."""
    name: str              # e.g., 'quality', 'quantizer', 'crf', 'compression_level'
    normalized: float      # [0.0, 1.0] internal optimizer search scale
    native: Any            # Encoder-native parameter value (e.g. JPEG 85, PNG 9)


def normalized_to_native(format_name: str, norm_q: float) -> QualityParameter:
    """Map normalized quality [0.0, 1.0] to codec-native parameter."""
    norm_q = max(0.01, min(1.0, norm_q))
    fmt = format_name.lower()

    if fmt in ("jpeg", "jpg"):
        # JPEG quality: 1 to 98 (libjpeg/mozjpeg)
        native_val = int(round(1 + norm_q * 97))
        return QualityParameter("quality", round(norm_q, 3), native_val)

    elif fmt == "webp":
        # WebP quality: 1 to 100
        native_val = int(round(1 + norm_q * 99))
        return QualityParameter("quality", round(norm_q, 3), native_val)

    elif fmt == "avif":
        # AVIF quality: 1 to 100 (or CRF equivalent)
        native_val = int(round(1 + norm_q * 99))
        return QualityParameter("quality", round(norm_q, 3), native_val)

    elif fmt == "png":
        # PNG: for norm_q >= 0.8, full 24-bit with compress_level 9
        # for norm_q < 0.8, adaptive quantized palette (16 to 256 colors)
        if norm_q >= 0.8:
            return QualityParameter("compress_level", round(norm_q, 3), 9)
        else:
            num_colors = max(16, int(round(256 * (norm_q / 0.8))))
            return QualityParameter("colors", round(norm_q, 3), num_colors)

    # Default fallback
    native_val = int(round(1 + norm_q * 99))
    return QualityParameter("quality", round(norm_q, 3), native_val)


def get_codec_ordered_neighbors(format_name: str, current_param: QualityParameter) -> List[QualityParameter]:
    """
    Get ordered neighbor probe points in the codec's actual parameter space (Issue #10).
    Replaces naive +/-2 step assumptions with domain-accurate neighbor sampling.
    """
    fmt = format_name.lower()
    norm = current_param.normalized
    step = 0.03  # ~3% in normalized space

    offsets = [-2 * step, -step, step, 2 * step]
    neighbors: List[QualityParameter] = []
    seen = set()

    for off in offsets:
        cand_norm = max(0.01, min(1.0, norm + off))
        param = normalized_to_native(fmt, cand_norm)
        if param.native not in seen and param.native != current_param.native:
            seen.add(param.native)
            neighbors.append(param)

    return neighbors
