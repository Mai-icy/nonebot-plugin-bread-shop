#!/usr/bin/python
# -*- coding:utf-8 -*-

import re
from itertools import chain

from nonebot import get_driver
from nonebot import on_command
from nonebot.params import CommandArg, RawCommand
from nonebot.adapters.onebot.v11 import Bot, Event, Message

from .bread_handle import BreadDataManage, Action
from .bread_operate import *
from .bread_event import rob_events, buy_events, eat_events, give_events, bet_events
from .config import LEVEL, random_config, bread_config

driver = get_driver()

cmd_buy_ori = {"buy", "🍞"}
cmd_eat_ori = {"eat", "🍞🍞"}
cmd_rob_ori = {"rob", "🍞🍞🍞"}
cmd_give_ori = {"give", "送"}
cmd_bet_ori = {"bet"}

cmd_log_ori = {"logb"}
cmd_check_ori = {"check"}

cmd_top_ori = {"breadtop"}
cmd_help_ori = {"breadhelp", "helpb"}

cmd_buy = cmd_buy_ori.copy()
cmd_eat = cmd_eat_ori.copy()
cmd_rob = cmd_rob_ori.copy()
cmd_give = cmd_give_ori.copy()
cmd_bet = cmd_bet_ori.copy()

cmd_log = cmd_log_ori.copy()
cmd_check = cmd_check_ori.copy()

cmd_top = cmd_top_ori.copy()
cmd_help = cmd_help_ori.copy()

for things in chain(bread_config.special_thing_group.values(), (bread_config.bread_thing,)):
    cmd_buy.add(f"买{things}")
    cmd_eat.add(f"吃{things}")
    cmd_eat.add(f"啃{things}")
    cmd_rob.add(f"抢{things}")
    cmd_give.add(f"送{things}")
    cmd_bet.add(f"{things}猜拳")
    cmd_bet.add(f"赌{things}")

    cmd_log.add(f"{things}记录")
    cmd_check.add(f"偷看{things}")
    cmd_check.add(f"查看{things}")

    cmd_top.add(f"{things}排行")
    cmd_top.add(f"{things}排名")
    cmd_help.add(f"{things}帮助")

bread_buy = on_command("bread_buy", aliases=cmd_buy, priority=5)
bread_eat = on_command("bread_eat", aliases=cmd_eat, priority=5)
bread_rob = on_command("bread_rob", aliases=cmd_rob, priority=5)
bread_give = on_command("bread_give", aliases=cmd_give, priority=5)
bread_bet = on_command("bread_bet", aliases=cmd_bet, priority=5)

bread_log = on_command("bread_log", aliases=cmd_log, priority=5)
bread_check = on_command("bread_check", aliases=cmd_check, priority=5)
bread_top = on_command("bread_top", aliases=cmd_top, priority=5)
bread_help = on_command("bread_help", aliases=cmd_help, priority=5)

EatEvent.add_events(eat_events)
BuyEvent.add_events(buy_events)
RobEvent.add_events(rob_events)
GiveEvent.add_events(give_events)
BetEvent.add_events(bet_events)

random_config()


@bread_buy.handle()
async def _(event: Event, bot: Bot, args: Message = CommandArg(), cmd: Message = RawCommand()):
    try:
        user_qq, group_id, name, msg_at, thing = await pre_get_data(event, bot, cmd, cmd_buy_ori)
        buy_num = get_num_arg(args.extract_plain_text(), BuyEvent, group_id)
    except ArgsError as e:
        await bot.send(event=event, message=str(e))
        return
    except CommandError:
        return

    wait_time = cd_wait_time(group_id, user_qq, Action.BUY)
    if wait_time > 0:
        data = BreadDataManage(group_id).get_bread_data(user_qq)
        msg_txt = f"您还得等待{wait_time // 60}分钟才能买{thing}w，现在一共拥有{data.bread_num}个{thing}！您的{thing}排名为:{data.no}"
    elif wait_time < 0:
        msg_txt = f"你被禁止购买{thing}啦！{(abs(wait_time) + CD.BUY.value) // 60}分钟后才能购买！"
    else:
        event_ = BuyEvent(group_id)
        event_.set_user_id(user_qq)
        msg_txt = event_.execute(buy_num)

    res_msg = msg_at + Message(msg_txt)
    await bot.send(event=event, message=res_msg)


