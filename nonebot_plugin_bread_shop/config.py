#!/usr/bin/python
# -*- coding:utf-8 -*-
from enum import Enum


class CD(Enum):
    BUY = 4200
    EAT = 4800
    ROB = 7000
    GIVE = 3000
    BET = 5400


class MAX(Enum):
    BUY = 10
    EAT = 7
    ROB = 7
    GIVE = 10
    BET = 10


class MIN(Enum):
    BUY = 1
    EAT = 1
    ROB = 1
    GIVE = 1
    BET = 5
