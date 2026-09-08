from __future__ import annotations

import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from aliyun_sync import (  # noqa: E402
    GitHubSource,
    PluginMirror,
    SyncError,
    SyncSkipped,
    extract_version,
    official_ali_url,
    parse_github_source,
    repository_uses_git_lfs,
)


class GitHubSourceTests(unittest.TestCase):
    def test_parses_repository_and_tree_branch(self) -> None:
        source = parse_github_source(
            {"github_url": "https://github.com/example/plugin/tree/master"}
        )
        self.assertEqual(source.clone_url, "https://github.com/example/plugin.git")
        self.assertEqual(source.repository_name, "plugin")
        self.assertEqual(source.branch, "master")
        self.assertEqual(
            source.tracking_key, "https://github.com/example/plugin@master"
        )

    def test_explicit_branch_takes_priority(self) -> None:
        source = parse_github_source(
            {
                "github_url": "https://github.com/example/plugin/tree/master",
                "branch": "release",
            }
        )
        self.assertEqual(source.branch, "release")

    def test_rejects_non_github_url(self) -> None:
        with self.assertRaises(SyncError):
            parse_github_source({"github_url": "https://example.com/plugin.git"})

    def test_builds_official_ali_url(self) -> None:
        self.assertEqual(
            official_ali_url("org", "plugins", "demo"),
            "https://codeup.aliyun.com/org/plugins/demo",
        )


class VersionExtractionTests(unittest.TestCase):
    def test_reads_pep621_version(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            (repository / "pyproject.toml").write_text(
                '[project]\nname = "demo"\nversion = "1.2.3"\n',
                encoding="utf-8",
            )
            version, source = extract_version(repository, {}, "abcdef123456")
        self.assertEqual(version, "1.2.3")
        self.assertEqual(source, "pyproject.project")

    def test_reads_static_plugin_metadata_version(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            module = repository / "demo"
            module.mkdir()
            (module / "__init__.py").write_text(
                '__plugin_meta__ = PluginMetadata(extra={"version": "2.4.6"})\n',
                encoding="utf-8",
            )
            version, source = extract_version(
                repository,
                {"module": "demo", "module_path": "demo"},
                "abcdef123456",
            )
        self.assertEqual(version, "2.4.6")
        self.assertEqual(source, "python:demo/__init__.py")

    def test_falls_back_to_six_character_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            with patch("aliyun_sync._run", return_value=""):
                version, source = extract_version(repository, {}, "abcdef1234567890")
        self.assertEqual(version, "abcdef")
        self.assertEqual(source, "commit")


class GitLfsDetectionTests(unittest.TestCase):
    def test_detects_lfs_filter_in_committed_attributes(self) -> None:
        with patch(
            "aliyun_sync._run",
            side_effect=[
                "README.md\0assets/.gitattributes\0",
                "*.png filter=lfs diff=lfs merge=lfs -text\n",
            ],
        ):
            self.assertTrue(repository_uses_git_lfs(Path("repository")))

    def test_ignores_commented_lfs_filter(self) -> None:
        with patch(
            "aliyun_sync._run",
            side_effect=[
                ".gitattributes\0",
                "# *.png filter=lfs diff=lfs merge=lfs -text\n*.txt text\n",
            ],
        ):
            self.assertFalse(repository_uses_git_lfs(Path("repository")))


class MirrorVerificationTests(unittest.TestCase):
    def test_skips_lfs_repository_before_creating_aliyun_repository(self) -> None:
        mirror = PluginMirror(
            org_id="org",
            namespace_id=1,
            namespace_path="plugins",
            access_token="token",
            account="account",
            password="password",
        )
        mirror.client.ensure_repository = Mock()
        source = GitHubSource(
            clone_url="https://github.com/example/lfs-plugin.git",
            repository_name="lfs-plugin",
            branch="main",
        )
        with (
            patch("aliyun_sync.parse_github_source", return_value=source),
            patch("aliyun_sync._run", side_effect=["", "a" * 40]),
            patch("aliyun_sync.repository_uses_git_lfs", return_value=True),
        ):
            with self.assertRaises(SyncSkipped):
                mirror.sync(
                    {
                        "name": "LFS plugin",
                        "github_url": "https://github.com/example/lfs-plugin",
                    }
                )

        mirror.client.ensure_repository.assert_not_called()

    def test_pushes_and_verifies_exact_source_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_repository = root / "source"
            aliyun_repository = root / "aliyun.git"
            source_repository.mkdir()
            subprocess.run(
                ["git", "init", "--initial-branch=main"],
                cwd=source_repository,
                check=True,
                stdout=subprocess.DEVNULL,
            )
            (source_repository / "pyproject.toml").write_text(
                '[project]\nname = "demo"\nversion = "3.2.1"\n',
                encoding="utf-8",
            )
            subprocess.run(
                ["git", "add", "pyproject.toml"],
                cwd=source_repository,
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@example.com",
                    "commit",
                    "-m",
                    "initial",
                ],
                cwd=source_repository,
                check=True,
                stdout=subprocess.DEVNULL,
            )
            subprocess.run(
                ["git", "init", "--bare", str(aliyun_repository)],
                check=True,
                stdout=subprocess.DEVNULL,
            )

            mirror = PluginMirror(
                org_id="org",
                namespace_id=1,
                namespace_path="plugins",
                access_token="token",
                account="account",
                password="password",
            )
            mirror.client.ensure_repository = Mock()
            local_source = GitHubSource(
                clone_url=str(source_repository),
                repository_name="demo",
                branch="main",
            )
            with (
                patch("aliyun_sync.parse_github_source", return_value=local_source),
                patch.object(
                    mirror, "_authenticated_url", return_value=str(aliyun_repository)
                ),
            ):
                result = mirror.sync(
                    {
                        "name": "Demo",
                        "github_url": "https://github.com/example/demo",
                    }
                )

            remote_commit = subprocess.run(
                [
                    "git",
                    "--git-dir",
                    str(aliyun_repository),
                    "rev-parse",
                    "refs/heads/main",
                ],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()

        self.assertEqual(result.commit, remote_commit)
        self.assertEqual(result.version, "3.2.1")
        mirror.client.ensure_repository.assert_called_once()


if __name__ == "__main__":
    unittest.main()
