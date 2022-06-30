#!/usr/bin/python
# -*- coding:utf-8 -*-
import random
from functools import wraps

from .bread_handle import Action
from .bread_operate import RobEvent, EatEvent, BuyEvent, GiveEvent, BetEvent
from .config import MIN, MAX, THING, LEVEL_NUM

rob_events = []
eat_events = []
buy_events = []
give_events = []
bet_events = []


# 特殊事件修饰器
def probability(value, action: Action, *, priority: int = 5, group_id_list: list = None):
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if random.random() < value:
                return func(*args, **kwargs)
            else:
                return None
        setattr(inner, "priority", priority)
        setattr(inner, "group_id_list", group_id_list)
        events_lists = (buy_events, eat_events, rob_events, give_events, bet_events)
        if action == Action.ALL:
            for events in events_lists:
                events.append(inner)
        else:
            event_list = events_lists[action.value]
            event_list.append(inner)
        return inner
    return wrapper


# region 购买特殊事件
@probability(0.01, Action.BUY, priority=5)
def buy_event_gold_bread(event: BuyEvent):
    buy_num = random.randint(MIN.BUY.value, MAX.BUY.value) + 20
    new_bread_num = event.bread_db.add_bread(event.user_id, buy_num)
    new_bread_no = event.bread_db.update_no(event.user_id)
    append_text = f"出现了！黄金{THING}！计为{buy_num}个！现在一共拥有{new_bread_num}个{THING}！您的{THING}排名为:{new_bread_no}"
    event.bread_db.cd_update_stamp(event.user_id, Action.BUY)
    return append_text


@probability(0.2, Action.BUY, priority=5)
def buy_event_poverty_relief(event: BuyEvent):
    if event.user_data.bread_num > 10:
        return
    buy_num = random.randint(MIN.BUY.value, MAX.BUY.value) + 10
    new_bread_num = event.bread_db.add_bread(event.user_id, buy_num)
    new_bread_no = event.bread_db.update_no(event.user_id)
    append_text = f"{THING}店看你{THING}太少了，送了你{buy_num}个！现在一共拥有{new_bread_num}个{THING}！您的{THING}排名为:{new_bread_no}"
    event.bread_db.cd_update_stamp(event.user_id, Action.BUY)
    return append_text


@probability(0.8, Action.BUY, priority=4)
def buy_event_too_much(event: BuyEvent):
    if event.user_data.bread_num < 90:
        return
    append_text = f"你{THING}太多啦！不卖给你了，快吃！现在一共拥有{event.user_data.bread_num}个{THING}！您的{THING}排名为:{event.user_data.no}"
    event.bread_db.cd_update_stamp(event.user_id, Action.BUY)
    return append_text


@probability(0.025, Action.BUY, priority=5)
def buy_event_find_bad(event: BuyEvent):
    if event.user_data.bread_num < MAX.BUY.value:
        return
    bad_num = random.randint(MIN.BUY.value, MAX.BUY.value)
    append_text = f"你刚要去买{THING}，发现自己{bad_num}个{THING}坏掉了！好难过，不想买啦！"
    event.bread_db.reduce_bread(event.user_id, bad_num)
    event.bread_db.cd_update_stamp(event.user_id, Action.BUY)
    return append_text
# endregion


# region 吃特殊事件
@probability(0.2, Action.EAT, priority=5)
def eat_event_too_much_bread(event: EatEvent):
    if event.user_data.bread_num < 90:
        return
    txt = event.normal_event()
    txt += f"\n你{THING}太多啦，我允许你再吃一次吧！"
    event.bread_db.cd_refresh(event.user_id, Action.EAT)
    return txt


@probability(0.2, Action.EAT, priority=5)
def eat_event_not_enough(event: EatEvent):
    eat_num = random.randint(MIN.EAT.value, min(MIN.EAT.value + 3, event.user_data.bread_num))
    event.bread_db.reduce_bread(event.user_id, eat_num)
    event.bread_db.add_bread(event.user_id, eat_num, Action.EAT)
    append_text = f"成功吃掉了{eat_num}个{THING}w！还是好饿，还可以继续吃！"
    event.bread_db.update_no(event.user_id)
    return append_text


@probability(0.1, Action.EAT, priority=5)
def eat_event_much(event: EatEvent):
    if event.user_data.bread_num <= MAX.EAT.value:
        return
    eat_num = random.randint(MAX.EAT.value, min(MAX.EAT.value * 2, event.user_data.bread_num))
    event.bread_db.reduce_bread(event.user_id, eat_num)
    event.bread_db.add_bread(event.user_id, eat_num, Action.EAT)
    append_text = f"成功吃掉了{eat_num}个{THING}w！吃太多啦，撑死了，下次吃多等30分钟！"
    event.bread_db.update_no(event.user_id)
    event.bread_db.cd_ban_action(event.user_id, Action.EAT, 1800)
    return append_text


