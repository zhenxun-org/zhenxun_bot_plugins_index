"""插件加载测试

测试代码修改自 <https://github.com/nonebot/noneflow>，谢谢 [NoneBot](https://github.com/nonebot)。

在 GitHub Actions 中运行，通过 GitHub Event 文件获取所需信息。并将测试结果保存至 GitHub Action 的输出文件中。

当前会输出 RESULT, OUTPUT, METADATA 三个数据，分别对应测试结果、测试输出、插件元数据。

经测试可以直接在 Python 3.10+ 环境下运行，无需额外依赖。
"""

# ruff: noqa: T201, ASYNC101

import asyncio
import json
import os
import re
from asyncio import create_subprocess_shell, run, subprocess
from pathlib import Path
from urllib.request import urlopen

# Plugin Store
STORE_PLUGINS_URL = "https://raw.githubusercontent.com/zhenxun-org/zhenxun_bot_plugins_index/index/plugins.json"
# 匹配信息的正则表达式
ISSUE_PATTERN = r"### {}\s+([^\s#].*?)(?=(?:\s+###|$))"
# 插件信息
PLUGIN_NAME_PATTERN = re.compile(ISSUE_PATTERN.format("插件名称"))
PLUGIN_MODULE_NAME_PATTERN = re.compile(ISSUE_PATTERN.format("模块名称"))
PLUGIN_MODULE_PATH_PATTERN = re.compile(ISSUE_PATTERN.format("模块路径"))
PLUGIN_GITHUB_URL_PATTERN = re.compile(ISSUE_PATTERN.format("仓库地址"))
IS_DIR_PATTERN = re.compile(ISSUE_PATTERN.format("是否为目录"))
CONFIG_PATTERN = re.compile(r"### 插件配置项\s+```(?:\w+)?\s?([\s\S]*?)```")

FAKE_SCRIPT = """from typing import Optional, Union

from nonebot import logger
from nonebot.drivers import (
    ASGIMixin,
    HTTPClientMixin,
    HTTPClientSession,
    HTTPVersion,
    Request,
    Response,
    WebSocketClientMixin,
)
from nonebot.drivers import Driver as BaseDriver
from nonebot.internal.driver.model import (
    CookieTypes,
    HeaderTypes,
    QueryTypes,
)
from typing_extensions import override


class Driver(BaseDriver, ASGIMixin, HTTPClientMixin, WebSocketClientMixin):
    @property
    @override
    def type(self) -> str:
        return "fake"

    @property
    @override
    def logger(self):
        return logger

    @override
    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)

    @property
    @override
    def server_app(self):
        return None

    @property
    @override
    def asgi(self):
        raise NotImplementedError

    @override
    def setup_http_server(self, setup):
        raise NotImplementedError

    @override
    def setup_websocket_server(self, setup):
        raise NotImplementedError

    @override
    async def request(self, setup: Request) -> Response:
        raise NotImplementedError

    @override
    async def websocket(self, setup: Request) -> Response:
        raise NotImplementedError

    @override
    def get_session(
        self,
        params: QueryTypes = None,
        headers: HeaderTypes = None,
        cookies: CookieTypes = None,
        version: Union[str, HTTPVersion] = HTTPVersion.H11,
        timeout: Optional[float] = None,
        proxy: Optional[str] = None,
    ) -> HTTPClientSession:
        raise NotImplementedError
"""

RUNNER_SCRIPT = """import json
import os
import asyncio
from pathlib import Path

from nonebot import init, load_plugin, logger, require, load_plugins
from pydantic import BaseModel


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


init()
load_plugins("zhenxun/builtin_plugins")
from zhenxun.builtin_plugins.plugin_store.data_source import ShopManage, download_file

url_path = ShopManage.get_url_path("{module_path}", {is_dir})
if not url_path:
    logger.error("插件下载地址构建失败...")
    exit(1)
asyncio.run(download_file("{github_download_url}".format(url_path)))
plugin = load_plugin(Path(__file__).parent / "zhenxun"/ "plugins" / "{module_name}")

if not plugin:
    exit(1)
else:
    if plugin.metadata:
        metadata = {{
            "name": "{plugin_name}",
            "module": "{module_name}",
            "module_path": "{module_path}",
            "description": plugin.metadata.description,
            "usage": plugin.metadata.usage,
            "author": plugin.metadata.extra["author"],
            "version": plugin.metadata.extra["version"],
            "plugin_type": plugin.metadata.extra["plugin_type"],
            "is_dir": {is_dir},
            "github_url": "{github_url}",
        }}
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf8") as f:
            f.write(f"METADATA<<EOF\\n{{json.dumps(metadata, cls=SetEncoder)}}\\nEOF\\n")

        if plugin.metadata.config and not issubclass(plugin.metadata.config, BaseModel):
            logger.error("插件配置项不是 Pydantic BaseModel 的子类")
            exit(1)

{deps}
"""


