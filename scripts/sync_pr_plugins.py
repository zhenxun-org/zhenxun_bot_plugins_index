from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from aliyun_sync import (
    PluginMirror,
    SyncError,
    SyncSkipped,
    load_json,
    write_json,
)


def changed_plugins(
    base_plugins: list[dict[str, Any]], head_plugins: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    base_by_url = {
        plugin.get("github_url"): plugin
        for plugin in base_plugins
        if plugin.get("github_url")
    }
    return [
        plugin
        for plugin in head_plugins
        if plugin.get("github_url")
        and base_by_url.get(plugin.get("github_url")) != plugin
    ]


def write_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as output:
        output.write(f"{name}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize plugins changed by a pull request to Aliyun"
    )
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--head", type=Path, required=True)
    parser.add_argument("--org-id", required=True)
    parser.add_argument("--namespace-id", type=int, required=True)
    parser.add_argument("--namespace-path", required=True)
    parser.add_argument("--access-token", required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    base_plugins = load_json(args.base)
    head_plugins = load_json(args.head)
    if not isinstance(base_plugins, list) or not isinstance(head_plugins, list):
        raise ValueError("plugins.json must contain a JSON array")

    plugins_to_sync = changed_plugins(base_plugins, head_plugins)
    mirror = PluginMirror(
        org_id=args.org_id,
        namespace_id=args.namespace_id,
        namespace_path=args.namespace_path,
        access_token=args.access_token,
        account=args.account,
        password=args.password,
    )

    generated: list[dict[str, str]] = []
    skipped: list[str] = []
    pending_updates: list[tuple[dict[str, Any], str]] = []
    synchronized = 0
    for plugin in plugins_to_sync:
        name = str(plugin.get("name") or plugin.get("github_url") or "unknown")
        try:
            result = mirror.sync(plugin)
        except SyncSkipped as error:
            skipped.append(f"{name}: {error}")
            print(f"Skipped {name}: {error}")
            continue
        synchronized += 1
        current_ali_url = str(plugin.get("ali_url", "")).strip().rstrip("/")
        if not current_ali_url:
            pending_updates.append((plugin, result.ali_url))
            generated.append(
                {
                    "name": str(plugin.get("name", result.repository_name)),
                    "ali_url": result.ali_url,
                }
            )

    for plugin, ali_url in pending_updates:
        plugin["ali_url"] = ali_url

    metadata_updated = bool(pending_updates)
    if metadata_updated:
        write_json(args.head, head_plugins)

    write_output("changed_count", str(len(plugins_to_sync)))
    write_output("synchronized_count", str(synchronized))
    write_output("skipped_count", str(len(skipped)))
    write_output("metadata_updated", str(metadata_updated).lower())
    write_output(
        "generated_urls",
        json.dumps(generated, ensure_ascii=False, separators=(",", ":")),
    )
    write_output(
        "skipped", json.dumps(skipped, ensure_ascii=False, separators=(",", ":"))
    )
    print(
        f"Synchronized {synchronized} changed plugin(s); "
        f"skipped {len(skipped)} plugin(s)"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, json.JSONDecodeError, SyncError) as error:
        print(f"PR plugin synchronization failed: {error}", file=sys.stderr)
        sys.exit(1)
