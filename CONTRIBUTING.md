# Contributing to Adaptive Image Optimizer

Thank you for your interest in contributing to the **Adaptive Image Optimizer** project! This document outlines the development workflow, testing standards, and pull request guidelines.

---

## 🛠️ Development Setup

### 1. Prerequisites
- Python 3.10+ (Python 3.11 or 3.12 recommended)
- Git

### 2. Clone the Repository
```bash
git clone https://github.com/<your-username>/Adaptive-Image-Optimizer.git
cd Adaptive-Image-Optimizer
```

### 3. Create a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🧪 Running the Test Suite

Run the full automated test suite (invariant property tests, encoder tests, quality evaluation, and desktop tests):

```bash
python -m unittest discover tests -v
```

All 25 automated tests should pass before submitting any pull request.

---

## 🚀 Running Locally

### Standalone Windows Application (In-Process)
```bash
python launch_gui.py
```

### Web Browser Interface
```bash
python launch_gui.py --web
```

### Headless API Server
```bash
python launch_gui.py --server --port 8000
```

---

## 📦 Packaging Portable Release Asset

To create a self-contained zero-install ZIP archive for Windows:
```bash
python scripts/package_release.py
```
This generates `Adaptive_Image_Optimizer_v1.0.0_Portable_Windows.zip` ready for upload to GitHub Releases.

---

## 📝 Code Guidelines

1. **Typing & Documentation**: Include Python type hints and docstrings for all new functions, domain models, and service methods.
2. **Deterministic Feasibility**: Never claim unverified feasibility; any feasibility claim must be proven strictly against exact measured artifact bytes.
3. **Clean Architecture**: Respect boundary separation between `src/domain`, `src/optimization`, `src/encoders`, `apps/desktop`, and `apps/api`.
4. **Git Commits**: Use descriptive commit messages following the Conventional Commits specification (e.g. `feat: ...`, `fix: ...`, `docs: ...`, `test: ...`).

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
