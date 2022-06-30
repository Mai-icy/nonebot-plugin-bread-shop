#!/usr/bin/python
# -*- coding:utf-8 -*-
from enum import Enum

# 自定义物品，改掉默认的”面包“
THING = "面包"

# 被禁止的群聊
BANNED_GROUPS = []


class CD(Enum):
    """操作冷却（单位：秒）"""
    BUY = 4200
    EAT = 4800
    ROB = 7000
    GIVE = 3000
    BET = 5400


class MAX(Enum):
    """操作随机值上限"""
    BUY = 10
    EAT = 7
    ROB = 7
    GIVE = 10
    BET = 10


class MIN(Enum):
    """操作随机值下限"""
    BUY = 1
    EAT = 1
    ROB = 1
    GIVE = 1
    BET = 5
