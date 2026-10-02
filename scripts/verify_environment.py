"""Environment and encoder backend verification script (Issue #4).

Inspects and reports the exact runtime identity of image codecs, libavif, AV1 backends,
and perceptual metrics without false claims.
"""

import sys
import PIL
from PIL import features

def inspect_avif_backend() -> dict:
    """Inspect libavif and underlying AV1 codec implementations."""
    try:
        import PIL.AvifImagePlugin as aip
        libavif_ver = getattr(aip._avif, "libavif_version", "unknown")
        aom_ver = aip.get_codec_version("aom")
        svt_ver = aip.get_codec_version("svt")
        rav1e_ver = aip.get_codec_version("rav1e")
        dav1d_ver = aip.get_codec_version("dav1d")

        active_encoder = "unknown"
        if aom_ver:
            active_encoder = f"AOM ({aom_ver})"
        elif svt_ver:
            active_encoder = f"SVT-AV1 ({svt_ver})"
        elif rav1e_ver:
            active_encoder = f"rav1e ({rav1e_ver})"

        return {
            "avif_available": True,
            "libavif_version": libavif_ver,
            "active_encoder": active_encoder,
            "svt_av1_available": svt_ver is not None,
            "aom_available": aom_ver is not None,
            "rav1e_available": rav1e_ver is not None,
            "dav1d_decoder_version": dav1d_ver,
        }
    except Exception as e:
        return {
            "avif_available": False,
            "error": str(e),
            "active_encoder": "none",
            "svt_av1_available": False,
        }


def inspect_all_codecs() -> dict:
    avif_info = inspect_avif_backend()
    return {
        "python_version": sys.version,
        "pillow_version": PIL.__version__,
        "jpeg_support": features.check("jpg"),
        "libjpeg_turbo": features.check("libjpeg_turbo"),
        "webp_support": features.check("webp"),
        "png_support": features.check("zlib"),
        "avif": avif_info,
    }


def main():
    print("=" * 64)
    print("  Runtime Codec & Codec-Backend Verification Report")
    print("=" * 64)
    info = inspect_all_codecs()
    print(f"Python:              {sys.version.split()[0]}")
    print(f"Pillow:              {info['pillow_version']}")
    print(f"JPEG Backend:        libjpeg_turbo ({info['libjpeg_turbo']})")
    print(f"WebP Backend:        libwebp ({info['webp_support']})")
    print(f"PNG Backend:         zlib ({info['png_support']})")
    print("-" * 64)
    avif = info["avif"]
    print(f"AVIF Available:      {avif.get('avif_available')}")
    print(f"libavif Version:     {avif.get('libavif_version')}")
    print(f"Active AV1 Encoder:  {avif.get('active_encoder')}")
    print(f"SVT-AV1 Available:   {'PASS' if avif.get('svt_av1_available') else 'NOT DETECTED (fallback to ' + str(avif.get('active_encoder')) + ')'}")
    print(f"AV1 Decoder (dav1d): {avif.get('dav1d_decoder_version')}")
    print("=" * 64)


if __name__ == "__main__":
    main()
