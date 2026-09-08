from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import daily_sync_plugins  # noqa: E402
import sync_pr_plugins  # noqa: E402
from aliyun_sync import SyncError, SyncResult, SyncSkipped  # noqa: E402
from sync_pr_plugins import changed_plugins  # noqa: E402


class PullRequestDiffTests(unittest.TestCase):
    def test_detects_new_and_modified_plugins(self) -> None:
        unchanged = {"name": "A", "github_url": "https://github.com/o/a"}
        old_b = {
            "name": "B",
            "version": "1.0",
            "github_url": "https://github.com/o/b",
        }
        new_b = {**old_b, "version": "1.1"}
        new_c = {"name": "C", "github_url": "https://github.com/o/c"}

        result = changed_plugins([unchanged, old_b], [unchanged, new_b, new_c])

        self.assertEqual(result, [new_b, new_c])

    def test_does_not_upload_deleted_plugins(self) -> None:
        deleted = {"name": "A", "github_url": "https://github.com/o/a"}
        self.assertEqual(changed_plugins([deleted], []), [])

    def test_writes_ali_url_only_after_successful_mirror(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base_path = root / "base.json"
            head_path = root / "head.json"
            base_path.write_text("[]", encoding="utf-8")
            head_path.write_text(
                json.dumps(
                    [
                        {
                            "name": "Demo",
                            "github_url": "https://github.com/example/demo",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            fake_mirror = Mock()
            fake_mirror.sync.return_value = SyncResult(
                ali_url="https://codeup.aliyun.com/org/plugins/demo",
                commit="abcdef123456",
                repository_name="demo",
                version="1.0",
                version_source="pyproject.project",
            )
            arguments = self._pr_arguments(base_path, head_path)
            with (
                patch.object(sys, "argv", arguments),
                patch.object(sync_pr_plugins, "PluginMirror", return_value=fake_mirror),
                patch.dict(os.environ, {}, clear=False),
            ):
                os.environ.pop("GITHUB_OUTPUT", None)
                result = sync_pr_plugins.main()

            updated = json.loads(head_path.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(
            updated[0]["ali_url"],
            "https://codeup.aliyun.com/org/plugins/demo",
        )

    def test_does_not_write_ali_url_when_mirror_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base_path = root / "base.json"
            head_path = root / "head.json"
            original = [
                {
                    "name": "Demo",
                    "github_url": "https://github.com/example/demo",
                }
            ]
            base_path.write_text("[]", encoding="utf-8")
            head_path.write_text(json.dumps(original), encoding="utf-8")
            fake_mirror = Mock()
            fake_mirror.sync.side_effect = SyncError("upload failed")
            arguments = self._pr_arguments(base_path, head_path)
            with (
                patch.object(sys, "argv", arguments),
                patch.object(sync_pr_plugins, "PluginMirror", return_value=fake_mirror),
                patch.dict(os.environ, {}, clear=False),
            ):
                os.environ.pop("GITHUB_OUTPUT", None)
                with self.assertRaises(SyncError):
                    sync_pr_plugins.main()

            unchanged = json.loads(head_path.read_text(encoding="utf-8"))

        self.assertEqual(unchanged, original)

    def test_lfs_plugin_is_skipped_without_failing_pull_request(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base_path = root / "base.json"
            head_path = root / "head.json"
            plugin = {
                "name": "LFS plugin",
                "github_url": "https://github.com/example/lfs-plugin",
            }
            base_path.write_text("[]", encoding="utf-8")
            head_path.write_text(json.dumps([plugin]), encoding="utf-8")
            fake_mirror = Mock()
            fake_mirror.sync.side_effect = SyncSkipped("Git LFS repository")

            with (
                patch.object(sys, "argv", self._pr_arguments(base_path, head_path)),
                patch.object(sync_pr_plugins, "PluginMirror", return_value=fake_mirror),
                patch.dict(os.environ, {}, clear=False),
            ):
                os.environ.pop("GITHUB_OUTPUT", None)
                result = sync_pr_plugins.main()

            unchanged = json.loads(head_path.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(unchanged, [plugin])

    @staticmethod
    def _pr_arguments(base_path: Path, head_path: Path) -> list[str]:
        return [
            "sync_pr_plugins.py",
            "--base",
            str(base_path),
            "--head",
            str(head_path),
            "--org-id",
            "org",
            "--namespace-id",
            "1",
            "--namespace-path",
            "plugins",
            "--access-token",
            "token",
            "--account",
            "account",
            "--password",
            "password",
        ]


class DailySynchronizationTests(unittest.TestCase):
    def test_lfs_plugin_resumes_sync_after_lfs_is_removed(self) -> None:
        lfs_commit = "1111111111111111111111111111111111111111"
        normal_commit = "2222222222222222222222222222222222222222"
        tracking_key = "https://github.com/example/lfs-plugin@main"
        plugin = {
            "name": "LFS plugin",
            "version": "1.1",
            "github_url": "https://github.com/example/lfs-plugin/tree/main",
        }

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plugins_path = root / "plugins.json"
            commits_path = root / "plugin_commits.json"
            plugins_path.write_text(
                json.dumps([plugin], ensure_ascii=False), encoding="utf-8"
            )
            commits_path.write_text("{}", encoding="utf-8")
            fake_mirror = Mock()
            fake_mirror.sync.side_effect = [
                SyncSkipped("Git LFS repository"),
                SyncResult(
                    ali_url="https://codeup.aliyun.com/org/plugins/lfs-plugin",
                    commit=normal_commit,
                    repository_name="lfs-plugin",
                    version="2.0",
                    version_source="pyproject.project",
                ),
            ]
            arguments = [
                "daily_sync_plugins.py",
                "--plugins",
                str(plugins_path),
                "--commits",
                str(commits_path),
                "--org-id",
                "org",
                "--namespace-id",
                "1",
                "--namespace-path",
                "plugins",
                "--access-token",
                "token",
                "--account",
                "account",
                "--password",
                "password",
            ]
            with (
                patch.object(sys, "argv", arguments),
                patch.object(
                    daily_sync_plugins, "PluginMirror", return_value=fake_mirror
                ),
                patch.object(
                    daily_sync_plugins,
                    "resolve_remote_commit",
                    side_effect=[lfs_commit, normal_commit],
                ),
                patch.dict(os.environ, {}, clear=False),
            ):
                os.environ.pop("GITHUB_OUTPUT", None)
                first_result = daily_sync_plugins.main()
                first_plugins = json.loads(plugins_path.read_text(encoding="utf-8"))
                first_commits = json.loads(commits_path.read_text(encoding="utf-8"))
                second_result = daily_sync_plugins.main()

            plugins = json.loads(plugins_path.read_text(encoding="utf-8"))
            commits = json.loads(commits_path.read_text(encoding="utf-8"))

        self.assertEqual(first_result, 0)
        self.assertEqual(first_plugins, [plugin])
        self.assertEqual(first_commits[tracking_key], lfs_commit)
        self.assertEqual(second_result, 0)
        self.assertEqual(
            plugins[0]["ali_url"],
            "https://codeup.aliyun.com/org/plugins/lfs-plugin",
        )
        self.assertEqual(plugins[0]["version"], "2.0")
        self.assertEqual(commits[tracking_key], normal_commit)
        self.assertEqual(fake_mirror.sync.call_count, 2)

    def test_updates_version_and_full_commit_after_successful_mirror(self) -> None:
        full_commit = "abcdef1234567890abcdef1234567890abcdef12"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plugins_path = root / "plugins.json"
            commits_path = root / "plugin_commits.json"
            plugins_path.write_text(
                json.dumps(
                    [
                        {
                            "name": "Demo",
                            "version": "1.0",
                            "github_url": "https://github.com/example/demo",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            commits_path.write_text("{}", encoding="utf-8")

            fake_mirror = Mock()
            fake_mirror.sync.return_value = SyncResult(
                ali_url="https://codeup.aliyun.com/org/plugins/demo",
                commit=full_commit,
                repository_name="demo",
                version="abcdef",
                version_source="commit",
            )
            arguments = [
                "daily_sync_plugins.py",
                "--plugins",
                str(plugins_path),
                "--commits",
                str(commits_path),
                "--org-id",
                "org",
                "--namespace-id",
                "1",
                "--namespace-path",
                "plugins",
                "--access-token",
                "token",
                "--account",
                "account",
                "--password",
                "password",
            ]
            with (
                patch.object(sys, "argv", arguments),
                patch.object(
                    daily_sync_plugins, "PluginMirror", return_value=fake_mirror
                ),
                patch.object(
                    daily_sync_plugins,
                    "resolve_remote_commit",
                    return_value=full_commit,
                ),
                patch.dict(os.environ, {}, clear=False),
            ):
                os.environ.pop("GITHUB_OUTPUT", None)
                result = daily_sync_plugins.main()

            plugins = json.loads(plugins_path.read_text(encoding="utf-8"))
            commits = json.loads(commits_path.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(plugins[0]["version"], "abcdef")
        self.assertEqual(
            plugins[0]["ali_url"],
            "https://codeup.aliyun.com/org/plugins/demo",
        )
        self.assertEqual(commits["https://github.com/example/demo@HEAD"], full_commit)

    def test_keeps_previous_metadata_and_commit_when_mirror_fails(self) -> None:
        tracking_key = "https://github.com/example/demo@HEAD"
        previous_commit = "1111111111111111111111111111111111111111"
        latest_commit = "2222222222222222222222222222222222222222"
        original_plugin = {
            "name": "Demo",
            "version": "1.0",
            "github_url": "https://github.com/example/demo",
            "ali_url": "https://codeup.aliyun.com/org/plugins/demo",
        }

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plugins_path = root / "plugins.json"
            commits_path = root / "plugin_commits.json"
            plugins_path.write_text(json.dumps([original_plugin]), encoding="utf-8")
            commits_path.write_text(
                json.dumps({tracking_key: previous_commit}), encoding="utf-8"
            )

            fake_mirror = Mock()
            fake_mirror.sync.side_effect = SyncError("upload failed")
            arguments = [
                "daily_sync_plugins.py",
                "--plugins",
                str(plugins_path),
                "--commits",
                str(commits_path),
                "--org-id",
                "org",
                "--namespace-id",
                "1",
                "--namespace-path",
                "plugins",
                "--access-token",
                "token",
                "--account",
                "account",
                "--password",
                "password",
            ]
            with (
                patch.object(sys, "argv", arguments),
                patch.object(
                    daily_sync_plugins, "PluginMirror", return_value=fake_mirror
                ),
                patch.object(
                    daily_sync_plugins,
                    "resolve_remote_commit",
                    return_value=latest_commit,
                ),
                patch.dict(os.environ, {}, clear=False),
            ):
                os.environ.pop("GITHUB_OUTPUT", None)
                result = daily_sync_plugins.main()

            plugins = json.loads(plugins_path.read_text(encoding="utf-8"))
            commits = json.loads(commits_path.read_text(encoding="utf-8"))

        self.assertEqual(result, 1)
        self.assertEqual(plugins, [original_plugin])
        self.assertEqual(commits[tracking_key], previous_commit)


if __name__ == "__main__":
    unittest.main()
