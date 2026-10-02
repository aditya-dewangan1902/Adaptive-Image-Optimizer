"""Unit tests for perceptual and diagnostic quality metrics."""

import unittest
from PIL import Image

from src.quality.butteraugli import compute_butteraugli
from src.quality.ssim import compute_ssim
from src.quality.psnr import compute_psnr
from src.quality.delta_e import compute_delta_e
from src.quality.evaluator import StandardQualityEvaluator


class TestQualityMetrics(unittest.TestCase):

    def setUp(self):
        self.img1 = Image.new("RGB", (100, 100), (128, 128, 128))
        self.img2 = Image.new("RGB", (100, 100), (128, 128, 128))
        self.img_shifted = Image.new("RGB", (100, 100), (135, 128, 125))

    def test_butteraugli_identical(self):
        dist = compute_butteraugli(self.img1, self.img2)
        self.assertEqual(dist, 0.0, "Identical images must have 0.0 Butteraugli distance")

    def test_butteraugli_distortion(self):
        dist = compute_butteraugli(self.img1, self.img_shifted)
        self.assertGreater(dist, 0.0)
        self.assertLess(dist, 5.0)

    def test_ssim(self):
        ssim_same = compute_ssim(self.img1, self.img2)
        self.assertAlmostEqual(ssim_same, 1.0, places=3)
        ssim_diff = compute_ssim(self.img1, self.img_shifted)
        self.assertLess(ssim_diff, 1.0)
        self.assertGreater(ssim_diff, 0.5)

    def test_psnr(self):
        psnr_diff = compute_psnr(self.img1, self.img_shifted)
        self.assertGreater(psnr_diff, 20.0)
        self.assertLess(psnr_diff, 90.0)

    def test_delta_e(self):
        de = compute_delta_e(self.img1, self.img_shifted)
        self.assertGreater(de, 0.0)

    def test_evaluator(self):
        evaluator = StandardQualityEvaluator()
        res = evaluator.evaluate_full(self.img1, self.img_shifted)
        self.assertIsNotNone(res.butteraugli_distance)
        self.assertIsNotNone(res.ssim)
        self.assertIsNotNone(res.psnr_db)
        self.assertIsNotNone(res.delta_e)


if __name__ == "__main__":
    unittest.main()
