#!/usr/bin/python
# -*- coding:utf-8 -*-
from enum import Enum
from nonebot import get_driver
from pydantic import BaseSettings, Extra


class Config(BaseSettings, extra=Extra.ignore):
    bread_thing: str = "面包"  # 自定义物品，改掉默认的”面包“ 此为全局
    special_thing_group: dict = {}  # 分群设置物品 示例{"群号": "炸鸡"} 可设置主次物品词 示例{"群号": ["炸鸡", "面包", "蛋糕"]}
    # 注：主次物品词bot将以主物品词进行回复，次物品词只用于触发指令，主关键词为列表第一个元素，次关键词可多个

    global_bread: bool = True  # 面包默认开关
    black_bread_groups: list = []  # 黑名单
    white_bread_groups: list = []  # 白名单
    level_bread_num: int = 10  # 设置升一级所需要的面包数量（数据库不保存等级！！等级会随之而变！）

    global_database: bool = False  # 数据库是否全局，若设置了group_database，以其为优先，全局数据库文件夹名为"global"
    group_database: dict = {}  # 合并一些群的数据库 分组id将作为文件夹名 例：{"分组id":["群号1", "群号2", "群号3"]}
    # 注意：此处的分组id将生效于 special_thing_group 的设置 示例{"分组id": "炸鸡"}，原来的设置将失效
    # 特殊事件同理设置的群聊id同理请改为组id

    """操作冷却（单位：秒）"""
    cd_buy: int = 4200
    cd_eat: int = 4800
    cd_rob: int = 5000
    cd_give: int = 3000
    cd_bet: int = 5400

    """操作随机值上限"""
    max_buy: int = 9
    max_eat: int = 8
    max_rob: int = 7
    max_give: int = 10
    max_bet: int = 10

    """操作随机值下限"""
    min_buy: int = 1
    min_eat: int = 2
    min_rob: int = 2
    min_give: int = 1
    min_bet: int = 5

    """设置是否操作值都由随机值决定"""
    is_random_buy: bool = True
    is_random_eat: bool = True
    is_random_rob: bool = True
    is_random_give: bool = True
    is_random_bet: bool = True

    is_random_robbed: bool = True  # 抢面包操作不指定群员可随机抢
    is_random_given: bool = True  # 送面包操作不指定群员可随机送

    special_buy_group: dict = {}  # 示例： {"群号": bool}
    special_eat_group: dict = {}
    special_rob_group: dict = {}
    special_give_group: dict = {}
    special_bet_group: dict = {}

    """设置是否启用有效@"""
    is_at_valid: bool = False


global_config = get_driver().config
bread_config = Config(**global_config.dict())  # 载入配置


LEVEL = bread_config.level_bread_num


class CD(Enum):
    """操作冷却（单位：秒）"""
    BUY = bread_config.cd_buy
    EAT = bread_config.cd_eat
    ROB = bread_config.cd_rob
    GIVE = bread_config.cd_give
    BET = bread_config.cd_bet


class MAX(Enum):
    """操作随机值上限"""
    BUY = bread_config.max_buy
    EAT = bread_config.max_eat
    ROB = bread_config.max_rob
    GIVE = bread_config.max_give
    BET = bread_config.max_bet


class MIN(Enum):
    """操作随机值下限"""
    BUY = bread_config.min_buy
    EAT = bread_config.min_eat
    ROB = bread_config.min_rob
    GIVE = bread_config.min_give
    BET = bread_config.min_bet


def random_config():
    """设置操作数量是否由用户指定或随机"""
    from .bread_operate import BuyEvent, EatEvent, RobEvent, GiveEvent, BetEvent
    events = [BuyEvent, EatEvent, RobEvent, GiveEvent, BetEvent]
    global_settings = [bread_config.is_random_buy, bread_config.is_random_eat, bread_config.is_random_rob,
                       bread_config.is_random_give, bread_config.is_random_bet]
    special_settings = [bread_config.special_buy_group, bread_config.special_eat_group, bread_config.special_rob_group,
                        bread_config.special_give_group, bread_config.special_bet_group]

    for event_, setting in zip(events, global_settings):
        if not setting:
            event_.set_random_global(False)

    for event_, setting in zip(events, special_settings):
        if setting:
            for group_id in setting.keys():
                event_(group_id).set_random(setting[group_id])
