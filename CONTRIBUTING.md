# 插件库贡献指南

首先，欢迎您为真寻机器人编写/适配插件

接下来，请阅读这篇文章，了解如何将插件上传至插件库

## 格式

### 提交

插件库对提交信息并无硬性规定，不过我们建议使用如下格式

```
feat: add `插件名` plugin
```

### Issue/Pull Request 标题

```
Feat: add `插件名` plugin
```

## 发起 Issue 

您可以根据 [Issue 模板](./.github/ISSUE_TEMPLATE/plugin.md)，将插件信息填入，并附带 `Plugin` 标签，我们会在空闲时对插件进行审核

在审核通过后，我们会将插件添加至索引

如果您愿意，可以参考下方的 `表格样式` 修改`indices`目录下的 `Function-Plugin.md`，并根据 `发起 Pull Request` 发布修改

## 表格样式

```markdown
| [插件名](仓库地址) | [@作者名](作者 GitHub 地址) | 插件备注 |
```

例如下面的成分姬插件

```markdown
| [github订阅](https://github.com/xuanerwa/zhenxun_github_sub) | [@xuanerwa](https://github.com/xuanerwa) | 用来推送github用户动态或仓库动态                             |
```

## 发起 Pull Request

提交 Pull Request 目前有两种模板

### 指向 Issue

您可以将 Pull Request 指向为先前开启的 Issue，同样，我们也不对标题有硬性规定，不过我们建议使用如下格式

```
Feat: add `插件名` plugin for #Issue编号
```

### 直接上传插件

你可以根据 [Issue 模板](./.github/ISSUE_TEMPLATE/plugin.md)，将插件信息填入，并附带 `Plugin` 标签，我们会在空闲时对插件进行审核

在审核通过后，我们会将分支合并

## 真寻插件商店

修改项目下的 `plugins.json` 文件添加你的插件，例如
```json
"github订阅": {
        "module": "github_sub",
        "module_path": "github_sub",
        "description": "订阅github用户或仓库",
        "usage：\n    github新Comment，PR，Issue等提醒\n指令：\n    添加github ['用户'/'仓库'] [用户名/{owner/repo}]\n    删除github [用户名/{owner/repo}]\n    查看github\n    示例：添加github订阅 用户 HibiKier\n    示例：添加gb订阅 仓库 HibiKier/zhenxun_bot\n    示例：添加github 用户 HibiKier\n    示例：删除gb订阅 HibiKier",
        "author": "xuanerwa",
        "version": "0.6",
        "plugin_type": "NORMAL",
        "is_dir": true,
		"github_url": "https://github.com/xuanerwa/zhenxun_github_sub"
    }
```




插件如果需要安装依赖可以写在`requirements.txt`里，真寻安装插件时将自动安装里面的依赖

