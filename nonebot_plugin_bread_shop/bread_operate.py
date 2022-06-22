#!/usr/bin/python
# -*- coding:utf-8 -*-
import time
import random
from .bread_handle import BreadDataManage, Action, BreadData
from .config import MAX, MIN, CD
from enum import Enum


def cd_wait_time(group_id, user_id, operate: Action) -> int:
    """获取需要等待的CD秒数，小于0则被ban，大于0则还在冷却，等于0则可操作"""
    cd_stamp = BreadDataManage(group_id).cd_get_stamp(user_id, operate)
    now_stamp = int(time.time())
    sep_time = now_stamp - cd_stamp
    cd = getattr(CD, operate.name)
    return cd.value - sep_time if sep_time < cd.value else 0


class _Event:

    def __init__(self):
        self.group_id = None
        self.user_id = None
        self.user_data = BreadData(0, "0", 0, 0, 0)
        self.bread_db = BreadDataManage(None)
        self._event_list = []

    def set_group_id(self, group_id: str):
        self.group_id = group_id
        self.bread_db = BreadDataManage(group_id)

    def set_user_id(self, user_id: str):
        self.user_id = user_id
        self.user_data = self.bread_db.get_bread_data(self.user_id)

    def add_event(self, func):
        self._event_list.append(func)

    def add_events(self, func_list):
        self._event_list.extend(func_list)

    def _special_event(self):
        """按照优先级排布，同优先级随机排布"""
        self._event_list.sort(key=lambda x: (x[0], random.random()))
        for event_func in self._event_list:
            return_data = event_func[1](self)
            if return_data:
                return return_data

    def execute(self):
        pass

    def normal_event(self):
        pass


class BuyEvent(_Event):
    def execute(self):
        self.bread_db.log_user_action(self.user_id, Action.BUY)

        return_data = self._special_event()
        if return_data:
            return return_data

        return self.normal_event()

    def normal_event(self):
        buy_num = random.randint(MIN.BUY.value, MAX.BUY.value)
        new_bread_num = self.bread_db.add_bread(self.user_id, buy_num)
        new_bread_no = self.bread_db.update_no(self.user_id)
        append_text = f"成功购买了{buy_num}个面包w，现在一共拥有{new_bread_num}个面包！您的面包排名为:{new_bread_no}"
        self.bread_db.cd_update_stamp(self.user_id, Action.BUY)
        return append_text


class EatEvent(_Event):
    def execute(self):
        self.bread_db.log_user_action(self.user_id, Action.EAT)

        if self.user_data.bread_num < MIN.EAT.value:
            append_text = f"你的面包还不够吃w，来买一些面包吧！"
            return append_text

        return_data = self._special_event()
        if return_data:
            return return_data

        return self.normal_event()

    def normal_event(self):
        eat_num = random.randint(MIN.EAT.value, min(MAX.EAT.value, self.user_data.bread_num))
        now_bread = self.bread_db.reduce_bread(self.user_id, eat_num)
        eaten_bread = self.bread_db.add_bread(self.user_id, eat_num, Action.EAT)
        append_text = f"成功吃掉了{eat_num}个面包w！现在你还剩{now_bread}个面包w！您目前的等级为Lv.{eaten_bread // 10}"
        self.bread_db.cd_update_stamp(self.user_id, Action.EAT)
        self.bread_db.update_no(self.user_id)
        return append_text


