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

如果您愿意，可以参考下方的 `表格样式` 修改 `README.md`，并根据 `发起 Pull Request` 发布修改

## 表格样式

```markdown
| [插件名](仓库地址) | [@作者名](作者 GitHub 地址) | 插件备注 |
```

如果您的插件发布了 Release，也可将 Release 地址写入，格式如下

```markdown
| [插件名](仓库地址) [点击下载](https://ghproxy.com/GitHub release 下载地址) | [@作者名](作者 GitHub 地址) | 插件备注 |
```

例如下面的成分姬插件

```markdown
| [成分姬](https://github.com/yajiwa/zhenxun_plugin_ddcheck)  [点击下载](https://ghproxy.com/https://github.com/yajiwa/zhenxun_plugin_ddcheck/releases/download/v0.2/zhenxun_plugin_ddcheck.zip) | [@yajiwa](https://github.com/yajiwa) | 查询B站关注列表的VTuber成分，并以图片形式发出 |
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

## 联动真寻插件仓库

需要有GitHub_Release的下载链接

### 压缩文件夹

压缩文件的时候不要压缩插件文件夹，直接选择插件内的`.py,requirements.txt`等文件或文件夹进行压缩

### 依赖

插件如果需要安装依赖可以写在`requirements.txt`里，真寻安装插件时将自动安装里面的依赖

