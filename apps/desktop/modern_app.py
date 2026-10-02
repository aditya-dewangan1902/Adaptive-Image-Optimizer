"""Modern Standalone Windows Application for Adaptive Image Optimizer.

A direct, in-process native Windows desktop application with a bright, minimalist,
professional design system. Operates with zero web server, zero localhost networking,
and direct access to the constrained optimization engine.
"""

import os
import sys
import json
import time
import shutil
import threading
from typing import Optional
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

# Ensure workspace root and runtime site-packages are on sys.path
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

RUNTIME_SITE = os.path.join(WORKSPACE_DIR, "runtime", "Lib", "site-packages")
if os.path.isdir(RUNTIME_SITE) and RUNTIME_SITE not in sys.path:
    sys.path.insert(1, RUNTIME_SITE)

# Automatically activate in-memory decryption hook for encrypted core modules
try:
    import secure_loader  # noqa: F401
except ImportError:
    pass

from src.services.job_service import JobService
from src.domain.models.job import Job
from src.domain.errors.statuses import JobStatus

# Modern Minimalist Bright Design Tokens (Light Aesthetic)
THEME = {
    "bg_window": "#F8FAFC",        # Crisp light canvas (Slate 50)
    "card_bg": "#FFFFFF",          # Pure white cards
    "card_border": "#E2E8F0",      # Subtle border (Slate 200)
    "card_border_focus": "#3B82F6",# Subtle blue highlight
    "input_bg": "#F8FAFC",         # Light input background
    "input_border": "#CBD5E1",     # Input border (Slate 300)
    "text_primary": "#0F172A",     # Slate 900
    "text_secondary": "#475569",   # Slate 600
    "text_muted": "#94A3B8",       # Slate 400
    "accent_blue": "#2563EB",      # Royal Blue
    "accent_hover": "#1D4ED8",     # Deep Royal Blue
    "pill_bg": "#F1F5F9",          # Soft Slate button
    "pill_hover": "#E2E8F0",       # Hover Slate
    "success_bg": "#ECFDF5",       # Soft Mint
    "success_text": "#047857",     # Emerald
    "success_border": "#A7F3D0",
    "warn_bg": "#FFFBEB",
    "warn_text": "#B45309",
    "warn_border": "#FDE68A",
    "error_bg": "#FEF2F2",
    "error_text": "#B91C1C",
    "error_border": "#FECACA",
    "font_family": "Segoe UI",
}