def strip_ansi(text: str | None) -> str:
    """去除 ANSI 转义字符"""
    if not text:
        return ""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def get_plugin_list() -> dict[str, str]:
    """获取插件列表

    通过 package_name 获取 module_name
    """
    with urlopen(STORE_PLUGINS_URL) as response:
        plugins = json.loads(response.read())

    return {plugin["plugin_name"]: plugin["module_name"] for plugin in plugins}


class PluginTest:
    def __init__(
        self,
        plugin_name: str,
        module_name: str,
        module_path: str,
        github_url: str,
        is_dir: bool,
        config: str | None = None,
    ) -> None:
        self.plugin_name = plugin_name
        self.module_name = module_name
        self.module_path = module_path
        self.github_url = github_url
        self.is_dir = is_dir
        self.config = config
        self._plugin_list = None

        self._create = False
        self._run = False
        self._deps = []

        # 输出信息
        self._output_lines: list[str] = []

        # 插件测试目录
        self.test_dir = Path("zhenxun/plugins")
        # 通过环境变量获取 GITHUB 输出文件位置
        self.github_output_file = Path(os.environ.get("GITHUB_OUTPUT", ""))
        self.github_step_summary_file = Path(os.environ.get("GITHUB_STEP_SUMMARY", ""))

    @property
    def key(self) -> str:
        """插件的标识符

        plugin_name:module_name
        例：nonebot-plugin-test:nonebot_plugin_test
        """
        return f"{self.module_name}"

    @property
    def path(self) -> Path:
        """插件测试目录"""
        # 替换 : 为 -，防止文件名不合法
        key = self.key.replace(":", "-")
        # return self.test_dir / f"{key}"
        return Path()

    async def run(self):
        # 运行前创建测试目录
        if not self.test_dir.exists():
            self.test_dir.mkdir()

        await self.create_poetry_project()
        if self._create:
            # await self.show_package_info()
            # await self.show_plugin_dependencies()
            await self.run_poetry_project()

        # 输出测试结果
        with open(self.github_output_file, "a", encoding="utf8") as f:
            f.write(f"RESULT={self._run}\n")
        # 输出测试输出
        output = "\n".join(self._output_lines)
        # GitHub 不支持 ANSI 转义字符所以去掉
        ansiless_output = strip_ansi(output)
        # 限制输出长度，防止评论过长，评论最大长度为 65536
        ansiless_output = ansiless_output[:50000]
        with open(self.github_output_file, "a", encoding="utf8") as f:
            f.write(f"OUTPUT<<EOF\n{ansiless_output}\nEOF\n")
        # 输出至作业摘要
        with open(self.github_step_summary_file, "a", encoding="utf8") as f:
            summary = f"插件 {self.plugin_name} 加载测试结果：{'通过' if self._run else '未通过'}\n"
            summary += f"<details><summary>测试输出</summary><pre><code>{ansiless_output}</code></pre></details>"
            f.write(f"{summary}")
        return self._run, output

    def get_env(self) -> dict[str, str]:
        """获取环境变量"""
        env = os.environ.copy()
        # 删除虚拟环境变量，防止 poetry 使用运行当前脚本的虚拟环境
        env.pop("VIRTUAL_ENV", None)
        # 启用 LOGURU 的颜色输出
        env["LOGURU_COLORIZE"] = "true"
        # Poetry 配置
        # https://python-poetry.org/docs/configuration/#virtualenvsin-project
        env["POETRY_VIRTUALENVS_IN_PROJECT"] = "true"
        # https://python-poetry.org/docs/configuration/#virtualenvsprefer-active-python-experimental
        env["POETRY_VIRTUALENVS_PREFER_ACTIVE_PYTHON"] = "true"
        return env

    async def create_poetry_project(self) -> None:
        if not self.path.exists():
            self.path.mkdir()
            proc = await create_subprocess_shell(
                f"""poetry init -n && sed -i "s/\\^/~/g" pyproject.toml && poetry env info --ansi""",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.path,
                env=self.get_env(),
            )
            stdout, stderr = await proc.communicate()
            code = proc.returncode

            self._create = not code
            if self._create:
                print(f"项目 {self.plugin_name} 创建成功。")
                for i in stdout.decode().strip().splitlines():
                    print(f"    {i}")
            else:
                self._log_output(f"项目 {self.plugin_name} 创建失败：")
                for i in stderr.decode().strip().splitlines():
                    self._log_output(f"    {i}")
        else:
            self._log_output(f"项目 {self.plugin_name} 已存在，跳过创建。")
            self._create = True

    async def show_package_info(self) -> None:
        if self.path.exists():
            proc = await create_subprocess_shell(
                f"poetry show {self.plugin_name} --ansi",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.path,
                env=self.get_env(),
            )
            stdout, _ = await proc.communicate()
            code = proc.returncode
            if not code:
                self._log_output(f"插件 {self.plugin_name} 的信息如下：")
                for i in stdout.decode().splitlines():
                    self._log_output(f"    {i}")
            else:
                self._log_output(f"插件 {self.plugin_name} 信息获取失败。")

    async def show_plugin_dependencies(self) -> None:
        if self.path.exists():
            proc = await create_subprocess_shell(
                "poetry export --without-hashes",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.path,
                env=self.get_env(),
            )
            stdout, _ = await proc.communicate()
            code = proc.returncode
            if not code:
                self._log_output(f"插件 {self.plugin_name} 依赖的插件如下：")
                for i in stdout.decode().strip().splitlines():
                    module_name = self._get_plugin_module_name(i)
                    if module_name:
                        self._deps.append(module_name)
                self._log_output(f"    {', '.join(self._deps)}")
            else:
                self._log_output(f"插件 {self.plugin_name} 依赖获取失败。")

    async def run_poetry_project(self) -> None:
        if self.path.exists():
            # 默认使用 fake 驱动
            with open(self.path / ".env", "w", encoding="utf8") as f:
                f.write("DRIVER=fake")
            # 如果提供了插件配置项，则写入配置文件
            if self.config is not None:
                with open(self.path / ".env.prod", "w", encoding="utf8") as f:
                    f.write(self.config)

            with open(self.path / "fake.py", "w", encoding="utf8") as f:
                f.write(FAKE_SCRIPT)
            with open(self.path / "runner.py", "w", encoding="utf8") as f:
                f.write(
                    RUNNER_SCRIPT.format(
                        plugin_name=self.plugin_name,
                        module_name=self.module_name,
                        module_path=self.module_path,
                        github_url=self.github_url,
                        github_download_url=self.get_github_download_url(),
                        is_dir=self.is_dir,
                        deps="\n".join([f"require('{i}')" for i in self._deps]),
                    )
                )

            try:
                proc = await create_subprocess_shell(
                    "poetry run python runner.py",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=self.path,
                    env=self.get_env(),
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=600)
                code = proc.returncode
            except asyncio.TimeoutError:
                proc.terminate()
                stdout = b""
                stderr = "测试超时".encode()
                code = 1

            self._run = not code

            status = "正常" if self._run else "出错"
            self._log_output(f"插件 {self.module_name} 加载{status}：")

            _out = stdout.decode().strip().splitlines()
            _err = stderr.decode().strip().splitlines()
            for i in _out:
                self._log_output(f"    {i}")
            for i in _err:
                self._log_output(f"    {i}")

    def get_github_download_url(self) -> str:
        username, repo = re.match(r"https://github.com/(.+)/(.+)(?:\.git)?", self.github_url).groups()
        return "https://api.github.com/repos/{}/{}/contents/{{}}?ref=main".format(username, repo)

    def _log_output(self, output: str) -> None:
        """记录输出，同时打印到控制台"""
        print(output)
        self._output_lines.append(output)

    @property
    def plugin_list(self) -> dict[str, str]:
        """获取插件列表"""
        if self._plugin_list is None:
            self._plugin_list = get_plugin_list()
        return self._plugin_list

    def _get_plugin_module_name(self, require: str) -> str | None:
        # anyio==3.6.2 ; python_version >= "3.11" and python_version < "4.0"
        # pydantic[dotenv]==1.10.6 ; python_version >= "3.10" and python_version < "4.0"
        match = re.match(r"^(.+?)(?:\[.+\])?==", require.strip())
        if match:
            package_name = match.group(1)
            # 不用包括自己
            if package_name in self.plugin_list and package_name != self.plugin_name:
                return self.plugin_list[package_name]


