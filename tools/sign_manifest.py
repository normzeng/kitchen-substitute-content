#!/usr/bin/env python3
"""Sign a content manifest with the ed25519 content key (secrets/content_signing_key.pem).

Signs the canonical string (must match UpdateConfig.canonicalString in UpdateService.swift):
    kitchen-substitute:content:v{pack_version}:s{schema_version}:{sha256_hex}

Usage:
  tools/sign_manifest.py --pack-version 2 --schema-version 1 --sha256 <hex> --size <bytes> \
      --entry-count <n> --url <pack_url> [--key secrets/content_signing_key.pem]

Prints manifest.json to stdout. Uses the openssl CLI (no pip dependencies).
"""
import argparse
import base64
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack-version", type=int, required=True)
    ap.add_argument("--schema-version", type=int, default=1)
    ap.add_argument("--sha256", required=True)
    ap.add_argument("--size", type=int, required=True)
    ap.add_argument("--entry-count", type=int, required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--released", required=True, help="ISO timestamp")
    ap.add_argument("--key", default=str(Path(__file__).parent.parent / "secrets" / "content_signing_key.pem"))
    args = ap.parse_args()

    key_path = Path(args.key)
    if not key_path.exists():
        print(f"FATAL: signing key not found at {key_path}", file=sys.stderr)
        return 1

    canonical = (f"kitchen-substitute:content:v{args.pack_version}"
                 f":s{args.schema_version}:{args.sha256.lower()}").encode()
    with tempfile.NamedTemporaryFile() as msg:
        msg.write(canonical)
        msg.flush()
        sig = subprocess.run(
            ["openssl", "pkeyutl", "-sign", "-inkey", args.key, "-rawin", "-in", msg.name],
            capture_output=True, check=True).stdout

    manifest = {
        "schema_version": args.schema_version,
        "pack_version": args.pack_version,
        "released": args.released,
        "entry_count": args.entry_count,
        "sha256": args.sha256.lower(),
        "url": args.url,
        "sig_key_id": "k1",
        "sig": base64.b64encode(sig).decode(),
    }
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
