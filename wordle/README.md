# nonebot-plugin-wordle

适用于真寻 [Nonebot2](https://github.com/nonebot/nonebot2) 的 wordle 猜单词插件


### 使用

```
@真寻 猜单词

```

绿色块代表此单词中有此字母且位置正确

黄色块代表此单词中有此字母，但该字母所处位置不对

灰色块代表此单词中没有此字母

猜出单词或用光次数则游戏结束

可发送“结束”结束游戏；可发送“提示”查看提示

可使用 -l / --length 指定单词长度，默认为 5

可使用 -d / --dic 指定词典，默认为 CET4

支持的词典：GRE、考研、GMAT、专四、TOFEL、SAT、专八、IELTS、CET4、CET6


或使用 `wordle` 指令：

```
wordle [-l --length <length>] [-d --dic <dic>] [--hint] [--stop] [word]
```



### 特别感谢
作者Meetwq
- [SAGIRI-kawaii/sagiri-bot](https://github.com/SAGIRI-kawaii/sagiri-bot) 基于Graia Ariadne和Mirai的QQ机器人 SAGIRI-BOT
