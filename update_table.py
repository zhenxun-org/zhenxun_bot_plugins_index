import json
import os
import re
import sys

def extract_plugin_name(entry):
    match = re.search(r'\| \[(.*?)\]\(', entry)
    return match.group(1).strip() if match else None

def main():
    os.makedirs("indices", exist_ok=True)
    
    try:
        with open("plugins.json", "r", encoding="utf-8") as f:
            plugins = json.load(f)
    except FileNotFoundError:
        print("❌ plugins.json 文件不存在！")
        return 1
    except json.JSONDecodeError:
        print("❌ plugins.json 格式错误！")
        return 1

    new_entries = []
    for name, plugin in plugins.items():
        github_url = plugin.get("github_url", "")
        author = plugin.get("author", "")
        description = plugin.get("description", "").split("\n")[0].strip()
        
        entry = f"| [{name}]({github_url}) | [@{author}](https://github.com/{author}) | {description} |"
        new_entries.append((name, entry))

    output_path = os.path.join("indices", "Plugin-list.md")
    existing_entries = {}
    
    if not os.path.exists(output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("## 功能类插件索引\n\n<!-- 请在表首添加新行 -->\n\n")
            f.write("| 名称 | 作者 | 备注 |\n")
            f.write("| :----------------------------------------------------------- | ------------------------------------ | ---------------------------------- |\n")
    
    current_content = ""
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            current_content = f.read()
    
    if current_content:
        lines = current_content.split("\n")
        for line in lines:
            if line.strip().startswith("| [") and "](http" in line:
                plugin_name = extract_plugin_name(line)
                if plugin_name:
                    existing_entries[plugin_name] = line.strip()

    final_entries = []
    for name, entry in new_entries:
        final_entries.append(entry)
        if name in existing_entries:
            del existing_entries[name]
    
    for name in sorted(existing_entries.keys()):
        final_entries.append(existing_entries[name])
    
    # 生成新内容
    new_content = "## 功能类插件索引\n\n<!-- 请在表首添加新行 -->\n\n"
    new_content += "| 名称 | 作者 | 备注 |\n"
    new_content += "| :----------------------------------------------------------- | ------------------------------------ | ---------------------------------- |\n"
    new_content += "\n".join(final_entries) + "\n"
    
    # 检查是否有实际更改
    if new_content == current_content:
        print("ℹ️ 插件索引表格没有变化")
        return 78  # 特殊退出码表示无更改
    
    # 写入新内容
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"✅ 成功更新插件索引表格: {output_path}")
    print(f"共处理 {len(final_entries)} 个插件条目")
    print(f"其中 {len(new_entries)} 个来自 plugins.json, {len(existing_entries)} 个来自现有文件")
    return 0

if __name__ == "__main__":
    sys.exit(main())