@bread_eat.handle()
async def _(event: Event, bot: Bot, args: Message = CommandArg(), cmd: Message = RawCommand()):
    try:
        user_qq, group_id, name, msg_at, thing = await pre_get_data(event, bot, cmd, cmd_eat_ori)
        eat_num = get_num_arg(args.extract_plain_text(), EatEvent, group_id)
    except ArgsError as e:
        await bot.send(event=event, message=str(e))
        return
    except CommandError:
        return

    wait_time = cd_wait_time(group_id, user_qq, Action.EAT)
    if wait_time > 0:
        data = BreadDataManage(group_id).get_bread_data(user_qq)
        msg_txt = f"您还得等待{wait_time // 60}分钟才能吃{thing}w，现在你的等级是Lv.{data.bread_eaten // LEVEL}！您的{thing}排名为:{data.no}"
    elif wait_time < 0:
        msg_txt = f"你被禁止吃{thing}啦！{(abs(wait_time) + CD.EAT.value) // 60}分钟后才能吃哦！"
    else:
        event_ = EatEvent(group_id)
        event_.set_user_id(user_qq)
        msg_txt = event_.execute(eat_num)

    res_msg = msg_at + Message(msg_txt)
    await bot.send(event=event, message=res_msg)


@bread_rob.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg(), cmd: Message = RawCommand()):
    try:
        user_qq, group_id, name, msg_at, thing = await pre_get_data(event, bot, cmd, cmd_rob_ori)
    except CommandError:
        return

    robbed_qq = None
    rob_num = None
    for arg in args:
        if arg.type == "at":
            robbed_qq = arg.data.get("qq", "")
        if arg.type == "text":
            text = arg.data.get("text")
            try:
                rob_num = get_num_arg(text, RobEvent, group_id)
            except ArgsError as e:
                await bot.send(event=event, message=str(e))
                return

    if not robbed_qq:
        return
    robbed_name = await get_nickname(bot, robbed_qq, group_id)

    wait_time = cd_wait_time(group_id, user_qq, Action.ROB)
    if wait_time > 0:
        msg_txt = f"您还得等待{wait_time // 60}分钟才能抢{thing}w"
    elif wait_time < 0:
        msg_txt = f"你被禁止抢{thing}啦！{(abs(wait_time) + CD.ROB.value) // 60}分钟后才能抢哦！"
    else:
        event_ = RobEvent(group_id)
        event_.set_user_id(user_qq)
        event_.set_other_id(robbed_qq, robbed_name)
        msg_txt = event_.execute(rob_num)

    res_msg = msg_at + msg_txt
    await bot.send(event=event, message=res_msg)


@bread_give.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg(), cmd: Message = RawCommand()):
    try:
        user_qq, group_id, name, msg_at, thing = await pre_get_data(event, bot, cmd, cmd_give_ori)
    except CommandError:
        return

    given_qq = None
    give_num = None
    for arg in args:
        if arg.type == "at":
            given_qq = arg.data.get("qq", "")
        if arg.type == "text":
            text = arg.data.get("text")
            try:
                give_num = get_num_arg(text, GiveEvent, group_id)
            except ArgsError as e:
                await bot.send(event=event, message=str(e))
                return

    if not given_qq:
        return
    given_name = await get_nickname(bot, given_qq, group_id)

    wait_time = cd_wait_time(group_id, user_qq, Action.GIVE)
    if wait_time > 0:
        msg_txt = f"您还得等待{wait_time // 60}分钟才能送{thing}w"
    elif wait_time < 0:
        msg_txt = f"你被禁止送{thing}啦！{(abs(wait_time) + CD.GIVE.value) // 60}分钟后才能赠送哦！"
    else:
        event_ = GiveEvent(group_id)
        event_.set_user_id(user_qq)
        event_.set_other_id(given_qq, given_name)
        msg_txt = event_.execute(give_num)

    res_msg = msg_at + msg_txt
    await bot.send(event=event, message=res_msg)


