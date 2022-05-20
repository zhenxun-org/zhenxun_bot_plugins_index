# nonebot-plugin-caiyunai

适用于真寻 [Nonebot2](https://github.com/nonebot/nonebot2) 的彩云小梦AI续写插件

### 配置

需要在 `.env.xxx` 文件中添加彩云小梦apikey：

```
caiyunai_apikey=xxx

```

apikey获取：

前往 http://if.caiyunai.com/dream 注册彩云小梦用户；

注册完成后，F12打开开发者工具；

在控制台中输入 `alert(localStorage.cy_dream_user)` ，弹出窗口中的 uid 即为 apikey；

或者进行一次续写，在 Network 中查看 novel_ai 请求，Payload 中的 uid 项即为 apikey。


### 使用

#### 触发方式：

```
@真寻 续写/彩云小梦 xxx

```


### 特别感谢
作者Meetwq
- [assassingyk/novel_ai_kai](https://github.com/assassingyk/novel_ai_kai) 适用hoshino的基于彩云小梦的小说AI续写插件
