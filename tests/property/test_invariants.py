"""Property tests enforcing architectural invariants P1 through P8 (Requirement.md)."""

import os
import unittest
from PIL import Image
import numpy as np

from src.domain.models.job import Job, TargetRange
from src.domain.policies.optimization_policy import OptimizationPolicy
from src.domain.policies.budget_policy import SearchBudget
from src.domain.errors.statuses import JobStatus
from src.optimization.candidate_space import build_finite_theta
from src.optimization.candidate_ledger import CandidateLedger
from src.optimization.termination import determine_termination_status
from src.image.analysis import analyze_image
from src.image.resize import resize_from_master
from src.image.color_management import convert_to_comparison_space
from src.services.optimization_service import OptimizationService
from src.services.verification_service import VerificationService


class TestArchitecturalInvariants(unittest.TestCase):
    """Test Suite verifying P1 through P8 formal invariants."""

    def setUp(self):
        # Create standard test master
        self.master = Image.new("RGB", (200, 200), color=(100, 150, 200))
        self.analysis = analyze_image(self.master, "jpeg", 10000)
        self.policy = OptimizationPolicy()
        self.budget = SearchBudget(max_total_encodes=10, max_coarse_candidates=6)

    def test_p1_provenance_invariant(self):
        """P1: A candidate is never derived from another compressed candidate."""
        # Verification that resize_from_master strictly uses canonical master
        resized1 = resize_from_master(self.master, 100, 100)
        resized2 = resize_from_master(self.master, 50, 50)
        self.assertEqual(resized1.size, (100, 100))
        self.assertEqual(resized2.size, (50, 50))
        # Ensure master dimensions are intact
        self.assertEqual(self.master.size, (200, 200))

    def test_p2_actual_bytes_feasibility(self):
        """P2: Final feasibility uses actual bytes, not predicted size."""
        from src.domain.models.candidate import CandidateRecord, CandidateParams
        from src.optimization.feasibility import evaluate_feasibility

        target = TargetRange(1000, 5000)
        param = CandidateParams("jpeg", 1.0, 100, 100, 80)
        
        # Predicted is within target, but actual is not
        record = CandidateRecord(param, predicted_size_bytes=3000, actual_size_bytes=6000)
        is_feas = evaluate_feasibility(record, target)
        self.assertFalse(is_feas, "Feasibility must rely on actual bytes, not predicted")

        # Actual is within target
        record_good = CandidateRecord(param, predicted_size_bytes=6000, actual_size_bytes=3000)
        is_feas_good = evaluate_feasibility(record_good, target)
        self.assertTrue(is_feas_good)

    def test_p3_budget_does_not_imply_unreachability_without_bound_proof(self):
        """P3: Budget exhaustion never implies unreachability without bound proof."""
        target = TargetRange(1000, 2000)
        ledger = CandidateLedger(SearchBudget(max_total_encodes=2))

        # Ledger runs out of encodes before search space is exhausted
        from src.optimization.termination import determine_termination_with_certificate
        status, cert = determine_termination_with_certificate(ledger, target, total_theta=[], exhausted_space=False)
        self.assertIn(
            status,
            [JobStatus.CANDIDATE_BUDGET_EXCEEDED, JobStatus.TIME_BUDGET_EXCEEDED],
            "Incomplete search cannot claim CONSTRAINT_UNREACHABLE without proof",
        )
        self.assertFalse(cert.proven, "Feasibility certificate must have proven=False when budget is exhausted")
        self.assertEqual(cert.method, "INCOMPLETE_SEARCH_UNPROVEN")
        self.assertNotEqual(status, JobStatus.CONSTRAINT_UNREACHABLE_MIN)
        self.assertNotEqual(status, JobStatus.CONSTRAINT_UNREACHABLE_MAX)

    def test_p4_theta_is_finite_and_enumerable(self):
        """P4: Theta(job) is finite and enumerable."""
        theta = build_finite_theta(self.analysis, self.policy)
        self.assertIsInstance(theta, list)
        self.assertGreater(len(theta), 0)
        self.assertLess(len(theta), 1000, "Theta must be strictly bounded")

    def test_p5_final_output_independently_encoded_and_verified(self):
        """P5: Final output is independently encoded and verified."""
        import tempfile
        verif = VerificationService()
        theta = build_finite_theta(self.analysis, self.policy)
        param = theta[0]

        with tempfile.TemporaryDirectory() as td:
            out_file = os.path.join(td, "test_out.jpg")
            verif.independent_final_encode(self.master, param, out_file)
            self.assertTrue(os.path.exists(out_file))
            size, csum = verif.verify_final_artifact(
                out_file,
                TargetRange(10, 500_000),
                param,
            )
            self.assertGreater(size, 0)
            self.assertEqual(len(csum), 64)

    def test_p6_comparison_space_symmetric(self):
        """P6: The declared comparison space is used symmetrically."""
        cand = Image.new("RGBA", (100, 100), (50, 100, 150, 200))
        ref_space = convert_to_comparison_space(self.master, "sRGB_8bit")
        cand_space = convert_to_comparison_space(cand, "sRGB_8bit")

        self.assertEqual(ref_space.shape[2], 3)
        self.assertEqual(cand_space.shape[2], 3)
        self.assertEqual(ref_space.dtype, np.float32)
        self.assertEqual(cand_space.dtype, np.float32)

    def test_p7_max_total_encodes_never_exceeded(self):
        """P7: max_total_encodes is never exceeded."""
        max_enc = 5
        ledger = CandidateLedger(SearchBudget(max_total_encodes=max_enc))
        for _ in range(max_enc):
            self.assertTrue(ledger.can_encode(1))
            from src.domain.models.candidate import CandidateRecord, CandidateParams
            ledger.record_encode(CandidateRecord(CandidateParams("webp", 1.0, 50, 50, 50), actual_size_bytes=100))

        self.assertFalse(ledger.can_encode(1), "Ledger must refuse to encode past budget limit")
        self.assertEqual(ledger.total_encodes, max_enc)

    def test_sandbox_enforcement_audit(self):
        """Audit distinguishing specification from kernel enforcement (Issue #6)."""
        from apps.worker.sandbox import inspect_sandbox_enforcement
        audit = inspect_sandbox_enforcement(configured_memory_mb=4096)
        self.assertTrue(audit.architecture_specified_isolation)
        self.assertIsInstance(audit.kernel_enforced_isolation, bool)
        self.assertIn(audit.enforcement_level, [
            "SPECIFICATION_ONLY_HOST_SUBPROCESS",
            "CGROUP_SECCOMP_CONTAINER_ENFORCED",
            "GVISOR_MICROVM_ENFORCED",
        ])


if __name__ == "__main__":
    unittest.main()