async def test() -> None:
    issue_body = """
### 插件名称
github订阅

### 模块名称
github_sub

### 模块路径
github_sub

### 仓库地址
https://github.com/xuanerwa/zhenxun_github_sub

### 是否为目录
是

### 插件配置项
```
SYSTEM_PROXY="http://127.0.0.1:7890"
```
    """
    plugin_name = PLUGIN_NAME_PATTERN.search(issue_body)
    module_name = PLUGIN_MODULE_NAME_PATTERN.search(issue_body)
    module_path = PLUGIN_MODULE_PATH_PATTERN.search(issue_body)
    plugin_github_url = PLUGIN_GITHUB_URL_PATTERN.search(issue_body)
    is_dir_text = IS_DIR_PATTERN.search(issue_body)
    config = CONFIG_PATTERN.search(issue_body)
    print(plugin_name, module_name, module_path, plugin_github_url, is_dir_text, config)

    if not (
        plugin_name
        and module_name
        and module_path
        and plugin_github_url
        and is_dir_text
    ):
        print("议题中没有插件信息，已跳过")
        return
    is_dir = True
    if is_dir_text.group(1).strip() == "是":
        is_dir = True
    elif is_dir_text.group(1).strip() == "否":
        is_dir = False

    # 测试插件
    test = PluginTest(
        plugin_name=plugin_name.group(1).strip(),
        module_name=module_name.group(1).strip(),
        module_path=module_path.group(1).strip(),
        github_url=plugin_github_url.group(1).strip(),
        is_dir=is_dir,
        config=config.group(1).strip() if config else None,
    )
    await test.run()