@bread_bet.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg(), cmd: Message = RawCommand()):
    try:
        user_qq, group_id, name, msg_at, thing = await pre_get_data(event, bot, cmd, cmd_bet_ori)
    except CommandError:
        return

    wait_time = cd_wait_time(group_id, user_qq, Action.BET)
    if wait_time > 0:
        msg_txt = f"您还得等待{wait_time // 60}分钟才能猜拳w"
        await bot.send(event=event, message=msg_at + msg_txt)
        return
    elif wait_time < 0:
        msg_txt = f"你被禁止猜拳啦！{(abs(wait_time) + CD.BET.value) // 60}分钟后才能猜拳哦！"
        await bot.send(event=event, message=msg_at + msg_txt)
        return
    else:
        texts = args.extract_plain_text().split()
        ges = texts[0]
        bet_num = None
        if len(texts) == 2:
            bet_txt = texts[1]
            try:
                bet_num = get_num_arg(bet_txt, BetEvent, group_id)
            except ArgsError as e:
                await bot.send(event=event, message=str(e))
                return

        if ges not in ["石头", "剪刀", "布"]:
            await bot.send(event=event, message=f"没有{ges}这种东西啦！请输入“石头”或“剪刀”或“布”！例如 ’/bet 石头‘ ")
            return
        if ges == "石头":
            ges_ = BetEvent.G(0)
        elif ges == "布":
            ges_ = BetEvent.G(1)
        else:
            ges_ = BetEvent.G(2)

        event_ = BetEvent(group_id)
        event_.set_user_id(user_qq)
        event_.set_user_gestures(ges_)
        msg_txt = event_.execute(bet_num)

        res_msg = msg_at + msg_txt
        await bread_bet.finish(res_msg)


@bread_check.handle()
async def _(event: Event, bot: Bot, args: Message = CommandArg(), cmd: Message = RawCommand()):
    try:
        user_qq, group_id, name, msg_at, thing = await pre_get_data(event, bot, cmd, cmd_check_ori)
    except CommandError:
        return

    checked_qq = user_qq
    for arg in args:
        if arg.type == "at":
            checked_qq = arg.data.get("qq", "")
    if checked_qq == user_qq:
        user_data = BreadDataManage(group_id).get_bread_data(user_qq)
        msg = f"你现在拥有{user_data.bread_num}个{thing}，等级为Lv.{user_data.level}，排名为{user_data.no}！"
    else:
        checked_name = await get_nickname(bot, checked_qq, group_id)
        checked_data = BreadDataManage(group_id).get_bread_data(checked_qq)
        msg = f"{checked_name} 现在拥有{checked_data.bread_num}个{thing}，等级为Lv.{checked_data.level}，排名为{checked_data.no}！"

    await bot.send(event=event, message=msg_at + msg)


@bread_log.handle()
async def _(event: Event, bot: Bot, args: Message = CommandArg(), cmd: Message = RawCommand()):
    try:
        user_qq, group_id, name, msg_at, thing = await pre_get_data(event, bot, cmd, cmd_log_ori)
    except CommandError:
        return

    add_arg = args.extract_plain_text()
    if add_arg:
        action_args = ["买", "吃", "抢", "赠送", "猜拳"]
        if add_arg in action_args:
            val_index = action_args.index(add_arg)
            action = Action(val_index)
            data = BreadDataManage(group_id).get_action_log(action)
            name = await get_nickname(bot, data.user_id, group_id)
            attr_val = BreadDataManage.LOG_COLUMN[val_index].lower()
            app_msg = ["哇好有钱！", "好能吃，大胃王！", "大坏比！", "我超，带好人！", "哇塞，赌狗！"]
            msg = f"{add_arg}次数最多是{name}！共{getattr(data, attr_val)}次！" + app_msg[val_index]
            await bot.send(event=event, message=msg)
            return
        else:
            msg = f'没有{add_arg}这个操作啦！只有"买"，"吃"，"抢"，"赠送"，"猜拳" 例如：/logb 买'
            await bot.send(event=event, message=msg_at + msg)
            return

    checked_qq = user_qq
    for arg in args:
        if arg.type == "at":
            checked_qq = arg.data.get("qq", "")
    if checked_qq == user_qq:
        user_log = BreadDataManage(group_id).get_log_data(user_qq)
        msg = f"你共购买{user_log.buy_times}次，吃{user_log.eat_times}次，抢{user_log.rob_times}次，" \
              f"赠送{user_log.give_times}次，猜拳{user_log.bet_times}次！"
    else:
        checked_name = await get_nickname(bot, checked_qq, group_id)
        checked_log = BreadDataManage(group_id).get_log_data(checked_qq)
        msg = f"{checked_name}共购买{checked_log.buy_times}次，吃{checked_log.eat_times}次，抢{checked_log.rob_times}次，" \
              f"赠送{checked_log.give_times}次，猜拳{checked_log.bet_times}次！"
    await bot.send(event=event, message=msg_at + msg)


