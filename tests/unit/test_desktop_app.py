"""Tests for desktop application module and launcher options."""

import os
import sys

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

RUNTIME_SITE = os.path.join(WORKSPACE_DIR, "runtime", "Lib", "site-packages")
if os.path.isdir(RUNTIME_SITE) and RUNTIME_SITE not in sys.path:
    sys.path.insert(1, RUNTIME_SITE)

try:
    import secure_loader  # noqa: F401
except ImportError:
    pass

import unittest
from unittest.mock import patch, MagicMock
import launch_gui
from apps.desktop.modern_app import ModernOptimizerApp


class TestModernOptimizerApp(unittest.TestCase):
    """Unit tests for standalone bright in-process ModernOptimizerApp."""

    def setUp(self):
        self.app = ModernOptimizerApp()

    def tearDown(self):
        try:
            self.app.update_idletasks()
            self.app.destroy()
        except Exception:
            pass

    def test_app_initialization(self):
        self.assertEqual(self.app.title(), "Adaptive Image Optimizer")
        self.assertIsNotNone(self.app.job_service)
        self.assertFalse(self.app.is_optimizing)

    def test_set_interval_preset(self):
        self.app._set_interval(25, 150)
        self.assertEqual(self.app.entry_min.get(), "25")
        self.assertEqual(self.app.entry_max.get(), "150")
        self.assertEqual(self.app.seg_unit.get(), "KB")

    def test_sample_image_loading(self):
        sample_name = "sample_photo.jpg"
        self.app._load_sample(sample_name)
        self.assertIsNotNone(self.app.source_bytes)
        self.assertIsNotNone(self.app.source_pil)
        self.assertIn("1200x800", self.app.lbl_selected_specs.cget("text"))


class TestLauncherConfig(unittest.TestCase):
    """Unit tests for launch_gui command-line options."""

    def test_default_args(self):
        with patch("sys.argv", ["launch_gui.py"]):
            args = launch_gui.parse_args()
            self.assertFalse(args.web)
            self.assertFalse(args.server)
            self.assertEqual(args.port, 8000)

    def test_web_flag(self):
        with patch("sys.argv", ["launch_gui.py", "--web"]):
            args = launch_gui.parse_args()
            self.assertTrue(args.web)
            self.assertFalse(args.server)

    def test_server_flag(self):
        with patch("sys.argv", ["launch_gui.py", "--server"]):
            args = launch_gui.parse_args()
            self.assertTrue(args.server)
            self.assertFalse(args.web)


if __name__ == "__main__":
    unittest.main()
