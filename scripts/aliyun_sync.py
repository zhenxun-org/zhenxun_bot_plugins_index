from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import tempfile
import urllib.parse
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


class SyncError(RuntimeError):
    """Raised when a GitHub repository cannot be mirrored safely."""


class SyncSkipped(RuntimeError):
    """Raised when a repository is intentionally excluded from mirroring."""


@dataclass(frozen=True)
class GitHubSource:
    clone_url: str
    repository_name: str
    branch: str | None

    @property
    def tracking_key(self) -> str:
        return f"{self.clone_url.removesuffix('.git')}@{self.branch or 'HEAD'}"


@dataclass(frozen=True)
class SyncResult:
    ali_url: str
    commit: str
    repository_name: str
    version: str
    version_source: str


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(value, file, ensure_ascii=False, indent=2)
        file.write("\n")


def parse_github_source(plugin: dict[str, Any]) -> GitHubSource:
    raw_url = str(plugin.get("github_url", "")).strip()
    parsed = urllib.parse.urlsplit(raw_url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() != "github.com":
        raise SyncError(f"Unsupported GitHub URL: {raw_url}")

    parts = [urllib.parse.unquote(part) for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        raise SyncError(f"Incomplete GitHub repository URL: {raw_url}")

    owner = parts[0]
    repository_name = parts[1].removesuffix(".git")
    name_pattern = re.compile(r"[A-Za-z0-9_.-]+")
    if (
        not name_pattern.fullmatch(owner)
        or not name_pattern.fullmatch(repository_name)
        or owner in {".", ".."}
        or repository_name in {".", ".."}
    ):
        raise SyncError(f"Incomplete GitHub repository URL: {raw_url}")

    configured_branch = str(plugin.get("branch", "")).strip() or None
    url_branch = None
    if len(parts) >= 4 and parts[2] in {"tree", "blob"}:
        url_branch = parts[3]
    branch = configured_branch or url_branch

    return GitHubSource(
        clone_url=f"https://github.com/{owner}/{repository_name}.git",
        repository_name=repository_name,
        branch=branch,
    )


def official_ali_url(org_id: str, namespace_path: str, repository_name: str) -> str:
    return f"https://codeup.aliyun.com/{org_id}/{namespace_path}/{repository_name}"


def _mask(text: str, secrets: Iterable[str]) -> str:
    for secret in secrets:
        if secret:
            text = text.replace(secret, "***")
            text = text.replace(urllib.parse.quote(secret, safe=""), "***")
    return text


def _run(
    arguments: list[str],
    *,
    cwd: Path | None = None,
    secrets: Iterable[str] = (),
) -> str:
    environment = os.environ.copy()
    environment["GIT_TERMINAL_PROMPT"] = "0"
    process = subprocess.run(
        arguments,
        cwd=cwd,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        command = " ".join(arguments[:2])
        details = _mask((process.stderr or process.stdout).strip(), secrets)
        raise SyncError(f"Command failed ({command}): {details}")
    return process.stdout.strip()


def resolve_remote_commit(source: GitHubSource) -> str:
    if source.branch:
        reference = f"refs/heads/{source.branch}"
        output = _run(["git", "ls-remote", "--heads", source.clone_url, reference])
    else:
        output = _run(["git", "ls-remote", source.clone_url, "HEAD"])
    if not output:
        target = source.branch or "HEAD"
        raise SyncError(f"Unable to resolve {target} for {source.clone_url}")
    return output.split()[0]


def repository_uses_git_lfs(repository: Path) -> bool:
    """Return whether committed attributes configure any Git LFS filter."""

    tracked_paths = _run(
        ["git", "ls-tree", "-r", "--name-only", "-z", "HEAD"],
        cwd=repository,
    ).split("\0")
    for relative_path in tracked_paths:
        if not relative_path or PurePosixPath(relative_path).name != ".gitattributes":
            continue
        attributes = _run(
            ["git", "show", f"HEAD:{relative_path}"],
            cwd=repository,
        )
        for raw_line in attributes.splitlines():
            line = raw_line.strip()
            if (
                line
                and not line.startswith("#")
                and re.search(r"(?:^|\s)filter\s*=\s*lfs(?:\s|$)", line)
            ):
                return True
    return False


def _literal_version(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return None
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if (
        isinstance(value, tuple)
        and value
        and all(isinstance(item, int) for item in value)
    ):
        return ".".join(str(item) for item in value)
    return None


def _version_from_metadata_node(node: ast.AST) -> str | None:
    if isinstance(node, ast.Dict):
        for key, value in zip(node.keys, node.values):
            if _literal_version(key) == "version":
                version = _literal_version(value)
                if version:
                    return version
    if isinstance(node, ast.Call):
        for keyword in node.keywords:
            if keyword.arg == "version":
                version = _literal_version(keyword.value)
                if version:
                    return version
            if keyword.arg == "extra":
                version = _version_from_metadata_node(keyword.value)
                if version:
                    return version
    for child in ast.iter_child_nodes(node):
        version = _version_from_metadata_node(child)
        if version:
            return version
    return None


def _version_from_python(path: Path) -> str | None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeDecodeError, SyntaxError):
        return None

    for statement in tree.body:
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            targets = (
                statement.targets
                if isinstance(statement, ast.Assign)
                else [statement.target]
            )
            value = statement.value
            for target in targets:
                if isinstance(target, ast.Name) and target.id in {
                    "__version__",
                    "VERSION",
                }:
                    version = _literal_version(value)
                    if version:
                        return version
                if isinstance(target, ast.Name) and target.id in {
                    "__plugin_meta__",
                    "plugin_meta",
                }:
                    version = _version_from_metadata_node(value)
                    if version:
                        return version
    return None


def _python_candidates(repository: Path, plugin: dict[str, Any]) -> list[Path]:
    candidates: list[Path] = []
    seen: set[Path] = set()

    for raw_module in (plugin.get("module_path"), plugin.get("module")):
        module = str(raw_module or "").strip()
        if not module or module == ".":
            continue
        module_path = Path(*module.split("."))
        for candidate in (
            repository / module_path / "__init__.py",
            repository / module_path.with_suffix(".py"),
        ):
            if candidate.is_file() and candidate not in seen:
                candidates.append(candidate)
                seen.add(candidate)

    root_init = repository / "__init__.py"
    if root_init.is_file() and root_init not in seen:
        candidates.append(root_init)
        seen.add(root_init)

    for candidate in sorted(repository.rglob("__init__.py")):
        if ".git" in candidate.parts or candidate in seen:
            continue
        candidates.append(candidate)
        seen.add(candidate)
        if len(candidates) >= 200:
            break
    return candidates


def extract_version(
    repository: Path, plugin: dict[str, Any], commit: str
) -> tuple[str, str]:
    try:
        import tomllib
    except ImportError:  # pragma: no cover - workflows use Python 3.11+
        tomllib = None

    if tomllib is not None:
        pyprojects = [repository / "pyproject.toml"]
        pyprojects.extend(sorted(repository.glob("*/pyproject.toml")))
        for pyproject in pyprojects:
            if not pyproject.is_file():
                continue
            try:
                with pyproject.open("rb") as file:
                    data = tomllib.load(file)
            except (OSError, tomllib.TOMLDecodeError):
                continue
            project_version = data.get("project", {}).get("version")
            if isinstance(project_version, str) and project_version.strip():
                return project_version.strip(), "pyproject.project"
            poetry_version = data.get("tool", {}).get("poetry", {}).get("version")
            if isinstance(poetry_version, str) and poetry_version.strip():
                return poetry_version.strip(), "pyproject.poetry"

    package_json = repository / "package.json"
    if package_json.is_file():
        try:
            package_version = load_json(package_json).get("version")
        except (OSError, json.JSONDecodeError, AttributeError):
            package_version = None
        if isinstance(package_version, str) and package_version.strip():
            return package_version.strip(), "package.json"

    for candidate in _python_candidates(repository, plugin):
        version = _version_from_python(candidate)
        if version:
            return version, f"python:{candidate.relative_to(repository).as_posix()}"

    tags = _run(["git", "tag", "--points-at", "HEAD"], cwd=repository)
    if tags:
        return sorted(tags.splitlines())[0].strip(), "git-tag"

    return commit[:6], "commit"


class AliyunClient:
    def __init__(
        self,
        *,
        org_id: str,
        namespace_id: int,
        namespace_path: str,
        access_token: str,
    ) -> None:
        self.org_id = org_id
        self.namespace_id = namespace_id
        self.namespace_path = namespace_path.strip("/")
        self.access_token = access_token

    def ensure_repository(self, repository_name: str, description: str) -> None:
        import requests

        full_path = f"{self.org_id}/{self.namespace_path}/{repository_name}"
        encoded_path = urllib.parse.quote(full_path, safe="")
        repository_url = (
            "https://openapi-rdc.aliyuncs.com/oapi/v1/codeup/organizations/"
            f"{self.org_id}/repositories/{encoded_path}"
        )
        headers = {
            "Content-Type": "application/json",
            "x-yunxiao-token": self.access_token,
        }
        try:
            response = requests.get(repository_url, headers=headers, timeout=30)
        except requests.RequestException as error:
            raise SyncError(
                f"Unable to query Aliyun repository {repository_name}: {error}"
            ) from error
        if response.status_code == 200:
            print(f"Aliyun repository already exists: {repository_name}")
            return
        if response.status_code != 404:
            raise SyncError(
                f"Unable to query Aliyun repository {repository_name}: "
                f"HTTP {response.status_code}"
            )

        create_url = (
            "https://openapi-rdc.aliyuncs.com/oapi/v1/codeup/organizations/"
            f"{self.org_id}/repositories"
        )
        payload = {
            "name": repository_name,
            "namespaceId": self.namespace_id,
            "visibility": "internal",
            "organizationId": self.org_id,
            "path": repository_name,
        }
        if description:
            payload["description"] = description
        try:
            response = requests.post(
                create_url,
                headers=headers,
                params={"createParentPath": "true"},
                json=payload,
                timeout=30,
            )
        except requests.RequestException as error:
            raise SyncError(
                f"Unable to create Aliyun repository {repository_name}: {error}"
            ) from error
        if response.status_code not in {200, 201, 409}:
            raise SyncError(
                f"Unable to create Aliyun repository {repository_name}: "
                f"HTTP {response.status_code}"
            )
        print(f"Aliyun repository is ready: {repository_name}")


class PluginMirror:
    def __init__(
        self,
        *,
        org_id: str,
        namespace_id: int,
        namespace_path: str,
        access_token: str,
        account: str,
        password: str,
    ) -> None:
        self.org_id = org_id
        self.namespace_path = namespace_path.strip("/")
        self.account = account
        self.password = password
        self.client = AliyunClient(
            org_id=org_id,
            namespace_id=namespace_id,
            namespace_path=self.namespace_path,
            access_token=access_token,
        )

    def _authenticated_url(self, repository_name: str) -> str:
        account = urllib.parse.quote(self.account, safe="")
        password = urllib.parse.quote(self.password, safe="")
        return (
            f"https://{account}:{password}@codeup.aliyun.com/{self.org_id}/"
            f"{self.namespace_path}/{repository_name}.git"
        )

    def sync(
        self,
        plugin: dict[str, Any],
        *,
        repair_invalid_ali_url: bool = False,
    ) -> SyncResult:
        source = parse_github_source(plugin)
        expected_ali_url = official_ali_url(
            self.org_id, self.namespace_path, source.repository_name
        )
        current_ali_url = str(plugin.get("ali_url", "")).strip().rstrip("/")

        description = str(plugin.get("description", "")).strip()
        github_url = str(plugin.get("github_url", "")).strip()
        repository_description = (
            f"{description}\n\nOriginal GitHub URL: {github_url}"
            if description
            else f"Original GitHub URL: {github_url}"
        )
        with tempfile.TemporaryDirectory(prefix="zhenxun-plugin-") as temporary:
            repository = Path(temporary) / "repository"
            clone_command = ["git", "clone", "--single-branch", "--no-checkout"]
            if source.branch:
                clone_command.extend(["--branch", source.branch])
            clone_command.extend([source.clone_url, str(repository)])
            _run(clone_command)

            source_commit = _run(["git", "rev-parse", "HEAD"], cwd=repository)
            if repository_uses_git_lfs(repository):
                raise SyncSkipped(
                    f"{source.repository_name} uses Git LFS and is excluded from "
                    "Aliyun synchronization"
                )

            _run(["git", "checkout", "--force", "HEAD"], cwd=repository)
            if current_ali_url and current_ali_url != expected_ali_url:
                if not repair_invalid_ali_url:
                    raise SyncError(
                        f"Unexpected ali_url for {source.repository_name}: "
                        f"{current_ali_url}"
                    )
                print(
                    f"Repairing ali_url for {source.repository_name}: "
                    f"{current_ali_url} -> {expected_ali_url}"
                )

            version, version_source = extract_version(repository, plugin, source_commit)

            self.client.ensure_repository(
                source.repository_name, repository_description
            )

            aliyun_url = self._authenticated_url(source.repository_name)
            secrets = (self.account, self.password)
            remote_output = _run(
                ["git", "ls-remote", "--heads", aliyun_url, "refs/heads/main"],
                secrets=secrets,
            )
            remote_commit = remote_output.split()[0] if remote_output else ""
            if remote_commit != source_commit:
                _run(
                    [
                        "git",
                        "push",
                        "--force",
                        aliyun_url,
                        "HEAD:refs/heads/main",
                    ],
                    cwd=repository,
                    secrets=secrets,
                )

            verified_output = _run(
                ["git", "ls-remote", "--heads", aliyun_url, "refs/heads/main"],
                secrets=secrets,
            )
            verified_commit = verified_output.split()[0] if verified_output else ""
            if verified_commit != source_commit:
                raise SyncError(
                    f"Aliyun verification failed for {source.repository_name}: "
                    f"expected {source_commit}, got {verified_commit or 'missing'}"
                )

        print(
            f"Aliyun mirror verified: {source.repository_name} "
            f"({source_commit[:12]})"
        )
        return SyncResult(
            ali_url=expected_ali_url,
            commit=source_commit,
            repository_name=source.repository_name,
            version=version,
            version_source=version_source,
        )


def mirror_local_repository(
    *,
    repository: Path,
    org_id: str,
    repository_path: str,
    branch: str,
    account: str,
    password: str,
) -> str:
    _run(["git", "check-ref-format", "--branch", branch], cwd=repository)
    current_commit = _run(["git", "rev-parse", "HEAD"], cwd=repository)
    encoded_account = urllib.parse.quote(account, safe="")
    encoded_password = urllib.parse.quote(password, safe="")
    aliyun_url = (
        f"https://{encoded_account}:{encoded_password}@codeup.aliyun.com/"
        f"{org_id}/{repository_path.strip('/')}.git"
    )
    secrets = (account, password)
    reference = f"refs/heads/{branch}"
    remote_output = _run(
        ["git", "ls-remote", "--heads", aliyun_url, reference], secrets=secrets
    )
    remote_commit = remote_output.split()[0] if remote_output else ""
    if remote_commit != current_commit:
        _run(
            ["git", "push", "--force", aliyun_url, f"HEAD:{reference}"],
            cwd=repository,
            secrets=secrets,
        )
    verified_output = _run(
        ["git", "ls-remote", "--heads", aliyun_url, reference], secrets=secrets
    )
    verified_commit = verified_output.split()[0] if verified_output else ""
    if verified_commit != current_commit:
        raise SyncError(
            f"Aliyun index verification failed: expected {current_commit}, "
            f"got {verified_commit or 'missing'}"
        )
    print(f"Aliyun index verified: {branch} ({current_commit[:12]})")
    return current_commit