@bread_help.handle()
async def _(event: Event, bot: Bot, cmd: Message = RawCommand()):
    try:
        user_qq, group_id, name, msg_at, thing = await pre_get_data(event, bot, cmd, cmd_help_ori)
    except CommandError:
        return

    msg = f"""       🍞商店使用说明🍞
指令	        说明
买{thing}    	购买随机{thing}
啃{thing}	    吃随机{thing}
抢{thing}+@	  抢随机{thing}
送{thing}+@	  送随机{thing}
赌{thing}+""	猜拳赌随机{thing}
{thing}记录+""   查看操作次数最多的人
{thing}记录+@    查看操作次数
查看{thing}+@    查看{thing}数据
{thing}排行	    本群排行榜top5
更多详情见本项目地址：
https://github.com/Mai-icy/nonebot-plugin-bread-shop"""
    await bot.send(event=event, message=msg)


@bread_top.handle()
async def _(bot: Bot, event: Event, cmd: Message = RawCommand()):
    try:
        user_qq, group_id, name, msg_at, thing = await pre_get_data(event, bot, cmd, cmd_top_ori)
    except CommandError:
        return

    msg = await get_group_top(bot, group_id, thing)
    await bot.send(event=event, message=msg)


async def get_group_id(session_id):
    res = re.findall("_(.*)_", session_id)
    group_id = res[0]
    return group_id


async def get_group_top(bot: Bot, group_id, thing) -> Message:
    group_member_list = await bot.get_group_member_list(group_id=int(group_id))
    user_id_list = {info['user_id'] for info in group_member_list}
    all_data = BreadDataManage(group_id).get_all_data()
    num = 0
    append_text = f"🍞本群{thing}排行top5！🍞\n"
    for data in all_data:
        if int(data.user_id) in user_id_list:
            num += 1
            name = await get_nickname(bot, data.user_id, group_id)
            append_text += f"top{num} : {name} Lv.{data.bread_eaten // LEVEL}，拥有{thing}{data.bread_num}个\n"
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


def get_num_arg(text, event_type, group_id):
    text = text.strip()
    if text:
        if event_type(group_id).is_random():
            raise ArgsError("本群不可指定其它参数！请正确使用'@'")
        elif not text.isdigit():
            raise ArgsError("请输入数字！")
        else:
            return int(text)
    else:
        return None


async def pre_get_data(event, bot, cmd, cmd_ori):
    user_qq = event.get_user_id()
    group_id = await get_group_id(event.get_session_id())
    name = await get_nickname(bot, user_qq, group_id)

    # msg_at = Message(f"[CQ:at,qq={user_qq}]")
    msg_at = Message("@" + name)

    thing = bread_config.special_thing_group.get(group_id, bread_config.bread_thing)
    if not cmd[1:] in cmd_ori and thing not in cmd:
        raise CommandError

    if (bread_config.global_bread and group_id in bread_config.black_bread_groups) or \
            (not bread_config.global_bread and group_id not in bread_config.white_bread_groups):
        await bot.send(event=event, message=f"本群已禁止{thing}店！请联系bot管理员！")
        raise CommandError

    return user_qq, group_id, name, msg_at, thing


class ArgsError(ValueError):
    pass


class CommandError(ValueError):
    pass


@driver.on_shutdown
async def close_db():
    BreadDataManage.close_dbs()
