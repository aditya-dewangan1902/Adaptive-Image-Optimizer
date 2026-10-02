# Adaptive High-Quality Image Optimization System

[![GitHub Release](https://img.shields.io/badge/Release-v1.0.0--Portable-blue.svg)](https://github.com/aditya-dewangan1902/Adaptive-Image-Optimizer/releases)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Tests: 25/25 Passing](https://img.shields.io/badge/Tests-25%2F25%20Passing-success.svg)](tests/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#-two-ways-to-run)
[![UI: Modern Light](https://img.shields.io/badge/UI-Bright%20Minimalist%20Desktop-informational.svg)](#-standalone-windows-desktop-application)

A bounded, constrained image-optimization engine that solves the budgeted search problem: finding the visually highest-quality representation strictly within a user-defined target file size interval $[B_{min}, B_{max}]$.

---

## 🎯 Mathematical Formulation & Objective Semantics

Rather than claiming an unprovable global minimum over an unobserved search space, the system solves the **budgeted constrained search problem**:

$$
\hat{\theta} = \arg\min_{\theta \in E(job)} D_{primary}\Big(I,\ \text{Decode}\big(\text{Encode}(I, \theta)\big)\Big)
$$

subject to:

$$
B_{min} \le B(\theta) \le B_{max}
$$

where:
- $\Theta(job)$ is the finite, enumerable set of candidate parameter combinations.
- $E(job) \subseteq \Theta(job)$ is the subset of candidate configurations actually evaluated under the computational search budget (`max_total_encodes`, `max_wall_clock_ms`).
- $D_{primary}$ is the Butteraugli psychovisual distance in the declared comparison space (`sRGB_8bit`).
- $B(\theta)$ is the exact measured artifact byte size on disk.
- **User-Facing Semantics**: *"Best verified feasible candidate found within the configured search budget."*

---

## 📦 Two Ways to Run

### Option 1: End Users — Zero-Install Portable Windows Application (Recommended)
No Python installation or command-line experience required.
1. Download **`Adaptive_Image_Optimizer_v1.0.0_Portable_Windows.zip`** from [GitHub Releases](https://github.com/aditya-dewangan1902/Adaptive-Image-Optimizer/releases).
2. Extract the ZIP file to any folder or USB drive.
3. Double-click [`launch_gui.bat`](launch_gui.bat) to launch immediately.

### Option 2: Developers — Git Clone & Source Setup
For contributors and developers running from source or on Linux/macOS:
```bash
# 1. Clone the repository
git clone https://github.com/aditya-dewangan1902/Adaptive-Image-Optimizer.git
cd Adaptive-Image-Optimizer

# 2. Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch Desktop Application or Web Interface
python launch_gui.py          # Native In-Process Desktop GUI
python launch_gui.py --web    # Optional Web Browser Interface
```

---

## 🖥️ Standalone Windows Desktop Application

The primary desktop experience is a native, in-process Windows GUI:

- **Zero-Server Architecture**: Runs **directly in-process** calling `JobService` in Python memory. **Zero web servers, zero localhost sockets, zero port conflicts, and instant startup.**
- **Bright Minimalist Professional UI/UX**: Designed with a clean light aesthetic:
  - Canvas: Slate background (`#F8FAFC`) with pure white elevated surface cards (`#FFFFFF`).
  - Typography: Crisp native typography (Segoe UI / Helvetica) with high-contrast text (`#0F172A`).
  - Accents: Royal blue focus states (`#2563EB`) and mint green badges (`#047857`).
  - Non-distracting layout without dark gaming or neon aesthetics.
- **Side-by-Side Visual Inspection**: Real-time comparative canvas displaying original master versus compressed output with exact pixel dimensions, scale factors, and byte size badges.
- **Native Windows OS Integration**:
  - 📂 **Open Outputs Folder**: 1-click button to launch Windows File Explorer directly to `artifacts/outputs`.
  - 💾 **Native Save Dialogs**: Save optimized images and JSON audit certificates to any folder on your machine.

---

## 🌐 Web Browser Mode (Optional)

If you need a browser-based interface or want to expose the optimizer over a local network:
- Double-click [`launch_web.bat`](launch_web.bat) or execute:
```bash
python launch_gui.py --web --port 8000
```
This spins up the FastAPI backend, opens your default browser at `http://127.0.0.1:8000`, and serves the interactive client.

### Command-Line Arguments Reference

| Flag | Description | Default |
| :--- | :--- | :---: |
| *(none)* | Launches standalone in-process Desktop GUI | Active |
| `--desktop` | Explicitly launch the native in-process Desktop GUI | Active |
| `--web` | Start FastAPI server and open web browser | Disabled |
| `--server` | Start headless FastAPI API server only | Disabled |
| `--host HOST` | Bind host address for web/server mode | `127.0.0.1` |
| `--port PORT` | Bind port for web/server mode | `8000` |

---

## ✨ Core Features & Engineering Safeguards

- **Dual Target Size Interval Controls**: Specify exact $[B_{min}, B_{max}]$ with instant unit conversion (KB, MB, Bytes) and quick presets (*Mobile/Thumb <80 KB*, *Web Banner 80–200 KB*, *Email Attachment <500 KB*, *Hero Image 0.5–1 MB*).
- **Conservative Candidate Triage**: Replaces unsafe proxy Pareto dominance with conservative candidate screening, preserving representation across distinct codec cells, candidates bracketing target boundaries, and top proxy candidates.
- **Formal Feasibility Certificates**: Unreachability statuses (`CONSTRAINT_UNREACHABLE_MIN`, `CONSTRAINT_UNREACHABLE_MAX`) are only emitted when backed by a verified `FeasibilityCertificate` establishing exhaustive or analytic proof. Budget exhaustion emits `CANDIDATE_BUDGET_EXCEEDED` or `TIME_BUDGET_EXCEEDED` with `proven=False`.
- **Modular Codec Support**:
  - **AVIF**: Modern AV1 image codec via `pillow-heif` / `libavif` with tuned effort, chroma subsampling (4:2:0 / 4:4:4), and depth parameters.
  - **WebP**: Google WebP codec supporting lossy and lossless modes, alpha preservation, and effort tuning.
  - **JPEG**: MozJPEG-compatible progressive encoding, Huffman table optimization, and chroma subsampling.
  - **PNG**: Palette quantization, adaptive row filtering, and compression level controls.
- **Runtime Codec & Backend Verification**: Explicit diagnostics distinguish active encoder backends without false assumptions (`python scripts/verify_environment.py`).
- **Normalized Quality Abstraction**: Internal search represents quality in normalized space $[0.0, 1.0]$ and maps to encoder-native parameters, with local refinement sampling ordered neighbor points in the codec's actual native space.
- **Auditability**: 1-click **Download Artifact** and **Download Audit JSON** recording checksums, encoder versions, comparison spaces, feasibility certificates, and candidate evaluation history.

---

## 🏛️ Repository Layout

```text
ImageOptimizer_Portable/
├── .github/
│   └── workflows/ci.yml       # GitHub Actions automated test workflow
├── launch_gui.bat             # 1-click Standalone Desktop Application launcher
├── launch_web.bat             # 1-click Web Browser Interface launcher
├── launch_gui.py              # Unified CLI launcher (--desktop, --web, --server)
├── runtime/                   # Bundled portable Python runtime (distributed via Releases)
├── apps/
│   ├── desktop/               # Standalone In-Process Windows GUI
│   │   ├── __init__.py
│   │   └── modern_app.py      # Bright Minimalist CustomTkinter Desktop Application
│   ├── api/                   # FastAPI routes, schemas, and static Web GUI
│   │   ├── main.py
│   │   ├── routes/            # health.py, jobs.py, results.py
│   │   ├── schemas/           # jobs.py, results.py
│   │   └── static/            # index.html, style.css, app.js, samples/
│   └── worker/                # Worker consumers, tasks, and sandbox audit
├── src/
│   ├── domain/                # Models, policies, certificates, and status codes
│   ├── image/                 # Validation, canonicalization, decoding, analysis
│   ├── encoders/              # Modular codec adapters (AVIF, WebP, JPEG, PNG)
│   ├── quality/               # Perceptual evaluation (Butteraugli, SSIM, PSNR, Delta-E)
│   ├── optimization/          # Multi-stage constrained search engine
│   ├── services/              # JobService, OptimizationService, ResultService
│   └── infrastructure/        # Storage, cache, telemetry
├── configs/                   # base.yaml, fast.yaml, balanced.yaml, max_quality.yaml
├── scripts/
│   ├── package_release.py     # 1-click packager for GitHub Releases ZIP
│   ├── verify_environment.py  # Diagnostics for encoder backends and PIL plugins
│   └── secure_core.py         # Core integrity loader & security wrapper
├── tests/                     # Property invariants, codec tests, perceptual quality tests
├── requirements.txt           # Python package dependencies
├── pyproject.toml             # Project metadata, build specs, and tooling config
├── CONTRIBUTING.md            # Guidelines for contributors
├── LICENSE                    # MIT License
└── README.md
```

---

## 🧪 Automated Test Suite (25 / 25 Passing)

The project includes invariant property tests, encoder tests, and perceptual quality tests:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

### Test Results

| Category | Test Case | Invariant / Property Verified | Status |
| :--- | :--- | :--- | :---: |
| **Property Invariants** (8) | `test_p1_provenance_invariant` | P1: Master provenance; never derived from lossy candidate | ✅ Passed |
| | `test_p2_actual_bytes_feasibility` | P2: Feasibility uses exact measured bytes | ✅ Passed |
| | `test_p3_budget_does_not_imply_unreachability` | P3: FeasibilityCertificate required for unreachability | ✅ Passed |
| | `test_p4_theta_is_finite_and_enumerable` | P4: Finite, bounded search space $\Theta(job)$ | ✅ Passed |
| | `test_p5_final_output_independently_encoded` | P5: Output independently encoded & verified | ✅ Passed |
| | `test_p6_comparison_space_symmetric` | P6: Declared comparison space conversion is symmetric | ✅ Passed |
| | `test_p7_max_total_encodes_never_exceeded` | P7: Hard budget ceiling enforced | ✅ Passed |
| | `test_sandbox_enforcement_audit` | Distinction between specification and kernel enforcement | ✅ Passed |
| **Codec Tests** (4) | `test_jpeg_encoder` | MozJPEG / progressive / 4:2:0 & 4:4:4 | ✅ Passed |
| | `test_webp_encoder` | WebP lossy/lossless & alpha channels | ✅ Passed |
| | `test_avif_encoder` | AVIF encoding & decoding via libavif / dav1d | ✅ Passed |
| | `test_png_encoder` | PNG adaptive compression / palette quantization | ✅ Passed |
| **Perceptual Quality** (6) | `test_butteraugli_identical` | Butteraugli distance = 0.0 for identical input | ✅ Passed |
| | `test_butteraugli_distortion` | Psychovisual sensitivity to distortion | ✅ Passed |
| | `test_ssim` | Structural Similarity Index | ✅ Passed |
| | `test_psnr` | Peak Signal to Noise Ratio | ✅ Passed |
| | `test_delta_e` | CIEDE2000 Color Space Difference | ✅ Passed |
| | `test_evaluator` | Full perceptual evaluator and guardrails | ✅ Passed |
| **Integration** (1) | `test_complete_optimization_workflow` | End-to-end multi-stage pipeline run within $[B_{min}, B_{max}]$ | ✅ Passed |

---

## 🛠️ Building the Portable Release Package

To create the zero-install portable ZIP for GitHub Releases:

```powershell
python scripts/package_release.py
```

This automatically packages the application, documentation, launchers, and bundled portable runtime into:
`Adaptive_Image_Optimizer_v1.0.0_Portable_Windows.zip` (~42 MB), ready to attach to any GitHub Release.

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on code style, branch structure, and test execution.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