async def main():
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        print("未找到 GITHUB_EVENT_PATH，已跳过")
        return

    with open(event_path, encoding="utf8") as f:
        event = json.load(f)

    event_name = os.environ.get("GITHUB_EVENT_NAME")
    if event_name not in ["issues", "issue_comment"]:
        print(f"不支持的事件: {event_name}，已跳过")
        return

    issue = event["issue"]

    pull_request = issue.get("pull_request")
    if pull_request:
        print("评论在拉取请求下，已跳过")
        return

    state = issue.get("state")
    if state != "open":
        print("议题未开启，已跳过")
        return

    labels = issue.get("labels", [])
    if not any(label["name"] == "Plugin" for label in labels):
        print("议题与插件发布无关，已跳过")
        return

    issue_body = issue.get("body")
    plugin_name = PLUGIN_NAME_PATTERN.search(issue_body)
    module_name = PLUGIN_MODULE_NAME_PATTERN.search(issue_body)
    module_path = PLUGIN_MODULE_PATH_PATTERN.search(issue_body)
    plugin_github_url = PLUGIN_GITHUB_URL_PATTERN.search(issue_body)
    is_dir_text = IS_DIR_PATTERN.search(issue_body)
    config = CONFIG_PATTERN.search(issue_body)

    if not (
        plugin_name
        and module_name
        and module_path
        and plugin_github_url
        and is_dir_text
    ):
        print("议题中没有插件信息，已跳过")
        return
    is_dir = True
    if is_dir_text.group(1).strip() == "是":
        is_dir = True
    elif is_dir_text.group(1).strip() == "否":
        is_dir = False

    # 测试插件
    test = PluginTest(
        plugin_name=plugin_name.group(1).strip(),
        module_name=module_name.group(1).strip(),
        module_path=module_path.group(1).strip(),
        github_url=plugin_github_url.group(1).strip(),
        is_dir=is_dir,
        config=config.group(1).strip() if config else None,
    )
    ok, msg = await test.run()
    if ok:
        print("测试通过")


if __name__ == "__main__":
    run(main())