@probability(0.07, Action.EAT, priority=5)
def eat_event_steal(event: EatEvent):
    eat_num = random.randint(MIN.EAT.value, min(MAX.EAT.value, event.user_data.bread_num))
    event.bread_db.reduce_bread(event.user_id, eat_num)
    append_text = f"你吃{THING}被我发现了！我好饿，我帮你吃吧！吃了你{eat_num}个{THING}！"
    event.bread_db.update_no(event.user_id)
    return append_text


@probability(0.02, Action.EAT, priority=5)
def eat_event_good(event: EatEvent):
    eat_num = random.randint(MIN.EAT.value, min(MAX.EAT.value, event.user_data.bread_num))
    event.bread_db.reduce_bread(event.user_id, eat_num)
    event.bread_db.add_bread(event.user_id, eat_num, Action.EAT)
    append_text = f"成功吃掉了{eat_num}个{THING}w！有个{THING}超好吃！让你心情舒爽！所有操作刷新！"
    event.bread_db.update_no(event.user_id)

    event.bread_db.cd_refresh(event.user_id, Action.ALL)

    return append_text


@probability(0.015, Action.EAT, priority=5)
def eat_event_bad(event: EatEvent):
    if event.user_data.bread_eaten <= 10:
        return
    append_text = f"{THING}坏啦！吃了一个坏{THING}！难受死了，等级减1。"
    event.bread_db.reduce_bread(event.user_id, 1)
    event.bread_db.reduce_bread(event.user_id, LEVEL_NUM, Action.EAT)
    event.bread_db.update_no(event.user_id)
    return append_text


@probability(0.03, Action.EAT, priority=5)
def eat_event_rob(event: EatEvent):
    eat_num = random.randint(MIN.EAT.value, min(MAX.EAT.value, event.user_data.bread_num))
    event.bread_db.reduce_bread(event.user_id, eat_num)
    event.bread_db.add_bread(event.user_id, eat_num, Action.EAT)
    event.bread_db.update_no(event.user_id)

    append_text = f"成功吃掉了{eat_num}个{THING}w！让你充满了力量！刷新抢的冷却！"
    event.bread_db.cd_refresh(event.user_id, Action.ROB)
    event.bread_db.cd_update_stamp(event.user_id, Action.EAT)
    return append_text


@probability(0.025, Action.EAT, priority=5)
def eat_event_find_bad(event: BuyEvent):
    if event.user_data.bread_num < MAX.EAT.value:
        return
    bad_num = random.randint(MIN.EAT.value, MAX.EAT.value)
    append_text = f"你刚想去吃{THING}，发现自己{bad_num}个{THING}坏掉了！好难过，不想吃啦！"
    event.bread_db.reduce_bread(event.user_id, bad_num)
    event.bread_db.cd_update_stamp(event.user_id, Action.EAT)
    return append_text
# endregion


# region 抢特殊事件
@probability(0.09, Action.ROB, priority=5)
def rob_event_fail(event: RobEvent):
    loss_num = random.randint(0, min(MAX.ROB.value, event.user_data.bread_num))
    new_bread_num = event.bread_db.reduce_bread(event.user_id, loss_num)
    event.bread_db.update_no(event.user_id)
    append_text = f"抢{THING}失败啦！被{event.robbed_name}反击，你丢失{loss_num}个{THING}！你现在拥有{new_bread_num}个{THING}！"
    event.bread_db.cd_update_stamp(event.user_id, Action.ROB)
    return append_text


@probability(0.07, Action.ROB, priority=5)
def rob_event_police(event: RobEvent):
    append_text = f"你抢{THING}被警察抓住了！你真的太坏了！下次抢{THING}时间多等40min！"
    event.bread_db.cd_ban_action(event.user_id, Action.ROB, 2400)
    return append_text


@probability(0.1, Action.ROB, priority=5)
def rob_event_addiction(event: BetEvent):
    append_text = event.normal_event()
    append_text += "有点上瘾，你想再抢一次！"
    event.bread_db.cd_refresh(event.user_id, Action.ROB)
    return append_text


@probability(0.05, Action.ROB, priority=5)
def rob_event_police2(event: RobEvent):
    loss_num = random.randint(0, min(MAX.ROB.value, event.user_data.bread_num))
    append_text = f"你抢{THING}被我抓住了！你真的太坏了！我要罚你{loss_num}个{THING}！"
    event.bread_db.reduce_bread(event.user_id, loss_num)
    event.bread_db.update_no(event.user_id)
    event.bread_db.cd_update_stamp(event.user_id, Action.ROB)
    return append_text


