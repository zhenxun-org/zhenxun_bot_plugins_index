## MockingBird 语音(真寻适配版)

此项目灵感来源于 [Diaosi1111/nonebot_mockingbird_plugin](https://github.com/Diaosi1111/nonebot_mockingbird_plugin)

### 食用方法

**需要使用python3.9**

> 如果你的python版本为3.8则不可以食用

1. 首先使用命令安装mockingbirdonlyforuse:

``` 
pip install mockingbirdonlyforuse
```

**如有报错请为正常现象**

2. 再使用requirements.txt文件，安装依赖:

```shell
pip install -r requirements.txt # 利用requirements.txt文件安装
# 或者
pip install torch==1.10.1 torchvision==0.11.2 torchaudio==0.10.1 numpy==1.21 # 使用命令直接安装
```

ps: 其实是我踩过的坑。。`pytorch`的版本必须和`numpy`的版本严格相关，否则无法运行。。

安装完成以后，@bot输入想要bot说的话，bot就可以进行复读啦！

在配置文件`config.yaml`中提供语音模型修改详细见更新

### 更新

**2022/04/09**

1. 真寻beta2适配
1. 提供azusa语音模型