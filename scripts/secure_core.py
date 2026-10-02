"""Utility script to encrypt or decrypt the core proprietary source code.

Usage:
    python scripts/secure_core.py encrypt   # Encrypts all .py files in src/ and apps/
    python scripts/secure_core.py decrypt   # Decrypts all files back to plaintext source
    python scripts/secure_core.py status    # Shows encryption status of all core modules
"""

import sys
import os
import argparse

# Ensure workspace root is on sys.path
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from secure_loader import MAGIC, MASTER_SECRET, encrypt_code, decrypt_source

TARGET_DIRS = ["src", "apps"]


def get_core_files():
    files_to_process = []
    for d in TARGET_DIRS:
        full_d = os.path.join(WORKSPACE_DIR, d)
        if not os.path.exists(full_d):
            continue
        for root, dirs, files in os.walk(full_d):
            if "static" in root or "__pycache__" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    files_to_process.append(os.path.join(root, f))
    return files_to_process


def is_encrypted(file_path: str) -> bool:
    try:
        with open(file_path, "rb") as f:
            header = f.read(4)
        return header == MAGIC
    except Exception:
        return False


def encrypt_all():
    files = get_core_files()
    count = 0
    print(f"[*] Encrypting core modules in: {', '.join(TARGET_DIRS)}")
    for f in files:
        if is_encrypted(f):
            continue
        try:
            with open(f, "r", encoding="utf-8") as file_in:
                source = file_in.read()
            encrypted_payload = encrypt_code(source, MASTER_SECRET)
            with open(f, "wb") as file_out:
                file_out.write(encrypted_payload)
            rel_path = os.path.relpath(f, WORKSPACE_DIR)
            print(f"  [+] Encrypted: {rel_path}")
            count += 1
        except Exception as e:
            print(f"  [!] Failed to encrypt {f}: {e}")

    print(f"\n[SUCCESS] Successfully encrypted {count} core modules.")


def decrypt_all():
    files = get_core_files()
    count = 0
    print(f"[*] Decrypting core modules in: {', '.join(TARGET_DIRS)}")
    for f in files:
        if not is_encrypted(f):
            continue
        try:
            with open(f, "rb") as file_in:
                payload = file_in.read()
            source = decrypt_source(payload, MASTER_SECRET)
            with open(f, "w", encoding="utf-8") as file_out:
                file_out.write(source)
            rel_path = os.path.relpath(f, WORKSPACE_DIR)
            print(f"  [-] Decrypted to source: {rel_path}")
            count += 1
        except Exception as e:
            print(f"  [!] Failed to decrypt {f}: {e}")
    print(f"\n[SUCCESS] Decrypted {count} modules to plaintext source.")


def check_status():
    files = get_core_files()
    enc_count = 0
    plain_count = 0
    print(f"\n=== Core Source Code Protection Audit ({len(files)} modules found) ===")
    for f in sorted(files):
        rel_path = os.path.relpath(f, WORKSPACE_DIR)
        if is_encrypted(f):
            enc_count += 1
            print(f"  [ENCRYPTED] {rel_path}")
        else:
            plain_count += 1
            print(f"  [PLAINTEXT] {rel_path}")
    print(f"===========================================================")
    print(f"  Total Encrypted: {enc_count}")
    print(f"  Total Plaintext: {plain_count}")
    print(f"===========================================================\n")


def main():
    parser = argparse.ArgumentParser(description="Core Source Code Encryption Manager")
    parser.add_argument("action", choices=["encrypt", "decrypt", "status"], help="Action to perform")
    args = parser.parse_args()

    if args.action == "encrypt":
        encrypt_all()
    elif args.action == "decrypt":
        decrypt_all()
    elif args.action == "status":
        check_status()


if __name__ == "__main__":
    main()
