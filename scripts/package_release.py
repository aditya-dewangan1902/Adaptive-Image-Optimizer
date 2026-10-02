"""Packaging script for Adaptive Image Optimizer Portable Windows Release.

Creates a self-contained zero-install ZIP distribution including the bundled
portable runtime, launcher scripts, and application code.
"""

import os
import sys
import zipfile
import shutil

VERSION = "1.0.0"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_NAME = f"Adaptive_Image_Optimizer_v{VERSION}_Portable_Windows"
OUTPUT_ZIP = os.path.join(PROJECT_ROOT, f"{DIST_NAME}.zip")

# Directories and files to include
INCLUDED_PATHS = [
    "launch_gui.bat",
    "launch_web.bat",
    "launch_gui.py",
    "pyproject.toml",
    "requirements.txt",
    "README.md",
    "LICENSE",
    "apps",
    "configs",
    "docs",
    "runtime",
    "scripts",
    "src",
]



def should_skip(file_path: str) -> bool:
    """Return True if path should be omitted from release zip."""
    parts = file_path.replace("\\", "/").split("/")
    if "__pycache__" in parts or ".pytest_cache" in parts:
        return True
    if any(p.endswith((".pyc", ".pyo", ".pyd.tmp", ".log")) for p in parts):
        return True
    if "artifacts/outputs" in file_path and not file_path.endswith(".gitkeep"):
        return True
    return False


def build_release_zip():
    print(f"[*] Packaging {DIST_NAME}.zip...")

    if os.path.exists(OUTPUT_ZIP):
        os.remove(OUTPUT_ZIP)

    count = 0
    total_bytes = 0

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # Include base directories
        for item in INCLUDED_PATHS:
            full_path = os.path.join(PROJECT_ROOT, item)
            if not os.path.exists(full_path):
                continue

            if os.path.isfile(full_path):
                rel_path = os.path.join(DIST_NAME, item)
                zf.write(full_path, rel_path)
                count += 1
                total_bytes += os.path.getsize(full_path)
            else:
                for root, dirs, files in os.walk(full_path):
                    for file in files:
                        file_full = os.path.join(root, file)
                        rel_file = os.path.relpath(file_full, PROJECT_ROOT)
                        if should_skip(rel_file):
                            continue
                        zip_entry = os.path.join(DIST_NAME, rel_file)
                        zf.write(file_full, zip_entry)
                        count += 1
                        total_bytes += os.path.getsize(file_full)

        # Ensure empty artifacts directories have .gitkeep
        for folder in ["artifacts/outputs", "artifacts/storage"]:
            keep_file = os.path.join(PROJECT_ROOT, folder, ".gitkeep")
            if os.path.exists(keep_file):
                zip_entry = os.path.join(DIST_NAME, folder, ".gitkeep")
                zf.write(keep_file, zip_entry)

    zip_size_mb = os.path.getsize(OUTPUT_ZIP) / (1024 * 1024)
    print(f"[+] Successfully built: {OUTPUT_ZIP}")
    print(f"[+] Total files archived: {count}")
    print(f"[+] Final ZIP size: {zip_size_mb:.2f} MB")
    print("\n[+] This ZIP archive can now be uploaded directly as a GitHub Release asset!")


if __name__ == "__main__":
    build_release_zip()