class ModernOptimizerApp(ctk.CTk):
    """Bright, minimalist standalone native Windows application."""

    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("Adaptive Image Optimizer")
        self.geometry("1280x880")
        self.minsize(1020, 680)

        # Force bright minimalist aesthetic
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=THEME["bg_window"])

        # Engine Service (Direct In-Process)
        self.job_service = JobService()

        # State Variables
        self.source_filepath = None
        self.source_bytes = None
        self.source_pil = None
        self.source_thumb = None
        self.optimized_pil = None
        self.optimized_thumb = None
        self.current_job: Optional[Job] = None
        self.is_optimizing = False

        self._build_layout()

    def _build_layout(self):
        """Construct the entire application UI layout."""
        # 1. Top Modern Header Bar
        self.header_frame = ctk.CTkFrame(
            self,
            fg_color=THEME["card_bg"],
            corner_radius=0,
            border_width=1,
            border_color=THEME["card_border"],
            height=64,
        )
        self.header_frame.pack(fill="x", side="top")
        self.header_frame.pack_propagate(False)

        # Header Title and Subtitle
        header_left = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        header_left.pack(side="left", padx=24, pady=12)

        lbl_app_title = ctk.CTkLabel(
            header_left,
            text="Adaptive Image Optimizer",
            font=ctk.CTkFont(family=THEME["font_family"], size=16, weight="bold"),
            text_color=THEME["text_primary"],
        )
        lbl_app_title.pack(side="left")

        lbl_divider = ctk.CTkLabel(
            header_left,
            text="•",
            font=ctk.CTkFont(family=THEME["font_family"], size=14),
            text_color=THEME["text_muted"],
        )
        lbl_divider.pack(side="left", padx=10)

        lbl_tagline = ctk.CTkLabel(
            header_left,
            text="Constrained Search & Perceptual Optimization (In-Process Native)",
            font=ctk.CTkFont(family=THEME["font_family"], size=12),
            text_color=THEME["text_secondary"],
        )
        lbl_tagline.pack(side="left")

        # Header Right Controls
        header_right = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        header_right.pack(side="right", padx=24, pady=12)

        # Engine Status Badge (Minimalist Soft Pill)
        self.status_chip = ctk.CTkLabel(
            header_right,
            text="● Engine Ready (Native In-Process)",
            font=ctk.CTkFont(family=THEME["font_family"], size=11, weight="bold"),
            text_color=THEME["success_text"],
            fg_color=THEME["success_bg"],
            corner_radius=12,
            padx=12,
            pady=4,
        )
        self.status_chip.pack(side="left", padx=(0, 12))

        btn_open_folder = ctk.CTkButton(
            header_right,
            text="Open Outputs Folder",
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            fg_color=THEME["pill_bg"],
            text_color=THEME["text_primary"],
            hover_color=THEME["pill_hover"],
            border_width=1,
            border_color=THEME["card_border"],
            corner_radius=8,
            height=32,
            command=self._open_output_folder,
        )
        btn_open_folder.pack(side="left")

        # 2. Main Two-Column Layout
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=24, pady=20)
        main_container.columnconfigure(0, weight=4, minsize=420)
        main_container.columnconfigure(1, weight=6, minsize=540)
        main_container.rowconfigure(0, weight=1)

        # Left Column: Configuration Controls (Scrollable)
        self.left_scroll = ctk.CTkScrollableFrame(
            main_container,
            fg_color=THEME["card_bg"],
            corner_radius=12,
            border_width=1,
            border_color=THEME["card_border"],
            scrollbar_button_color=THEME["card_border"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.left_scroll.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        # Right Column: Visual Comparison & Results
        self.right_frame = ctk.CTkFrame(
            main_container,
            fg_color=THEME["card_bg"],
            corner_radius=12,
            border_width=1,
            border_color=THEME["card_border"],
        )
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        # Populate Left and Right columns
        self._build_left_controls()
        self._build_right_results()

    def _build_left_controls(self):
        """Construct the configuration panels in the left column."""
        pad_x = 16

        # --- Section 1: Ingest Master Image ---
        lbl_sec1 = ctk.CTkLabel(
            self.left_scroll,
            text="1. Master Source Image",
            font=ctk.CTkFont(family=THEME["font_family"], size=13, weight="bold"),
            text_color=THEME["text_primary"],
        )
        lbl_sec1.pack(anchor="w", padx=pad_x, pady=(16, 8))

        # Drop / Pick Card
        self.file_card = ctk.CTkFrame(
            self.left_scroll,
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            corner_radius=10,
        )
        self.file_card.pack(fill="x", padx=pad_x, pady=(0, 8))

        self.lbl_selected_file = ctk.CTkLabel(
            self.file_card,
            text="No source image chosen",
            font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
            text_color=THEME["text_secondary"],
        )
        self.lbl_selected_file.pack(pady=(12, 4))

        self.lbl_selected_specs = ctk.CTkLabel(
            self.file_card,
            text="Supports JPEG, PNG, WebP, AVIF up to 50MB",
            font=ctk.CTkFont(family=THEME["font_family"], size=10),
            text_color=THEME["text_muted"],
        )
        self.lbl_selected_specs.pack(pady=(0, 10))

        btn_browse = ctk.CTkButton(
            self.file_card,
            text="Browse Image File...",
            font=ctk.CTkFont(family=THEME["font_family"], size=11, weight="bold"),
            fg_color=THEME["accent_blue"],
            hover_color=THEME["accent_hover"],
            corner_radius=8,
            height=34,
            command=self._browse_image,
        )
        btn_browse.pack(pady=(0, 14))

        # Sample Presets
        lbl_samples = ctk.CTkLabel(
            self.left_scroll,
            text="Quick Test Samples:",
            font=ctk.CTkFont(family=THEME["font_family"], size=10, weight="bold"),
            text_color=THEME["text_muted"],
        )
        lbl_samples.pack(anchor="w", padx=pad_x, pady=(4, 4))

        sample_row = ctk.CTkFrame(self.left_scroll, fg_color="transparent")
        sample_row.pack(fill="x", padx=pad_x, pady=(0, 16))

        samples = [
            ("Photo (JPG)", "sample_photo.jpg"),
            ("Logo (PNG)", "sample_graphic.png"),
            ("UI (PNG)", "sample_screenshot.png"),
        ]
        for title, fname in samples:
            btn = ctk.CTkButton(
                sample_row,
                text=title,
                font=ctk.CTkFont(family=THEME["font_family"], size=10),
                fg_color=THEME["pill_bg"],
                text_color=THEME["text_primary"],
                hover_color=THEME["pill_hover"],
                border_width=1,
                border_color=THEME["card_border"],
                corner_radius=6,
                height=26,
                command=lambda fn=fname: self._load_sample(fn),
            )
            btn.pack(side="left", padx=(0, 6))

        # --- Section 2: Target File Size Interval ---
        lbl_sec2 = ctk.CTkLabel(
            self.left_scroll,
            text="2. Target File Size Interval [B_min, B_max]",
            font=ctk.CTkFont(family=THEME["font_family"], size=13, weight="bold"),
            text_color=THEME["text_primary"],
        )
        lbl_sec2.pack(anchor="w", padx=pad_x, pady=(8, 8))

        # Unit Segmented Switch
        unit_row = ctk.CTkFrame(self.left_scroll, fg_color="transparent")
        unit_row.pack(fill="x", padx=pad_x, pady=(0, 8))

        lbl_unit = ctk.CTkLabel(
            unit_row,
            text="Measurement Unit:",
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            text_color=THEME["text_secondary"],
        )
        lbl_unit.pack(side="left")

        self.seg_unit = ctk.CTkSegmentedButton(
            unit_row,
            values=["KB", "MB", "Bytes"],
            font=ctk.CTkFont(family=THEME["font_family"], size=10, weight="bold"),
            fg_color=THEME["pill_bg"],
            selected_color=THEME["accent_blue"],
            selected_hover_color=THEME["accent_hover"],
            unselected_color=THEME["pill_bg"],
            unselected_hover_color=THEME["pill_hover"],
            corner_radius=6,
            height=28,
            command=self._on_unit_change,
        )
        self.seg_unit.set("KB")
        self.seg_unit.pack(side="right")

        # Numerical Interval Inputs
        interval_frame = ctk.CTkFrame(self.left_scroll, fg_color="transparent")
        interval_frame.pack(fill="x", padx=pad_x, pady=(0, 10))

        lbl_min = ctk.CTkLabel(
            interval_frame,
            text="Min Size:",
            font=ctk.CTkFont(family=THEME["font_family"], size=11, weight="bold"),
            text_color=THEME["text_secondary"],
        )
        lbl_min.grid(row=0, column=0, sticky="w", pady=2)

        self.entry_min = ctk.CTkEntry(
            interval_frame,
            width=90,
            font=ctk.CTkFont(family=THEME["font_family"], size=12),
            fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
            corner_radius=6,
        )
        self.entry_min.insert(0, "10")
        self.entry_min.grid(row=0, column=1, padx=(6, 16), pady=2)

        lbl_max = ctk.CTkLabel(
            interval_frame,
            text="Max Size:",
            font=ctk.CTkFont(family=THEME["font_family"], size=11, weight="bold"),
            text_color=THEME["text_secondary"],
        )
        lbl_max.grid(row=0, column=2, sticky="w", pady=2)

        self.entry_max = ctk.CTkEntry(
            interval_frame,
            width=90,
            font=ctk.CTkFont(family=THEME["font_family"], size=12),
            fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
            corner_radius=6,
        )
        self.entry_max.insert(0, "40")
        self.entry_max.grid(row=0, column=3, padx=(6, 0), pady=2)

        # Quick Preset Buttons
        lbl_preset = ctk.CTkLabel(
            self.left_scroll,
            text="Target Interval Presets:",
            font=ctk.CTkFont(family=THEME["font_family"], size=10, weight="bold"),
            text_color=THEME["text_muted"],
        )
        lbl_preset.pack(anchor="w", padx=pad_x, pady=(4, 4))

        preset_grid = ctk.CTkFrame(self.left_scroll, fg_color="transparent")
        preset_grid.pack(fill="x", padx=pad_x, pady=(0, 16))
        preset_grid.columnconfigure(0, weight=1)
        preset_grid.columnconfigure(1, weight=1)

        presets = [
            ("Mobile (<80 KB)", 10, 80),
            ("Web Banner (80–200 KB)", 80, 200),
            ("Email (<500 KB)", 200, 500),
            ("Hero (0.5–1 MB)", 500, 1024),
        ]
        for idx, (label, p_min, p_max) in enumerate(presets):
            btn = ctk.CTkButton(
                preset_grid,
                text=label,
                font=ctk.CTkFont(family=THEME["font_family"], size=10),
                fg_color=THEME["pill_bg"],
                text_color=THEME["text_primary"],
                hover_color=THEME["pill_hover"],
                border_width=1,
                border_color=THEME["card_border"],
                corner_radius=6,
                height=26,
                command=lambda mi=p_min, ma=p_max: self._set_interval(mi, ma),
            )
            r = idx // 2
            c = idx % 2
            btn.grid(row=r, column=c, padx=(0 if c == 0 else 4, 4 if c == 0 else 0), pady=3, sticky="ew")

        # --- Section 3: Codec & Optimization Policy ---
        lbl_sec3 = ctk.CTkLabel(
            self.left_scroll,
            text="3. Codec & Optimization Policy",
            font=ctk.CTkFont(family=THEME["font_family"], size=13, weight="bold"),
            text_color=THEME["text_primary"],
        )
        lbl_sec3.pack(anchor="w", padx=pad_x, pady=(8, 8))

        # Codec Choice
        lbl_codec = ctk.CTkLabel(
            self.left_scroll,
            text="Codec / Format Strategy:",
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            text_color=THEME["text_secondary"],
        )
        lbl_codec.pack(anchor="w", padx=pad_x, pady=(0, 4))

        self.seg_codec = ctk.CTkSegmentedButton(
            self.left_scroll,
            values=["Auto", "WebP", "AVIF", "JPEG", "PNG"],
            font=ctk.CTkFont(family=THEME["font_family"], size=10, weight="bold"),
            fg_color=THEME["pill_bg"],
            selected_color=THEME["accent_blue"],
            selected_hover_color=THEME["accent_hover"],
            unselected_color=THEME["pill_bg"],
            unselected_hover_color=THEME["pill_hover"],
            corner_radius=6,
            height=30,
        )
        self.seg_codec.set("Auto")
        self.seg_codec.pack(fill="x", padx=pad_x, pady=(0, 12))

        # Quality and Dimension dropdowns
        opt_grid = ctk.CTkFrame(self.left_scroll, fg_color="transparent")
        opt_grid.pack(fill="x", padx=pad_x, pady=(0, 16))
        opt_grid.columnconfigure(0, weight=1)
        opt_grid.columnconfigure(1, weight=1)

        lbl_qm = ctk.CTkLabel(opt_grid, text="Search Mode:", font=ctk.CTkFont(family=THEME["font_family"], size=11), text_color=THEME["text_secondary"])
        lbl_qm.grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.opt_quality = ctk.CTkOptionMenu(
            opt_grid,
            values=["Balanced (Standard)", "Fast (Quick Sweep)", "Maximum (Deep Search)"],
            font=ctk.CTkFont(family=THEME["font_family"], size=10),
            fg_color=THEME["pill_bg"],
            text_color=THEME["text_primary"],
            button_color=THEME["pill_hover"],
            corner_radius=6,
            height=28,
        )
        self.opt_quality.set("Balanced (Standard)")
        self.opt_quality.grid(row=1, column=0, sticky="ew", padx=(0, 4))

        lbl_dm = ctk.CTkLabel(opt_grid, text="Dimensions Policy:", font=ctk.CTkFont(family=THEME["font_family"], size=11), text_color=THEME["text_secondary"])
        lbl_dm.grid(row=0, column=1, sticky="w", pady=(0, 2))
        self.opt_dim = ctk.CTkOptionMenu(
            opt_grid,
            values=["Joint Search (Scale+Quality)", "Preserve 100% Dimensions"],
            font=ctk.CTkFont(family=THEME["font_family"], size=10),
            fg_color=THEME["pill_bg"],
            text_color=THEME["text_primary"],
            button_color=THEME["pill_hover"],
            corner_radius=6,
            height=28,
        )
        self.opt_dim.set("Joint Search (Scale+Quality)")
        self.opt_dim.grid(row=1, column=1, sticky="ew", padx=(4, 0))

        # --- Section 4: Run Optimization ---
        self.btn_optimize = ctk.CTkButton(
            self.left_scroll,
            text="Run Constrained Optimization",
            font=ctk.CTkFont(family=THEME["font_family"], size=13, weight="bold"),
            fg_color=THEME["accent_blue"],
            hover_color=THEME["accent_hover"],
            corner_radius=8,
            height=42,
            command=self._start_optimization,
        )
        self.btn_optimize.pack(fill="x", padx=pad_x, pady=(12, 8))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self.left_scroll,
            fg_color=THEME["card_border"],
            progress_color=THEME["accent_blue"],
            corner_radius=4,
            height=6,
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=pad_x, pady=(0, 6))

        self.lbl_stage = ctk.CTkLabel(
            self.left_scroll,
            text="Engine Ready",
            font=ctk.CTkFont(family=THEME["font_family"], size=10),
            text_color=THEME["text_muted"],
        )
        self.lbl_stage.pack(anchor="w", padx=pad_x, pady=(0, 20))

    def _build_right_results(self):
        """Construct the visual comparison and audit presentation in the right column."""
        # Top Headline Results Summary Card
        self.result_headline_card = ctk.CTkFrame(
            self.right_frame,
            fg_color=THEME["input_bg"],
            corner_radius=10,
            border_width=1,
            border_color=THEME["card_border"],
            height=80,
        )
        self.result_headline_card.pack(fill="x", padx=16, pady=16)
        self.result_headline_card.pack_propagate(False)

        # Headline inner
        self.lbl_result_status = ctk.CTkLabel(
            self.result_headline_card,
            text="No optimization job run yet",
            font=ctk.CTkFont(family=THEME["font_family"], size=13, weight="bold"),
            text_color=THEME["text_primary"],
        )
        self.lbl_result_status.pack(anchor="w", padx=16, pady=(12, 2))

        self.lbl_result_metrics = ctk.CTkLabel(
            self.result_headline_card,
            text="Select an image on the left, configure target size, and click 'Run Constrained Optimization'.",
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            text_color=THEME["text_secondary"],
        )
        self.lbl_result_metrics.pack(anchor="w", padx=16, pady=(0, 10))

        # Before / After Preview Side-by-Side Frames
        preview_container = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        preview_container.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        preview_container.columnconfigure(0, weight=1)
        preview_container.columnconfigure(1, weight=1)
        preview_container.rowconfigure(0, weight=1)

        # Left Preview Card (Original Master)
        self.card_src = ctk.CTkFrame(
            preview_container,
            fg_color=THEME["input_bg"],
            corner_radius=10,
            border_width=1,
            border_color=THEME["card_border"],
        )
        self.card_src.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        lbl_src_title = ctk.CTkLabel(
            self.card_src,
            text="Original Master",
            font=ctk.CTkFont(family=THEME["font_family"], size=11, weight="bold"),
            text_color=THEME["text_primary"],
        )
        lbl_src_title.pack(anchor="w", padx=12, pady=(10, 4))

        self.lbl_src_badge = ctk.CTkLabel(
            self.card_src,
            text="-",
            font=ctk.CTkFont(family=THEME["font_family"], size=10),
            text_color=THEME["text_muted"],
        )
        self.lbl_src_badge.pack(anchor="w", padx=12, pady=(0, 6))

        self.lbl_src_canvas = ctk.CTkLabel(
            self.card_src,
            text="Source image preview",
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            text_color=THEME["text_muted"],
        )
        self.lbl_src_canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Right Preview Card (Optimized Output)
        self.card_opt = ctk.CTkFrame(
            preview_container,
            fg_color=THEME["input_bg"],
            corner_radius=10,
            border_width=1,
            border_color=THEME["card_border"],
        )
        self.card_opt.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        lbl_opt_title = ctk.CTkLabel(
            self.card_opt,
            text="Optimized Result",
            font=ctk.CTkFont(family=THEME["font_family"], size=11, weight="bold"),
            text_color=THEME["success_text"],
        )
        lbl_opt_title.pack(anchor="w", padx=12, pady=(10, 4))

        self.lbl_opt_badge = ctk.CTkLabel(
            self.card_opt,
            text="-",
            font=ctk.CTkFont(family=THEME["font_family"], size=10),
            text_color=THEME["text_muted"],
        )
        self.lbl_opt_badge.pack(anchor="w", padx=12, pady=(0, 6))

        self.lbl_opt_canvas = ctk.CTkLabel(
            self.card_opt,
            text="Optimized preview will appear here",
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            text_color=THEME["text_muted"],
        )
        self.lbl_opt_canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Bottom Actions Bar
        bottom_actions = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        bottom_actions.pack(fill="x", padx=16, pady=(0, 16))

        self.btn_save_image = ctk.CTkButton(
            bottom_actions,
            text="Save Optimized Image...",
            font=ctk.CTkFont(family=THEME["font_family"], size=11, weight="bold"),
            fg_color=THEME["accent_blue"],
            hover_color=THEME["accent_hover"],
            corner_radius=8,
            height=34,
            state="disabled",
            command=self._save_image,
        )
        self.btn_save_image.pack(side="left", padx=(0, 8))

        self.btn_save_audit = ctk.CTkButton(
            bottom_actions,
            text="Export Audit JSON Certificate",
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            fg_color=THEME["pill_bg"],
            text_color=THEME["text_primary"],
            hover_color=THEME["pill_hover"],
            border_width=1,
            border_color=THEME["card_border"],
            corner_radius=8,
            height=34,
            state="disabled",
            command=self._save_audit,
        )
        self.btn_save_audit.pack(side="left")

    # --- UI Event Handlers ---
    def _open_output_folder(self):
        """Open artifacts/outputs in Windows Explorer."""
        out_dir = os.path.abspath(os.path.join(WORKSPACE_DIR, "artifacts", "outputs"))
        os.makedirs(out_dir, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(out_dir)

    def _set_interval(self, min_val: int, max_val: int):
        """Quick preset assignment."""
        self.seg_unit.set("KB")
        self.entry_min.delete(0, "end")
        self.entry_min.insert(0, str(min_val))
        self.entry_max.delete(0, "end")
        self.entry_max.insert(0, str(max_val))

    def _on_unit_change(self, val):
        pass

    def _browse_image(self):
        """Open native Windows file dialog to choose master image."""
        filetypes = [
            ("Image Files", "*.jpg;*.jpeg;*.png;*.webp;*.avif"),
            ("All Files", "*.*"),
        ]
        chosen = filedialog.askopenfilename(title="Select Master Image", filetypes=filetypes)
        if chosen and os.path.isfile(chosen):
            self._load_file(chosen)

    def _load_sample(self, filename: str):
        """Load one of the bundled sample benchmark images."""
        sample_path = os.path.join(WORKSPACE_DIR, "apps", "api", "static", "samples", filename)
        if os.path.isfile(sample_path):
            self._load_file(sample_path)
        else:
            messagebox.showwarning("Sample Not Found", f"Sample file {filename} could not be located.")

    def _load_file(self, filepath: str):
        """Load image bytes, read specs, and generate preview thumbnail."""
        try:
            with open(filepath, "rb") as f:
                content = f.read()

            pil_img = Image.open(filepath)
            self.source_filepath = filepath
            self.source_bytes = content
            self.source_pil = pil_img.copy()

            fname = os.path.basename(filepath)
            fsize_kb = len(content) / 1024
            w, h = pil_img.size

            self.lbl_selected_file.configure(text=fname)
            self.lbl_selected_specs.configure(text=f"{w}x{h} px • {pil_img.format or 'RAW'} • {fsize_kb:.1f} KB")

            # Render Source Preview in Right Card
            thumb_img = pil_img.copy()
            thumb_img.thumbnail((380, 380), Image.Resampling.LANCZOS)
            self.source_thumb = ctk.CTkImage(light_image=thumb_img, dark_image=thumb_img, size=thumb_img.size)
            self.lbl_src_canvas.configure(image=self.source_thumb, text="")
            self.lbl_src_badge.configure(text=f"{w}x{h} px • {fsize_kb:.1f} KB ({len(content):,} B)")

        except Exception as e:
            messagebox.showerror("Failed to Load Image", f"Error decoding image file:\n{e}")

    def _start_optimization(self):
        """Validate input parameters and dispatch in-process search thread."""
        if not self.source_bytes:
            messagebox.showwarning("No Master Image", "Please select or drop a master image first.")
            return

        if self.is_optimizing:
            return

        try:
            min_raw = float(self.entry_min.get().strip())
            max_raw = float(self.entry_max.get().strip())
            if min_raw <= 0 or max_raw <= 0 or min_raw > max_raw:
                messagebox.showerror("Invalid Interval", "Min target must be > 0 and <= Max target.")
                return
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric sizes for Min and Max.")
            return

        # Calculate exact target byte interval
        unit = self.seg_unit.get()
        mult = 1024 if unit == "KB" else (1024 * 1024 if unit == "MB" else 1)
        b_min = int(min_raw * mult)
        b_max = int(max_raw * mult)

        codec_raw = self.seg_codec.get().lower()
        requested_format = "auto" if codec_raw == "auto" else codec_raw

        qm_str = self.opt_quality.get().split()[0].lower()
        dim_str = "preserve_dimensions" if "Preserve" in self.opt_dim.get() else "joint_search"

        self.is_optimizing = True
        self.btn_optimize.configure(state="disabled", text="Optimizing...")
        self.btn_save_image.configure(state="disabled")
        self.btn_save_audit.configure(state="disabled")
        self.progress_bar.set(0.1)
        self.lbl_stage.configure(text="Constructing candidate space...")

        # Run direct in-process search in worker thread
        threading.Thread(
            target=self._run_optimization_thread,
            args=(b_min, b_max, requested_format, qm_str, dim_str),
            daemon=True,
        ).start()

    def _run_optimization_thread(self, b_min: int, b_max: int, fmt: str, quality_mode: str, dim_policy: str):
        """Direct in-process search execution."""
        try:
            fname = os.path.basename(self.source_filepath) if self.source_filepath else "source_image.png"

            # 1. Create Job model via JobService
            job = self.job_service.create_job(
                source_filename=fname,
                source_bytes=self.source_bytes,
                target_min_bytes=b_min,
                target_max_bytes=b_max,
                requested_format=fmt,
                quality_mode=quality_mode,
                dimension_policy=dim_policy,
            )
            self.current_job = job

            # 2. Execute job synchronously in background thread
            self._update_progress(0.3, "Executing multi-stage constrained search...")
            self.job_service.execute_job_sync(job.id)

            # 3. Handle results
            self._on_job_finished(job)

        except Exception as e:
            self._on_job_failed(str(e))

    def _update_progress(self, progress: float, stage_text: str):
        """Thread-safe UI progress update."""
        self.after(0, lambda: self._apply_progress(progress, stage_text))

    def _apply_progress(self, progress: float, stage_text: str):
        self.progress_bar.set(progress)
        self.lbl_stage.configure(text=stage_text)

    def _on_job_failed(self, error_msg: str):
        def _apply():
            self.is_optimizing = False
            self.btn_optimize.configure(state="normal", text="Run Constrained Optimization")
            self.progress_bar.set(0)
            self.lbl_stage.configure(text="Optimization failed")
            messagebox.showerror("Optimization Error", f"Search encountered an error:\n{error_msg}")

        self.after(0, _apply)

    def _on_job_finished(self, job: Job):
        def _apply():
            self.is_optimizing = False
            self.btn_optimize.configure(state="normal", text="Run Constrained Optimization")
            self.progress_bar.set(1.0)

            res = job.result
            if not res or job.status != JobStatus.COMPLETED:
                # Unreachable or Budget Exceeded
                st_val = job.status.value
                self.lbl_stage.configure(text=f"Completed: {st_val}")
                self.lbl_result_status.configure(
                    text=f"Target Interval Unreachable ({st_val})",
                    text_color=THEME["warn_text"],
                )
                self.lbl_result_metrics.configure(
                    text="No parameter combination fell strictly inside the target interval under current budget."
                )
                return

            # Success
            self.lbl_stage.configure(text="Optimization Completed!")
            self.btn_save_image.configure(state="normal")
            self.btn_save_audit.configure(state="normal")

            opt_kb = res.output_size_bytes / 1024
            savings = res.savings_percent or 0.0
            codec = (res.format or "").upper()
            butter = res.butteraugli_distance

            # Butteraugli explanation
            butter_note = "Indistinguishable" if (butter and butter < 0.5) else ("Below Noticeable Diff (JND)" if (butter and butter < 1.0) else "Minor visible difference")
            butter_str = f"Butteraugli: {butter:.4f} ({butter_note})" if butter is not None else "Butteraugli: N/A"

            self.lbl_result_status.configure(
                text=f"Optimal Feasible Candidate Found ({codec})",
                text_color=THEME["success_text"],
            )
            self.lbl_result_metrics.configure(
                text=f"Output: {opt_kb:.1f} KB ({res.output_size_bytes:,} B) • Saved {savings:.1f}% ({res.compression_ratio:.1f}x ratio) • {butter_str}"
            )

            # Load and display optimized preview
            if res.output_path and os.path.isfile(res.output_path):
                try:
                    opt_pil = Image.open(res.output_path)
                    self.optimized_pil = opt_pil.copy()

                    w, h = opt_pil.size
                    self.lbl_opt_badge.configure(text=f"{w}x{h} px • {opt_kb:.1f} KB ({res.output_size_bytes:,} B)")

                    disp_img = opt_pil.copy()
                    disp_img.thumbnail((380, 380), Image.Resampling.LANCZOS)
                    self.optimized_thumb = ctk.CTkImage(light_image=disp_img, dark_image=disp_img, size=disp_img.size)
                    self.lbl_opt_canvas.configure(image=self.optimized_thumb, text="")
                except Exception as e:
                    self.lbl_opt_canvas.configure(text=f"Could not render preview: {e}")

        self.after(0, _apply)

    def _save_image(self):
        """Save optimized output file to chosen destination via native Windows Save dialog."""
        if not self.current_job or not self.current_job.result or not self.current_job.result.output_path:
            return

        res = self.current_job.result
        fmt = (res.format or "webp").lower()
        default_name = res.output_filename or f"optimized_{self.current_job.id[:8]}.{fmt}"

        dest = filedialog.asksaveasfilename(
            title="Save Optimized Image",
            initialfile=default_name,
            defaultextension=f".{fmt}",
            filetypes=[(f"{fmt.upper()} Image", f"*.{fmt}"), ("All Files", "*.*")],
        )
        if dest:
            try:
                shutil.copyfile(res.output_path, dest)
                messagebox.showinfo("Saved", f"Optimized image saved successfully to:\n{dest}")
            except Exception as e:
                messagebox.showerror("Save Failed", f"Could not copy file:\n{e}")

    def _save_audit(self):
        """Export comprehensive JSON audit certificate."""
        if not self.current_job or not self.current_job.result:
            return

        res = self.current_job.result
        default_name = f"audit_{self.current_job.id[:8]}.json"

        dest = filedialog.asksaveasfilename(
            title="Save Audit Certificate JSON",
            initialfile=default_name,
            defaultextension=".json",
            filetypes=[("JSON Audit Report", "*.json"), ("All Files", "*.*")],
        )
        if dest:
            try:
                # Build audit payload
                audit_dict = {
                    "job_id": self.current_job.id,
                    "status": self.current_job.status.value,
                    "chosen_format": res.format,
                    "output_size_bytes": res.output_size_bytes,
                    "savings_percent": res.savings_percent,
                    "compression_ratio": res.compression_ratio,
                    "butteraugli_distance": res.butteraugli_distance,
                    "ssim": res.ssim,
                    "psnr_db": res.psnr_db,
                    "delta_e": res.delta_e,
                    "sha256_checksum": res.sha256_checksum,
                    "duration_ms": res.duration_ms,
                    "total_candidates_evaluated": res.total_candidates_evaluated,
                    "total_encodes_performed": res.total_encodes_performed,
                    "certificate": res.certificate.model_dump() if res.certificate else None,
                }
                with open(dest, "w", encoding="utf-8") as f:
                    json.dump(audit_dict, f, indent=2)
                messagebox.showinfo("Saved", f"Audit certificate JSON saved successfully to:\n{dest}")
            except Exception as e:
                messagebox.showerror("Save Failed", f"Could not write audit report:\n{e}")


def launch_modern_app():
    """Launch the modern bright in-process Windows application."""
    app = ModernOptimizerApp()
    app.mainloop()


if __name__ == "__main__":
    launch_modern_app()
