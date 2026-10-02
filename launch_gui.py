"""Primary Windows Desktop Application & Web Interface Launcher.

Default Mode:
  Runs the standalone, bright, minimalist professional native Windows desktop
  application directly in-process with ZERO server and ZERO network ports.

Optional Modes:
  --web       Starts the local Uvicorn web server and opens default browser
  --server    Runs headless API server only (no GUI)
  --port      Port for web server mode (default: 8000)
"""

import os
import sys
import argparse

# Ensure workspace root and runtime site-packages are on sys.path
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

RUNTIME_SITE = os.path.join(WORKSPACE_DIR, "runtime", "Lib", "site-packages")
if os.path.isdir(RUNTIME_SITE) and RUNTIME_SITE not in sys.path:
    sys.path.insert(1, RUNTIME_SITE)

os.chdir(WORKSPACE_DIR)

# Automatically activate in-memory decryption hook for encrypted core modules
try:
    import secure_loader  # noqa: F401
except ImportError:
    pass


def parse_args():
    parser = argparse.ArgumentParser(
        description="Adaptive Image Optimizer - Standalone Windows Application & Web Launcher"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--desktop",
        action="store_true",
        default=False,
        help="Launch standalone native Windows desktop application (Default, zero server)",
    )
    group.add_argument(
        "--web",
        action="store_true",
        default=False,
        help="Launch local web server and open default web browser",
    )
    group.add_argument(
        "--server",
        "--headless",
        action="store_true",
        default=False,
        help="Run headless API server only",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for web/server mode (default: 8000)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host for web/server mode (default: 127.0.0.1)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Ensure required artifact directories exist
    os.makedirs("artifacts/outputs", exist_ok=True)
    os.makedirs("artifacts/storage", exist_ok=True)

    # 1. Web Browser Mode
    if args.web:
        import time
        import socket
        import webbrowser
        import threading
        import uvicorn

        def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex((host, port)) == 0

        port = args.port
        while is_port_in_use(port, args.host):
            port += 1

        url = f"http://{args.host}:{port}"
        print("=" * 72)
        print("  Adaptive High-Quality Image Optimization System")
        print("  Mode: Web Browser Interface")
        print(f"  Server URL: {url}")
        print("=" * 72)

        def open_browser():
            time.sleep(1.2)
            print(f"\n[+] Opening browser at: {url}\n")
            webbrowser.open(url)

        threading.Thread(target=open_browser, daemon=True).start()
        uvicorn.run("apps.api.main:app", host=args.host, port=port, log_level="info")
        return

    # 2. Headless API Server Mode
    if args.server:
        import uvicorn
        print(f"[*] Starting headless FastAPI server at http://{args.host}:{args.port}...")
        uvicorn.run("apps.api.main:app", host=args.host, port=args.port, log_level="info")
        return

    # 3. Default: Standalone Native Windows Desktop Application (Zero Server)
    print("=" * 72)
    print("  Adaptive High-Quality Image Optimization System")
    print("  Mode: Standalone Native Windows Application (In-Process, Zero Server)")
    print("  UI: Bright Minimalist Professional")
    print("=" * 72)

    from apps.desktop.modern_app import launch_modern_app
    launch_modern_app()


if __name__ == "__main__":
    main()
