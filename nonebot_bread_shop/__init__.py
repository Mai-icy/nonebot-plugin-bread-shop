#!/usr/bin/python
# -*- coding:utf-8 -*-
import random
import time
import re

from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Bot, Event, Message

from .bread_handle import BreadDataManage, Action
from .bread_operate import *
from .bread_event import rob_events, buy_events, eat_events


bread_buy = on_command("bread_buy", aliases={"买面包", "buy", "🍞"}, priority=5)
bread_eat = on_command("bread_eat", aliases={"吃面包", "啃面包", "eat", "🍞🍞"}, priority=5)
bread_rob = on_command("bread_rob", aliases={"抢面包", "rob", "🍞🍞🍞"}, priority=5)
bread_give = on_command("bread_give", aliases={"送面包", "give", "送"}, priority=5)
bread_top = on_command("bread_top", aliases={"面包排行", "breadtop"}, priority=5)


EAT_EVENT = Eat()
BUY_EVENT = Buy()
ROB_EVENT = Rob()
GIVE_EVENT = Give()


ROB_EVENT.add_events(rob_events)


@bread_buy.handle()
async def _(event: Event, bot: Bot):
    user_qq = event.get_user_id()
    msg_at = Message(f"[CQ:at,qq={user_qq}]")

    group_id = await get_group_id(event.get_session_id())

    wait_time = cd_wait_time(group_id, user_qq, Action.BUY)
    if wait_time:
        data = BreadDataManage(group_id).get_bread_data(user_qq)
        msg_txt = f"您还得等待{wait_time // 60}分钟才能买面包w，现在一共拥有{data.bread_num}个面包！您的面包排名为:{data.no}"
    else:
        BUY_EVENT.set_group_id(group_id)
        BUY_EVENT.set_user_id(user_qq)
        msg_txt = BUY_EVENT.execute()

    res_msg = msg_at + Message(msg_txt)
    await bot.send(event=event, message=res_msg)
    # await bread_buy.finish(event=ad, message="购买成功/test")


@bread_eat.handle()
async def _(event: Event, bot: Bot):
    user_qq = event.get_user_id()
    msg_at = Message(f"[CQ:at,qq={user_qq}]")

    group_id = await get_group_id(event.get_session_id())

    wait_time = cd_wait_time(group_id, user_qq, Action.EAT)
    if wait_time:
        data = BreadDataManage(group_id).get_bread_data(user_qq)
        msg_txt = f"您还得等待{wait_time // 60}分钟才能吃面包w，现在你的等级是Lv.{data.bread_eaten // 10}！您的面包排名为:{data.no}"
    else:
        EAT_EVENT.set_group_id(group_id)
        EAT_EVENT.set_user_id(user_qq)
        msg_txt = EAT_EVENT.execute()

    res_msg = msg_at + Message(msg_txt)
    await bot.send(event=event, message=res_msg)


@bread_rob.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    user_qq = event.get_user_id()
    msg_at = Message(f"[CQ:at,qq={user_qq}]")

    group_id = await get_group_id(event.get_session_id())

    robbed_qq = None
    for arg in args:
        if arg.type == "at":
            robbed_qq = arg.data.get("qq", "")
    if not robbed_qq:
        return
    robbed_name = await get_nickname(bot, robbed_qq, group_id)

    wait_time = cd_wait_time(group_id, user_qq, Action.ROB)
    if wait_time:
        msg_txt = f"您还得等待{wait_time // 60}分钟才能抢面包w"
    else:
        ROB_EVENT.set_group_id(group_id)
        ROB_EVENT.set_user_id(user_qq)
        ROB_EVENT.set_robbed_id(robbed_qq, robbed_name)
        msg_txt = ROB_EVENT.execute()

    res_msg = msg_at + msg_txt
    await bot.send(event=event, message=res_msg)


@bread_give.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    user_qq = event.get_user_id()
    msg_at = Message(f"[CQ:at,qq={user_qq}]")

    group_id = await get_group_id(event.get_session_id())

    robbed_qq = None
    for arg in args:
        if arg.type == "at":
            robbed_qq = arg.data.get("qq", "")
    if not robbed_qq:
        return
    robbed_name = await get_nickname(bot, robbed_qq, group_id)

    wait_time = cd_wait_time(group_id, user_qq, Action.GIVE)
    if wait_time:
        msg_txt = f"您还得等待{wait_time // 60}分钟才能送面包w"
    else:
        GIVE_EVENT.set_group_id(group_id)
        GIVE_EVENT.set_user_id(user_qq)
        GIVE_EVENT.set_given_id(robbed_qq, robbed_name)
        msg_txt = GIVE_EVENT.execute()

    res_msg = msg_at + msg_txt
    await bot.send(event=event, message=res_msg)


@bread_top.handle()
async def _(bot: Bot, event: Event):
    group_id = event.get_session_id()
    res = re.findall("_(.*)_", group_id)
    group_id = res[0]
    msg = await get_group_top(bot, group_id)
    await bot.send(event=event, message=msg)


async def get_group_id(session_id):
    res = re.findall("_(.*)_", session_id)
    group_id = res[0]
    return group_id


async def get_group_top(bot: Bot, group_id) -> Message:
    group_member_list = await bot.get_group_member_list(group_id=int(group_id))
    user_id_list = {info['user_id'] for info in group_member_list}
    all_data = BreadDataManage(group_id).get_all_data()
    num = 0
    append_text = "🍞本群面包排行top5！🍞\n"
    for data in all_data:
        if int(data.user_id) in user_id_list:
            num += 1
            name = await get_nickname(bot, data.user_id, group_id)
            append_text += f"top{num} : {name} Lv.{data.bread_eaten // 10}，拥有面包{data.bread_num}个\n"
        if num == 5:
            break
    append_text += "大家继续加油w！"
    return Message(append_text)


async def get_nickname(bot: Bot, user_id, group_id=None):
    if group_id:
        info = await bot.get_group_member_info(group_id=int(group_id), user_id=int(user_id))
        other_name = info.get("card", "") or info.get("nickname", "")
        if not other_name:
            info = await bot.get_stranger_info(user_id=int(user_id))
            other_name = info.get("nickname", "")
    else:
        info = await bot.get_stranger_info(user_id=int(user_id))
        other_name = info.get("nickname", "")
    return other_name
