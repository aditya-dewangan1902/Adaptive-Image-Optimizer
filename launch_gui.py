"""Windows Desktop Application & Web Interface Launcher.

Default:
  Runs the desktop application directly.

Options:
  --web       Starts the local web interface and opens browser
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


def parse_args():
    parser = argparse.ArgumentParser(
        description="Adaptive Image Optimizer"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--desktop",
        action="store_true",
        default=False,
        help="Launch desktop application (default)",
    )
    group.add_argument(
        "--web",
        action="store_true",
        default=False,
        help="Launch web interface",
    )
    group.add_argument(
        "--server",
        "--headless",
        action="store_true",
        default=False,
        help="Run headless API server",
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
        print(f"Starting web server at {url}...")

        def open_browser():
            time.sleep(1.2)
            webbrowser.open(url)

        threading.Thread(target=open_browser, daemon=True).start()
        uvicorn.run("apps.api.main:app", host=args.host, port=port, log_level="info")
        return

    # 2. Headless API Server Mode
    if args.server:
        import uvicorn
        print(f"Starting API server at http://{args.host}:{args.port}...")
        uvicorn.run("apps.api.main:app", host=args.host, port=args.port, log_level="info")
        return

    # 3. Default: Desktop Application
    from apps.desktop.modern_app import launch_modern_app
    launch_modern_app()


if __name__ == "__main__":
    main()
