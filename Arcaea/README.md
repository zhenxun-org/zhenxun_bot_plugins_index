# Arcaea

> 基于 Arcaea [https://github.com/Yuri-YuzuChaN/Arcaea](https://github.com/Yuri-YuzuChaN/Arcaea)
> 在其基础上对真寻进行适配

**由于不可描述的原因，本地查分器暂时不可用，请耐心等待**

## 使用方法

1. 将该项目放在zhenxun插件目录 `plugins` 下，或者clone本项目 `git clone https://github.com/AkashiCoin/nonebot_plugins_zhenxun_bot/Arcaea`
2. pip以下依赖：`websockets`，`brotli`
3. 在数据库`./arcaea.db`中`LOGIN`表添加查分账号密码以及绑定ID（随意数字），`IS_FULL` 字段请根据查分账号的好友数量填写，如果已经到达10个上限请输入`1`，否则为`0`

**注意：查分账号需要自行注册，查询自己也需要查分账号添加自己为好友**

## 另外

1. 后续游戏版本更新需自行修改数据库文件`arcsong.db`添加曲目，`img/song`的曲目图片
2. 每次添加完好友必须使用一次`arcup`指令

## 指令

| 指令              | 功能     | 可选参数              | 说明                            |
| :---------------- | :------- | :-------------------- | :------------------------------ |
| arcinfo           | 查询B30  |  无                   | 使用est查分器查询自己的B30成绩                |
| arcre             | 查询最近  | 无                   | 使用本地查分器查询最近一次游玩成绩              |
|                   |          | [:]                  | 使用est查分器查询最近一次游玩成绩，全角半角都可以            |
|                   |          | [:] [@]              | 冒号结尾@好友使用est查询最近一次游玩成绩            |
|                   |          | [:] [arcid]          | 冒号结尾带好友码使用est查询最近一次游玩成绩            |
| arcup             | 账号绑定  | 无                   | 查询用账号添加完好友，使用该指令绑定查询账号，添加成功即可使用`arcre`指令|
| arcbind           | 绑定     | [arcid] [arcname]     | 绑定用户                        |
| arcun             | 解绑     | 无                    | 解除绑定                        |
| arcrd             | 随机曲目  | [定数] [难度]         | 随机一首该定数的曲目，例如：`arcrd 10.8`，`arcrd 10+`，`arcrd 9+ byd` |

## 更新

**2022/3/5**

1. 对真寻beta1进行了适配