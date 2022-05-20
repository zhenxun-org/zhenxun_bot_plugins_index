# ELF_RSS

这是一个以 Python 编写的 QQ 机器人插件，用于订阅 RSS 并实时以 QQ消息推送。

此插件搬运自[ELF_RSS](https://github.com/Quan666/ELF_RSS)，对真寻进行了适配。

---

当然也有很多插件能够做到订阅 RSS ，但不同的是，大多数都需要在服务器上修改相应配置才能添加订阅，而该插件只需要发送QQ消息给机器人就能动态添加订阅。

对于订阅，支持QQ、QQ群、QQ频道的单个、多个订阅。

每个订阅的个性化设置丰富，能够应付多种场景。

本项目所需依赖较多，可以使用 `pip install -r requirements.txt` 来进行安装

## 功能介绍

* 发送QQ消息来动态增、删、查、改 RSS 订阅
* 订阅内容翻译（使用谷歌机翻，可设置为百度翻译）
* 个性化订阅设置（更新频率、翻译、仅标题、仅图片等）
* 多平台支持
* 图片压缩后发送
* 种子下载并上传到群文件
* 消息支持根据链接、标题、图片去重
* 可设置只发送限定数量的图片，防止刷屏
* 可设置从正文中要移除的指定内容，支持正则

## 文档目录

> 注意：推荐 Python 3.8.3+ 版本 
>
> * [使用教程](docs/2.0%20使用教程.md)
> * [使用教程 旧版](docs/1.0%20使用教程.md)
> * [常见问题](docs/常见问题.md)
> * [更新日志](docs/更新日志.md)

## TODO

* [x] 1. 订阅信息保护，不在群组中输出订阅QQ、群组
* [x] 2. 更为强大的检查更新时间设置
* [x] 3. RSS 源中 torrent 自动下载并上传至订阅群（适合番剧订阅）
* [ ] 4. 暂停检查订阅更新
* [ ] 5. 模糊匹配订阅名
* [ ] 6. 性能优化，全部替换为异步操作

## 感谢以下项目或服务

不分先后

* [RSSHub](https://github.com/DIYgod/RSSHub)
* [Nonebot](https://github.com/nonebot/nonebot2)
* [酷Q（R. I. P）](https://cqp.cc/)
* [coolq-http-api](https://github.com/richardchien/coolq-http-api)
* [go-cqhttp](https://github.com/Mrs4s/go-cqhttp)
## 项目源地址

https://github.com/Quan666/ELF_RSS