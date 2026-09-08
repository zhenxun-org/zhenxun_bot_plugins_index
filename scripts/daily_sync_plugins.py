from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from aliyun_sync import (
    PluginMirror,
    SyncError,
    SyncSkipped,
    load_json,
    official_ali_url,
    parse_github_source,
    resolve_remote_commit,
    write_json,
)


def write_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as output:
        output.write(f"{name}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update Aliyun plugin mirrors and their tracked GitHub commits"
    )
    parser.add_argument("--plugins", type=Path, required=True)
    parser.add_argument("--commits", type=Path, required=True)
    parser.add_argument("--org-id", required=True)
    parser.add_argument("--namespace-id", type=int, required=True)
    parser.add_argument("--namespace-path", required=True)
    parser.add_argument("--access-token", required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    plugins = load_json(args.plugins)
    if not isinstance(plugins, list):
        raise ValueError("plugins.json must contain a JSON array")

    if args.commits.exists():
        commits = load_json(args.commits)
        if not isinstance(commits, dict):
            raise ValueError("plugin_commits.json must contain a JSON object")
    else:
        commits = {}

    mirror = PluginMirror(
        org_id=args.org_id,
        namespace_id=args.namespace_id,
        namespace_path=args.namespace_path,
        access_token=args.access_token,
        account=args.account,
        password=args.password,
    )

    next_commits: dict[str, str] = {}
    failures: list[str] = []
    skipped: list[str] = []
    synchronized = 0
    metadata_updated = False

    for plugin in plugins:
        name = str(plugin.get("name") or plugin.get("github_url") or "unknown")
        try:
            source = parse_github_source(plugin)
            previous_commit = str(commits.get(source.tracking_key, ""))
            latest_commit = resolve_remote_commit(source)
            expected_ali_url = official_ali_url(
                args.org_id, args.namespace_path, source.repository_name
            )
            metadata_needs_repair = (
                str(plugin.get("ali_url", "")).strip().rstrip("/") != expected_ali_url
                or not str(plugin.get("version", "")).strip()
            )
            if latest_commit == previous_commit and not metadata_needs_repair:
                next_commits[source.tracking_key] = previous_commit
                print(f"No source change: {name} ({latest_commit[:12]})")
                continue

            result = mirror.sync(plugin, repair_invalid_ali_url=True)
            if result.commit != latest_commit:
                print(
                    f"Source advanced while syncing {name}: "
                    f"{latest_commit[:12]} -> {result.commit[:12]}"
                )

            if plugin.get("ali_url") != result.ali_url:
                plugin["ali_url"] = result.ali_url
                metadata_updated = True
            if str(plugin.get("version", "")) != result.version:
                plugin["version"] = result.version
                metadata_updated = True

            next_commits[source.tracking_key] = result.commit
            synchronized += 1
            print(
                f"Updated {name}: version={result.version} "
                f"source={result.version_source} commit={result.commit[:12]}"
            )
        except SyncSkipped as error:
            skipped.append(f"{name}: {error}")
            next_commits[source.tracking_key] = latest_commit
            print(f"Skipped {name}: {error}")
        except (OSError, ValueError, SyncError) as error:
            failures.append(f"{name}: {error}")
            try:
                source = parse_github_source(plugin)
            except SyncError:
                source = None
            if source and source.tracking_key in commits:
                next_commits[source.tracking_key] = str(commits[source.tracking_key])
            print(f"Failed to update {name}: {error}", file=sys.stderr)

    if metadata_updated:
        write_json(args.plugins, plugins)
    if next_commits != commits or not args.commits.exists():
        write_json(args.commits, dict(sorted(next_commits.items())))

    write_output("synchronized_count", str(synchronized))
    write_output("failed_count", str(len(failures)))
    write_output("skipped_count", str(len(skipped)))
    write_output("has_failures", str(bool(failures)).lower())
    write_output(
        "failures", json.dumps(failures, ensure_ascii=False, separators=(",", ":"))
    )
    write_output(
        "skipped", json.dumps(skipped, ensure_ascii=False, separators=(",", ":"))
    )
    print(
        f"Daily synchronization updated {synchronized} plugin(s); "
        f"skipped {len(skipped)} plugin(s)"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, json.JSONDecodeError, SyncError) as error:
        print(f"Daily plugin synchronization failed: {error}", file=sys.stderr)
        sys.exit(1)
