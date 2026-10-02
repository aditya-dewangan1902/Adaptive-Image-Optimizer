"""Unit tests for encoder backends (JPEG, WebP, AVIF, PNG)."""

import os
import tempfile
import unittest
from PIL import Image

from src.encoders.registry import get_encoder_registry
from src.encoders.base import EncodeRequest


class TestEncoders(unittest.TestCase):

    def setUp(self):
        self.registry = get_encoder_registry()
        self.image = Image.new("RGB", (80, 80), color=(200, 100, 50))
        self.image_alpha = Image.new("RGBA", (80, 80), color=(50, 150, 250, 180))

    def test_jpeg_encoder(self):
        enc = self.registry.get("jpeg")
        self.assertIsNotNone(enc)
        with tempfile.TemporaryDirectory() as td:
            out_p = os.path.join(td, "test.jpg")
            req = EncodeRequest("jpeg", 80, 80, 75, chroma="420", progressive=True)
            art = enc.encode(self.image, req, out_p)
            self.assertTrue(os.path.exists(out_p))
            self.assertGreater(art.size_bytes, 0)
            self.assertEqual(len(art.checksum_sha256), 64)

    def test_webp_encoder(self):
        enc = self.registry.get("webp")
        self.assertIsNotNone(enc)
        with tempfile.TemporaryDirectory() as td:
            out_p = os.path.join(td, "test.webp")
            req = EncodeRequest("webp", 80, 80, 80)
            art = enc.encode(self.image_alpha, req, out_p)
            self.assertTrue(os.path.exists(out_p))
            self.assertGreater(art.size_bytes, 0)

    def test_avif_encoder(self):
        enc = self.registry.get("avif")
        self.assertIsNotNone(enc)
        with tempfile.TemporaryDirectory() as td:
            out_p = os.path.join(td, "test.avif")
            req = EncodeRequest("avif", 80, 80, 60, chroma="420")
            art = enc.encode(self.image_alpha, req, out_p)
            self.assertTrue(os.path.exists(out_p))
            self.assertGreater(art.size_bytes, 0)

    def test_png_encoder(self):
        enc = self.registry.get("png")
        self.assertIsNotNone(enc)
        with tempfile.TemporaryDirectory() as td:
            out_p = os.path.join(td, "test.png")
            req = EncodeRequest("png", 80, 80, 90)
            art = enc.encode(self.image_alpha, req, out_p)
            self.assertTrue(os.path.exists(out_p))
            self.assertGreater(art.size_bytes, 0)


if __name__ == "__main__":
    unittest.main()
