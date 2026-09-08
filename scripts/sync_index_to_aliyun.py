from __future__ import annotations

import argparse
import sys
from pathlib import Path

from aliyun_sync import SyncError, mirror_local_repository


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mirror the final plugin index commit to Aliyun"
    )
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--org-id", required=True)
    parser.add_argument("--repository-path", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    mirror_local_repository(
        repository=args.repository,
        org_id=args.org_id,
        repository_path=args.repository_path,
        branch=args.branch,
        account=args.account,
        password=args.password,
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SyncError as error:
        print(f"Index synchronization failed: {error}", file=sys.stderr)
        sys.exit(1)
