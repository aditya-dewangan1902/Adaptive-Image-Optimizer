"""End-to-end integration test of optimization service."""

import os
import io
import unittest
from PIL import Image

from src.domain.models.job import Job, TargetRange
from src.domain.policies.optimization_policy import OptimizationPolicy
from src.domain.policies.budget_policy import SearchBudget
from src.domain.errors.statuses import JobStatus
from src.services.optimization_service import OptimizationService


class TestEndToEndOptimization(unittest.TestCase):

    def test_complete_optimization_workflow(self):
        # 1. Create a synthetic test image with varying content
        w, h = 300, 300
        img = Image.new("RGB", (w, h), (30, 60, 90))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        for i in range(10):
            draw.ellipse([i * 10, i * 10, 280 - i * 10, 280 - i * 10], outline=(200, 100, i * 20))

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        raw_bytes = buf.getvalue()

        # Target range: target between 3,000 and 15,000 bytes
        target = TargetRange(min_bytes=3_000, max_bytes=15_000)

        job = Job(
            target=target,
            source_filename="test_synthetic.jpg",
            source_bytes=raw_bytes,
            optimization_policy=OptimizationPolicy(requested_format="auto"),
            budget=SearchBudget(max_total_encodes=15, max_coarse_candidates=8),
        )

        svc = OptimizationService(output_dir="artifacts/outputs")
        result = svc.run_job(job)

        # Invariant checks
        self.assertEqual(result.status, JobStatus.COMPLETED)
        self.assertIsNotNone(result.output_path)
        self.assertTrue(os.path.exists(result.output_path))
        self.assertGreaterEqual(result.output_size_bytes, target.min_bytes)
        self.assertLessEqual(result.output_size_bytes, target.max_bytes)
        self.assertIsNotNone(result.butteraugli_distance)
        self.assertIsNotNone(result.ssim)
        self.assertIsNotNone(result.sha256_checksum)
        self.assertEqual(len(result.sha256_checksum), 64)
        self.assertGreater(len(result.candidates_ledger), 0)


if __name__ == "__main__":
    unittest.main()