class RobEvent(_Event):
    def __init__(self):
        super().__init__()
        self.robbed_id = None
        self.robbed_name = None
        self.robbed_data = BreadData(0, "0", 0, 0, 0)

    def set_robbed_id(self, robbed_id: str, robbed_name: str):
        self.robbed_id = robbed_id
        self.robbed_name = robbed_name
        self.robbed_data = self.bread_db.get_bread_data(robbed_id)

    def execute(self):
        self.bread_db.log_user_action(self.user_id, Action.ROB)

        if not self.robbed_data or self.robbed_data.bread_num < MIN.ROB.value:
            append_text = f"{self.robbed_name}没有面包可抢呜"
            return append_text

        return_data = self._special_event()
        if return_data:
            return return_data

        return self.normal_event()

    def normal_event(self):
        rob_num = random.randint(MIN.ROB.value, min(MAX.ROB.value, self.robbed_data.bread_num))
        new_bread_num = self.bread_db.add_bread(self.user_id, rob_num)
        self.bread_db.reduce_bread(self.robbed_id, rob_num)
        new_bread_no = self.bread_db.update_no(self.user_id)
        self.bread_db.update_no(self.robbed_id)

        append_text = f"成功抢了{self.robbed_name}{rob_num}个面包，你现在拥有{new_bread_num}个面包！您的面包排名为:{new_bread_no}"
        self.bread_db.cd_update_stamp(self.user_id, Action.ROB)
        return append_text


class GiveEvent(_Event):
    def __init__(self):
        super().__init__()
        self.given_id = None
        self.given_name = None
        self.given_data = BreadData(0, "0", 0, 0, 0)

    def set_given_id(self, robbed_id: str, robbed_name: str):
        self.given_id = robbed_id
        self.given_name = robbed_name
        self.given_data = self.bread_db.get_bread_data(robbed_id)

    def execute(self):
        self.bread_db.log_user_action(self.user_id, Action.GIVE)

        if self.user_data.bread_num < MIN.EAT.value:
            append_text = f"你的面包还不够赠送w，来买一些面包吧！"
            return append_text

        return_data = self._special_event()
        if return_data:
            return return_data
        return self.normal_event()

    def normal_event(self):
        give_num = random.randint(MIN.GIVE.value, min(MAX.GIVE.value, self.user_data.bread_num))
        new_bread_num_given = self.bread_db.add_bread(self.given_id, give_num)
        new_bread_num_user = self.bread_db.reduce_bread(self.user_id, give_num)
        self.bread_db.update_no(self.given_id)
        self.bread_db.update_no(self.user_id)

        append_text = f"成功赠送了{give_num}个面包给{self.given_name}，你现在拥有{new_bread_num_user}个面包！" \
                      f"{self.given_name}有{new_bread_num_given}个面包！"
        self.bread_db.cd_update_stamp(self.user_id, Action.GIVE)
        return append_text


class BetEvent(_Event):
    class G(Enum):
        ROCK = 0
        PAPER = 1
        SCISSORS = 2

    def __init__(self):
        super().__init__()
        self.user_gestures = None

    def set_user_gestures(self, ges: G):
        self.user_gestures = ges

    def execute(self):
        self.bread_db.log_user_action(self.user_id, Action.BET)

        if self.user_data.bread_num < MIN.BET.value:
            append_text = f"你的面包还不够猜拳w，来买一些面包吧！"
            return append_text

        return_data = self._special_event()
        if return_data:
            return return_data

    def normal_event(self):
        bet_num = random.randint(MIN.BET.value, min(MAX.BET.value, self.user_data.bread_num))

        bot_ges = self.G(random.randint(0, 2))
        bot_ges_text = ("石头", "布", "剪刀")[bot_ges.value]

        val = self.user_gestures.value - bot_ges.value
        if val == 1 or val == -2:
            new_bread_num_user = self.bread_db.add_bread(self.user_id, bet_num)
            self.bread_db.update_no(self.user_id)
            append_text = f"{bot_ges_text}! 呜呜，我输了，给你{bet_num}个面包！你现在拥有{new_bread_num_user}个面包！"
            self.bread_db.cd_update_stamp(self.user_id, Action.BET)
        elif val == 0:
            append_text = f"{bot_ges_text}!平局啦！面包都还给你啦！还可以再来一次w！"
        else:
            new_bread_num_user = self.bread_db.reduce_bread(self.user_id, bet_num)
            self.bread_db.update_no(self.user_id)
            append_text = f"{bot_ges_text}!嘿嘿，我赢啦！你的{bet_num}个面包归我了！你现在拥有{new_bread_num_user}个面包！"
            self.bread_db.cd_update_stamp(self.user_id, Action.BET)
        return append_text
