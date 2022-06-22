# nonebot-plugin-bread-shop
<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/Mai-icy/nonebot-plugin-bread-shop.svg" alt="license">
</a><img src="https://img.shields.io/badge/python-3.7+-blue.svg" alt="python">
<a href="https://www.oscs1024.com/project/oscs/Mai-icy/nonebot-plugin-bread-shop?ref=badge_small" alt="OSCS Status"><img src="https://www.oscs1024.com/platform/badge/Mai-icy/nonebot-plugin-bread-shop.svg?size=small"/></a>

## ⚠️警告须知！

本插件不适宜用于群人员较多的群，经过测试，本功能具有极大上瘾性，容易造成bot刷屏，影响正常聊天！

## 📄介绍

面包小游戏，用户可以通过“买”，“吃”，“抢”，“送”，”猜拳“操作来获取面包和使用面包。

将会记录所有用户的面包数据进行排行

所有的操作都可能产生特殊面包事件哦！

一起来买面包吧！

## 🤔使用

| 指令 | 说明 | 其它形式 |
|:-----:|:----:|:----:|
| 买面包 | 购买随机数量面包 |buy，🍞|
| 啃面包 | 吃随机数量面包 |eat，🍞🍞，吃面包|
| 抢面包 + @指定用户 | 抢指定用户随机数量面包 |rob，🍞🍞🍞|
| 送面包 + @指定用户 | 送指定用户随机数量面包 |give，送|
| 查看面包 + @指定用户 | 查看指定用户的面包数据 |偷看面包，查看面包，check|
| 赌面包 + “石头剪刀布” | 和bot进行猜拳赌随机数量面包 |bet，面包猜拳|
| 面包排行 | 发送本群排行榜top5 |breadtop，面包排名|

## 🍞自定义配置

在**config.py**的枚举类中可以设置所有随机操作的最大值和最小值以及操作冷却。

在**bread_event.py**中可以编写特殊事件

特殊事件模板：

```python
@probability(概率, Action.操作, priority=优先级)
def 函数名(event: 操作):
    # event.user_data 可以查看操作的用户的面包数据
    # event.user_id   可以获取操作的用户的id（qq）
    # event.user_id   可以获取操作的用户的id（qq）
    # event.bread_db.reduce_bread(event.user_id, eat_num) 减少用户面包数量
    # event.bread_db.reduce_bread(event.user_id, eat_num) 增加用户面包数量
    # event.bread_db.add_bread(event.user_id, eat_num, "BREAD_EATEN")  增加用户面包食用量
    # event.bread_db.update_no(event.user_id)  更新用户排名
    # event.bread_db.ban_user_action(event.user_id, Action.EAT, 1800) 禁止用户操作
    # event.bread_db.cd_refresh(event.user_id, Action.EAT)        刷新用户CD
    # event.bread_db.update_cd_stamp(event.user_id, Action.GIVE)  重置用户CD
    # 等等见源码
    return append_text  # 返回回答，由bot发送
```

特殊事件示例：

```python
@probability(0.1, Action.EAT, priority=5)
def eat_event_much(event: Eat):
    if event.user_data.bread_num <= MAX.EAT.value:
        return
    eat_num = random.randint(MAX.EAT.value, min(MAX.EAT.value * 2, event.user_data.bread_num))
    event.bread_db.reduce_bread(event.user_id, eat_num)
    event.bread_db.add_bread(event.user_id, eat_num, "BREAD_EATEN")
    append_text = f"成功吃掉了{eat_num}个面包w！吃太多啦，撑死了，下次吃多等30分钟！"
    event.bread_db.update_no(event.user_id)
    event.bread_db.ban_user_action(event.user_id, Action.EAT, 1800)
    return append_text
```