@probability(0.05, Action.ROB, priority=5)
def rob_event_hungry(event: RobEvent):
    append_text = f"太饿了！什么都没抢到，但是你想吃东西！吃{THING}冷却刷新！"
    event.bread_db.cd_refresh(event.user_id, Action.EAT)
    event.bread_db.cd_update_stamp(event.user_id, Action.ROB)
    return append_text
# endregion


# region 送特殊事件
@probability(0.1, Action.GIVE, priority=5)
def give_event_commission(event: GiveEvent):
    if event.user_data.bread_num <= MAX.GIVE.value * 2:
        return
    give_num = random.randint(MAX.GIVE.value, min(MAX.GIVE.value * 2, event.user_data.bread_num))
    give_bot = give_num // 2
    user_num = event.bread_db.reduce_bread(event.user_id, give_num)
    event.bread_db.add_bread(event.given_id, give_num - give_bot)
    append_text = f"哇！这么多{THING}，你送了{give_num - give_bot}个给{event.given_name}！" \
                  f"再给我{give_bot}吧嘿嘿！你现在有{user_num}个{THING}！"
    event.bread_db.update_no(event.user_id)
    event.bread_db.update_no(event.given_id)
    event.bread_db.cd_update_stamp(event.user_id, Action.GIVE)
    return append_text


@probability(0.1, Action.GIVE, priority=5)
def give_event_lossless(event: GiveEvent):
    give_num = random.randint(MIN.GIVE.value, min(MAX.GIVE.value, event.user_data.bread_num))
    event.bread_db.add_bread(event.given_id, give_num)
    append_text = f"看在你如此善良的份上，我帮你送吧！送了{give_num}给{event.given_name}，你不损失{THING}！"
    event.bread_db.update_no(event.given_id)
    event.bread_db.cd_update_stamp(event.user_id, Action.GIVE)
    return append_text


@probability(0.06, Action.GIVE, priority=5)
def give_event_lossless2(event: GiveEvent):
    give_num = random.randint(MIN.GIVE.value, min(MAX.GIVE.value, event.user_data.bread_num))
    give_num2 = random.randint(MIN.GIVE.value, min(MAX.GIVE.value, event.user_data.bread_num))
    event.bread_db.add_bread(event.given_id, give_num)
    event.bread_db.add_bread(event.user_id, give_num2)
    append_text = f"大好人！我帮你送吧！送了{give_num}给{event.given_name}，我再送你{give_num2}个！"
    event.bread_db.update_no(event.given_id)
    event.bread_db.cd_update_stamp(event.user_id, Action.GIVE)
    return append_text
# endregion


# region 猜拳特殊事件
@probability(0.1, Action.BET, priority=5)
def bet_event_addiction(event: BetEvent):
    append_text = event.normal_event()
    append_text += "有点上瘾，你想再来一把！"
    event.bread_db.cd_refresh(event.user_id, Action.BET)
    return append_text


@probability(0.07, Action.BET, priority=5)
def bet_event_police(event: BetEvent):
    append_text = f"你赌{THING}被警察抓住了！你不赌，我不赌，和谐幸福跟我走！下次赌{THING}时间多等40min！"
    event.bread_db.cd_ban_action(event.user_id, Action.BET, 2400)
    return append_text


@probability(0.2, Action.BET, priority=4)
def bet_event_big(event: RobEvent):
    if event.user_data.bread_num < 70:
        return
    ori_num = event.user_data.bread_num
    append_text = f"你{THING}这么多！多来了几把，"
    for _ in range(4):
        event.normal_event()
    now_num = event.user_data.bread_num
    delta_num = abs(ori_num - now_num)
    event.bread_db.cd_update_stamp(event.user_id, Action.BET)
    if ori_num > now_num:
        return append_text + f"你一共损失了{delta_num}个面包！"
    else:
        return append_text + f"你一共获得了{delta_num}个面包！"


@probability(0.04, Action.BET, priority=5)
def bet_event_cheat(event: RobEvent):
    loss_num = random.randint(MIN.ROB.value, min(event.user_data.bread_num, MAX.BET.value))
    append_text = f"我出三只手！石头剪刀布！你输啦！给我{loss_num}个{THING}！"
    event.bread_db.reduce_bread(event.user_id, loss_num)
    event.bread_db.update_no(event.user_id)
    event.bread_db.cd_update_stamp(event.user_id, Action.BET)
    return append_text
# endregion
