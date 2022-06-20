#!/usr/bin/python
# -*- coding:utf-8 -*-
import random
from .bread_handle import Action
from .bread_operate import Rob, Eat, Buy
from .config import MIN, MAX, CD
from functools import wraps


rob_events = []
eat_events = []
buy_events = []
give_events = []


def probability(value, action: Action, *, priority: int = 5):
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if random.random() < value:
                return func(*args, **kwargs)
            else:
                return None
        event_list = (buy_events, eat_events, rob_events, give_events)[action.value]
        event_list.append((priority, inner))
        return inner
    return wrapper


@probability(0.09, Action.ROB, priority=5)
def rob_event_fail(event: Rob):
    if event.user_data.bread_num < MAX.ROB.value:
        loss_num = random.randint(0, event.user_data.bread_num)
    else:
        loss_num = random.randint(MIN.ROB.value, MAX.ROB.value)
    new_bread_num = event.bread_db.reduce_bread(event.user_id, loss_num)
    event.bread_db.update_no(event.user_id)
    append_text = f"抢面包失败啦！被{event.robbed_name}反击，你丢失{loss_num}个面包！你现在拥有{new_bread_num}个面包！"
    event.bread_db.update_cd_stamp(event.user_id, Action.ROB)
    return append_text


@probability(0.01, Action.BUY, priority=5)
def buy_event_gold_bread(event: Buy):
    buy_num = random.randint(MIN.BUY.value, MAX.BUY.value) + 20
    new_bread_num = event.bread_db.add_bread(event.user_id, buy_num)
    new_bread_no = event.bread_db.update_no(event.user_id)
    append_text = f"出现了！黄金面包！计为{buy_num}个！现在一共拥有{new_bread_num}个面包！您的面包排名为:{new_bread_no}"
    event.bread_db.update_cd_stamp(event.user_id, Action.BUY)
    return append_text


@probability(0.2, Action.BUY, priority=5)
def buy_event_poverty_relief(event: Buy):
    if event.user_data.bread_num > 10:
        return
    buy_num = random.randint(MIN.BUY.value, MAX.BUY.value) + 10
    new_bread_num = event.bread_db.add_bread(event.user_id, buy_num)
    new_bread_no = event.bread_db.update_no(event.user_id)
    append_text = f"面包店看你面包太少了，送了你{buy_num}个！现在一共拥有{new_bread_num}个面包！您的面包排名为:{new_bread_no}"
    event.bread_db.update_cd_stamp(event.user_id, Action.BUY)
    return append_text


@probability(0.8, Action.BUY, priority=5)
def buy_event_too_much(event: Buy):
    if event.user_data.bread_num < 90:
        return
    append_text = f"你面包太多啦！不卖给你了，快吃！现在一共拥有{event.user_data.bread_num}个面包！您的面包排名为:{event.user_data.no}"
    return append_text


@probability(0.4, Action.EAT, priority=5)
def eat_event_not_enough(event: Eat):
    if event.user_data.bread_num < MAX.EAT.value:
        eat_num = random.randint(MIN.EAT.value, event.user_data.bread_num)
    else:
        eat_num = random.randint(MIN.EAT.value, MAX.EAT.value)
    now_bread = event.bread_db.reduce_bread(event.user_id, eat_num)
    eaten_bread = event.bread_db.add_bread(event.user_id, eat_num, "BREAD_EATEN")

    if eat_num < 3:
        append_text = f"成功吃掉了{eat_num}个面包w！还是好饿，还可以继续吃！"
    else:
        append_text = f"成功吃掉了{eat_num}个面包w！现在你还剩{now_bread}个面包w！您目前的等级为Lv.{eaten_bread // 10}"
        event.bread_db.update_cd_stamp(event.user_id, Action.EAT)
    event.bread_db.update_no(event.user_id)
    return append_text














