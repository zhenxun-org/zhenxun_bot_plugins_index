import json

# 读取插件数据
with open("plugins.json", "r", encoding="utf-8") as f:
    plugins = json.load(f)

# 读取现有表格内容
with open("indices/Plugin-list.md", "r", encoding="utf-8") as f:
    lines = f.readlines()

# 提取现有条目
existing_entries = []
in_table = False
for line in lines:
    if line.strip() == "| 名称":
        in_table = True
        continue
    if in_table and line.startswith("|"):
        existing_entries.append(line.strip())

# 生成新条目
new_entries = []
for name, plugin in plugins.items():
    github_url = plugin["github_url"]
    author = plugin["author"]
    description = plugin["description"].split("\n")[0].strip()  # 取description首行

    entry = f"| [{name}]({github_url}) | [@{author}](https://github.com/{author}) | {description} |"
    new_entries.append(entry)

# 合并现有条目（去重）
all_entries = new_entries + [e for e in existing_entries if e not in new_entries]

# 重新生成文件内容
with open("indices/Plugin-list.md", "w", encoding="utf-8") as f:
    f.write("## 功能类插件索引\n\n<!-- 请在表首添加新行 -->\n\n")
    f.write("| 名称 | 作者 | 备注 |\n")
    f.write(
        "| :----------------------------------------------------------- | ------------------------------------ | ---------------------------------- |\n"
    )
    for entry in all_entries:
        f.write(f"{entry}\n")
