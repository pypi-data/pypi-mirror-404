from __future__ import annotations

import argparse
import logging
import os

from .client import BaiduPanClient, BaiduPanConfig


def main() -> int:
    parser = argparse.ArgumentParser(prog="bdpan")
    parser.add_argument("--cookie-file", required=True, help="Path to cookies.txt (Cookie header or Netscape format)")
    parser.add_argument("--remote-root", default="/apps/bdpan", help="Remote root dir (default: /apps/bdpan)")
    parser.add_argument("--state-dir", default=None, help="Upload state dir for resume (optional)")
    parser.add_argument("--workers", type=int, default=4, help="Upload workers")
    parser.add_argument("--chunk-size", type=int, default=4 * 1024 * 1024, help="Chunk size in bytes")
    parser.add_argument("--debug", action="store_true", help="Enable debug logs")

    sub = parser.add_subparsers(dest="cmd", required=True)

    up = sub.add_parser("upload", help="Upload file or directory")
    up.add_argument("local_path")
    up.add_argument("--remote-path", default=None, help="Remote path (file) or remote dir (directory)")
    up.add_argument("--no-resume", action="store_true", help="Disable resume")
    up.add_argument("--overwrite", action="store_true", help="Overwrite if exists")

    sh = sub.add_parser("share", help="Create share link")
    sh.add_argument("remote_path", help="Remote file/dir path (relative to remote root or absolute)")
    sh.add_argument("--password", default=None)
    sh.add_argument("--period-days", type=int, default=7, help="Share period in days (0/1/7)")

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    client = BaiduPanClient(
        BaiduPanConfig(
            cookie_file=args.cookie_file,
            remote_root=args.remote_root,
            upload_workers=args.workers,
            chunk_size=args.chunk_size,
            state_dir=args.state_dir,
        )
    )

    if args.cmd == "upload":
        client.upload(
            args.local_path,
            remote_path=args.remote_path,
            resume=not args.no_resume,
            overwrite=args.overwrite,
        )
        return 0
    if args.cmd == "share":
        link = client.share(args.remote_path, password=args.password, period_days=args.period_days)
        print(link + (f"?pwd={args.password}" if args.password else ""))
        return 0

    raise RuntimeError(f"unknown command: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
