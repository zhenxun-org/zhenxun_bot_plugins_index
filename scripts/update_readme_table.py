#!/usr/bin/env python3
"""
更新 README.md 中的插件列表表格
"""

import json
import re
import sys
from pathlib import Path


def update_readme_table():
    """读取 plugins.json 并更新 README.md 中的插件列表表格"""

    # 读取 plugins.json
    plugins_json_path = Path("plugins.json")
    if not plugins_json_path.exists():
        print("❌ plugins.json 文件不存在！")
        return 1

    try:
        with open(plugins_json_path, "r", encoding="utf-8") as f:
            plugins = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ plugins.json 格式错误: {e}")
        return 1

    # 读取 README.md
    readme_path = Path("README.md")
    if not readme_path.exists():
        print("❌ README.md 文件不存在！")
        return 1

    with open(readme_path, "r", encoding="utf-8") as f:
        readme_content = f.read()

    # 使用正则表达式查找表格区域
    # 匹配从 <!-- PLUGIN_TABLE_START --> 到 <!-- PLUGIN_TABLE_END --> 之间的内容
    table_pattern = re.compile(
        r"(<!-- PLUGIN_TABLE_START -->\s*\n)(.*?)(\n\s*<!-- PLUGIN_TABLE_END -->)",
        re.DOTALL,
    )

    match = table_pattern.search(readme_content)
    if not match:
        print(
            "❌ 未找到表格标识符，请确保 README.md 中包含 <!-- PLUGIN_TABLE_START --> 和 <!-- PLUGIN_TABLE_END -->"
        )
        return 1

    # 提取表格内容（包含表头和分隔符）
    table_content = match.group(2).strip()
    table_lines = [line for line in table_content.split("\n") if line.strip()]

    # 找到表头和分隔符
    if len(table_lines) < 2:
        print("❌ 表格格式错误：缺少表头或分隔符")
        return 1

    table_header = table_lines[0]  # 表头
    table_separator = table_lines[1]  # 分隔符

    # 生成新的表格行
    table_rows = []
    for plugin in plugins:
        name = plugin.get("name", "")
        github_url = plugin.get("github_url", "")
        author = plugin.get("author", "")
        description = plugin.get("description", "").strip()

        # 如果描述有多行，只取第一行
        if "\n" in description:
            description = description.split("\n")[0].strip()

        # 构建表格行
        # 格式: | [插件名](github_url) | [@作者](https://github.com/作者) | 描述 |
        author_github_url = f"https://github.com/{author}" if author else ""
        row = f"| [{name}]({github_url}) | [@{author}]({author_github_url}) | {description} |"
        table_rows.append(row)

    # 构建新的表格内容（保留换行格式）
    new_table_content = "\n".join([table_header, table_separator] + table_rows)

    # 替换表格内容，保留标识符和换行
    new_content = table_pattern.sub(r"\1" + new_table_content + r"\3", readme_content)

    # 检查是否有实际更改
    if new_content == readme_content:
        print("ℹ️ README.md 中的插件列表表格没有变化")
        return 0

    # 写入新内容
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("✅ 成功更新 README.md 中的插件列表表格")
    print(f"共处理 {len(table_rows)} 个插件条目")
    return 0


if __name__ == "__main__":
    sys.exit(update_readme_table())
