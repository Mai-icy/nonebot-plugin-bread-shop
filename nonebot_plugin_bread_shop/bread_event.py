#!/usr/bin/python
# -*- coding:utf-8 -*-
import random
from .bread_handle import Action
from .bread_operate import Rob, Eat, Buy, Give, Bet
from .config import MIN, MAX, CD
from functools import wraps


rob_events = []
eat_events = []
buy_events = []
give_events = []
bet_events = []


def probability(value, action: Action, *, priority: int = 5):
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if random.random() < value:
                return func(*args, **kwargs)
            else:
                return None
        event_list = (buy_events, eat_events, rob_events, give_events, bet_events)[action.value]
        event_list.append((priority, inner))
        return inner
    return wrapper


@probability(0.07, Action.ROB, priority=5)
def bet_event_police(event: Rob):
    append_text = f"你抢面包被警察抓住了！你真的太坏了！下次抢面包时间多等40min！"
    event.bread_db.cd_ban_action(event.user_id, Action.BET, 2400)
    return append_text


@probability(0.09, Action.ROB, priority=5)
def rob_event_fail(event: Rob):
    loss_num = random.randint(0, min(MAX.ROB.value, event.user_data.bread_num))
    new_bread_num = event.bread_db.reduce_bread(event.user_id, loss_num)
    event.bread_db.update_no(event.user_id)
    append_text = f"抢面包失败啦！被{event.robbed_name}反击，你丢失{loss_num}个面包！你现在拥有{new_bread_num}个面包！"
    event.bread_db.cd_update_stamp(event.user_id, Action.ROB)
    return append_text


@probability(0.01, Action.BUY, priority=5)
def buy_event_gold_bread(event: Buy):
    buy_num = random.randint(MIN.BUY.value, MAX.BUY.value) + 20
    new_bread_num = event.bread_db.add_bread(event.user_id, buy_num)
    new_bread_no = event.bread_db.update_no(event.user_id)
    append_text = f"出现了！黄金面包！计为{buy_num}个！现在一共拥有{new_bread_num}个面包！您的面包排名为:{new_bread_no}"
    event.bread_db.cd_update_stamp(event.user_id, Action.BUY)
    return append_text


@probability(0.2, Action.BUY, priority=5)
def buy_event_poverty_relief(event: Buy):
    if event.user_data.bread_num > 10:
        return
    buy_num = random.randint(MIN.BUY.value, MAX.BUY.value) + 10
    new_bread_num = event.bread_db.add_bread(event.user_id, buy_num)
    new_bread_no = event.bread_db.update_no(event.user_id)
    append_text = f"面包店看你面包太少了，送了你{buy_num}个！现在一共拥有{new_bread_num}个面包！您的面包排名为:{new_bread_no}"
    event.bread_db.cd_update_stamp(event.user_id, Action.BUY)
    return append_text


@probability(0.8, Action.BUY, priority=4)
def buy_event_too_much(event: Buy):
    if event.user_data.bread_num < 90:
        return
    append_text = f"你面包太多啦！不卖给你了，快吃！现在一共拥有{event.user_data.bread_num}个面包！您的面包排名为:{event.user_data.no}"
    event.bread_db.cd_update_stamp(event.user_id, Action.BUY)
    return append_text


@probability(0.2, Action.EAT, priority=5)
def eat_event_not_enough(event: Eat):
    eat_num = random.randint(MIN.EAT.value, min(MIN.EAT.value + 3, event.user_data.bread_num))
    event.bread_db.reduce_bread(event.user_id, eat_num)
    event.bread_db.add_bread(event.user_id, eat_num, Action.EAT)
    append_text = f"成功吃掉了{eat_num}个面包w！还是好饿，还可以继续吃！"
    event.bread_db.update_no(event.user_id)
    return append_text


@probability(0.1, Action.EAT, priority=5)
def eat_event_much(event: Eat):
    if event.user_data.bread_num <= MAX.EAT.value:
        return
    eat_num = random.randint(MAX.EAT.value, min(MAX.EAT.value * 2, event.user_data.bread_num))
    event.bread_db.reduce_bread(event.user_id, eat_num)
    event.bread_db.add_bread(event.user_id, eat_num, Action.EAT)
    append_text = f"成功吃掉了{eat_num}个面包w！吃太多啦，撑死了，下次吃多等30分钟！"
    event.bread_db.update_no(event.user_id)
    event.bread_db.cd_ban_action(event.user_id, Action.EAT, 1800)
    return append_text


@probability(0.02, Action.EAT, priority=5)
def eat_event_much(event: Eat):
    eat_num = random.randint(MIN.EAT.value, min(MAX.EAT.value, event.user_data.bread_num))
    event.bread_db.reduce_bread(event.user_id, eat_num)
    event.bread_db.add_bread(event.user_id, eat_num, Action.EAT)
    append_text = f"成功吃掉了{eat_num}个面包w！有个面包超好吃！让你心情舒爽！所有操作刷新！"
    event.bread_db.update_no(event.user_id)

    event.bread_db.cd_refresh(event.user_id, Action.EAT)
    event.bread_db.cd_refresh(event.user_id, Action.BET)
    event.bread_db.cd_refresh(event.user_id, Action.BUY)
    event.bread_db.cd_refresh(event.user_id, Action.ROB)
    event.bread_db.cd_refresh(event.user_id, Action.GIVE)

    return append_text


@probability(0.015, Action.EAT, priority=5)
def eat_event_bad(event: Eat):
    if event.user_data.bread_eaten <= 10:
        return
    append_text = f"面包坏啦！吃了一个坏面包！难受死了，等级减1。"
    event.bread_db.reduce_bread(event.user_id, 1)
    event.bread_db.reduce_bread(event.user_id, 10, Action.EAT)
    event.bread_db.update_no(event.user_id)
    return append_text


@probability(0.1, Action.GIVE, priority=5)
def give_event_commission(event: Give):
    if event.user_data.bread_num <= MAX.GIVE.value * 2:
        return
    give_num = random.randint(MAX.GIVE.value, min(MAX.GIVE.value * 2, event.user_data.bread_num))
    give_bot = give_num // 2
    user_num = event.bread_db.reduce_bread(event.user_id, give_num)
    event.bread_db.add_bread(event.given_id, give_num - give_bot)
    append_text = f"哇！这么多面包，你送了{give_num - give_bot}个给{event.given_name}！" \
                  f"再给我{give_bot}吧嘿嘿！你现在有{user_num}个面包！"
    event.bread_db.update_no(event.user_id)
    event.bread_db.update_no(event.given_id)
    event.bread_db.cd_update_stamp(event.user_id, Action.GIVE)
    return append_text


@probability(0.07, Action.BET, priority=5)
def bet_event_police(event: Bet):
    append_text = f"你赌面包被警察抓住了！你不赌，我不赌，和谐幸福跟我走！下次赌面包时间多等40min！"
    event.bread_db.cd_ban_action(event.user_id, Action.BET, 2400)
    return append_text










