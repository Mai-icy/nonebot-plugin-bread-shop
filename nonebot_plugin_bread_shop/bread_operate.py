#!/usr/bin/python
# -*- coding:utf-8 -*-
import time
import random
from .bread_handle import BreadDataManage, Action, BreadData
from .config import MAX, MIN, CD, THING, LEVEL_NUM
from enum import Enum


def cd_wait_time(group_id, user_id, operate: Action) -> int:
    """获取需要等待的CD秒数，小于0则被ban，大于0则还在冷却，等于0则可操作"""
    cd_stamp = BreadDataManage(group_id).cd_get_stamp(user_id, operate)
    now_stamp = int(time.time())
    sep_time = now_stamp - cd_stamp
    cd = getattr(CD, operate.name)
    if sep_time < 0:
        return sep_time
    return cd.value - sep_time if sep_time < cd.value else 0


class _Event:
    _instance = {}
    _has_init = {}
    _public_events = []
    _is_random = {}
    _is_random_global = True

    def __new__(cls, group_id: str):
        if group_id is None:
            return None
        if cls._instance.get(group_id) is None:
            cls._instance[group_id] = super(_Event, cls).__new__(cls)
        return cls._instance[group_id]

    def __init__(self, group_id: str):
        if not self._has_init.get(group_id):
            self._has_init[group_id] = True
            self.group_id = group_id
            self.bread_db = BreadDataManage(group_id)
            self.user_id = None
            self.user_data = BreadData(0, "0", 0, 0, 0)
            self._private_events = []

    @classmethod
    def add_event(cls, func):
        if not func.group_id_list:
            cls._public_events.append(func)
        else:
            for group_id in func.group_id_list:
                cls(group_id)._private_events.append(func)

    @classmethod
    def add_events(cls, func_list):
        for func in func_list:
            cls.add_event(func)

    @classmethod
    def set_random_global(cls, flag):
        cls._is_random_global = flag

    def set_random(self, flag):
        self._is_random[self.group_id] = flag

    def is_random(self):
        if self._is_random.get(self.group_id) is not None:
            return self._is_random.get(self.group_id)
        else:
            return self._is_random_global

    def _special_event(self):
        """按照优先级排布，同优先级随机排布"""
        events = self._private_events + self._public_events
        events.sort(key=lambda x: (x.priority, random.random()))
        for event_func in events:
            return_data = event_func(self)
            if return_data:
                return return_data

    def set_user_id(self, user_id: str):
        self.user_id = user_id
        self.user_data = self.bread_db.get_bread_data(self.user_id)

    def execute(self, num=None):
        pass

    def normal_event(self):
        pass

    def _pre_judge_random(self, num=None):
        pass


class BuyEvent(_Event):
    _instance = {}
    _has_init = {}
    _public_events = []
    _is_random = {}
    _is_random_global = True

    def execute(self, num=None):
        pre_error = self._pre_judge_random(num)
        if pre_error:
            return pre_error

        return_data = self._special_event()
        self.bread_db.add_user_log(self.user_id, Action.BUY)
        if return_data:
            return return_data

        return self.normal_event()

    def normal_event(self):
        new_bread_num = self.bread_db.add_bread(self.user_id, self.buy_num)
        new_bread_no = self.bread_db.update_no(self.user_id)
        append_text = f"成功购买了{self.buy_num}个{THING}w，现在一共拥有{new_bread_num}个{THING}！您的{THING}排名为:{new_bread_no}"
        self.bread_db.cd_update_stamp(self.user_id, Action.BUY)
        return append_text

    def _pre_judge_random(self, num=None):
        if not self.is_random() and num is not None:
            if MIN.BUY.value <= num <= MAX.BUY.value:
                self.buy_num = num
                return
            else:
                return "数量和限制不符！"
        self.buy_num = random.randint(MIN.BUY.value, min(MAX.BUY.value, self.user_data.bread_num))


class EatEvent(_Event):
    _instance = {}
    _has_init = {}
    _public_events = []
    _is_random = {}
    _is_random_global = True

    def execute(self, num=None):
        if self.user_data.bread_num < MIN.EAT.value or (num and self.user_data.bread_num < num):
            append_text = f"你的{THING}还不够吃w，来买一些{THING}吧！"
            return append_text

        pre_error = self._pre_judge_random(num)
        if pre_error:
            return pre_error

        return_data = self._special_event()
        self.bread_db.add_user_log(self.user_id, Action.EAT)
        if return_data:
            return return_data

        return self.normal_event()

    def normal_event(self):
        now_bread = self.bread_db.reduce_bread(self.user_id, self.eat_num)
        eaten_bread = self.bread_db.add_bread(self.user_id, self.eat_num, Action.EAT)
        append_text = f"成功吃掉了{self.eat_num}个{THING}w！现在你还剩{now_bread}个{THING}w！您目前的等级为Lv.{eaten_bread // LEVEL_NUM}"
        self.bread_db.cd_update_stamp(self.user_id, Action.EAT)
        self.bread_db.update_no(self.user_id)
        return append_text

    def _pre_judge_random(self, num=None):
        if not self.is_random() and num is not None:
            if MIN.EAT.value <= num <= MAX.EAT.value:
                self.eat_num = num
                return
            else:
                return "数量和限制不符！"
        self.eat_num = random.randint(MIN.EAT.value, min(MAX.EAT.value, self.user_data.bread_num))


class RobEvent(_Event):
    _instance = {}
    _has_init = {}
    _public_events = []
    _is_random = {}
    _is_random_global = True

    def __init__(self, group_id: str):
        super().__init__(group_id)
        self.robbed_id = None
        self.robbed_name = None
        self.robbed_data = BreadData(0, "0", 0, 0, 0)

    def set_robbed_id(self, robbed_id: str, robbed_name: str):
        self.robbed_id = robbed_id
        self.robbed_name = robbed_name
        self.robbed_data = self.bread_db.get_bread_data(robbed_id)

    def execute(self, num=None):
        if not self.robbed_data or self.robbed_data.bread_num < MIN.ROB.value\
                or (num and self.robbed_data.bread_num < num):
            append_text = f"{self.robbed_name}没有那么多{THING}可抢呜"
            return append_text

        pre_error = self._pre_judge_random(num)
        if pre_error:
            return pre_error

        if self.user_id == self.robbed_id:
            append_text = f"这么想抢自己哇，那我帮你抢！抢了你{self.rob_num}个{THING}嘿嘿！"
            self.bread_db.reduce_bread(self.user_id, self.rob_num)
            self.bread_db.update_no(self.robbed_id)
            self.bread_db.cd_update_stamp(self.user_id, Action.ROB)
            return append_text

        return_data = self._special_event()
        self.bread_db.add_user_log(self.user_id, Action.ROB)
        if return_data:
            return return_data

        return self.normal_event()

    def normal_event(self):
        new_bread_num = self.bread_db.add_bread(self.user_id, self.rob_num)
        self.bread_db.reduce_bread(self.robbed_id, self.rob_num)
        new_bread_no = self.bread_db.update_no(self.user_id)
        self.bread_db.update_no(self.robbed_id)

        append_text = f"成功抢了{self.robbed_name}{self.rob_num}个{THING}，你现在拥有{new_bread_num}个{THING}！" \
                      f"您的{THING}排名为:{new_bread_no}"
        self.bread_db.cd_update_stamp(self.user_id, Action.ROB)
        return append_text

    def _pre_judge_random(self, num=None):
        if not self.is_random() and num is not None:
            if MIN.ROB.value <= num <= MAX.ROB.value:
                self.rob_num = num
                return
            else:
                return "数量和限制不符！"
        self.rob_num = random.randint(MIN.ROB.value, min(MAX.ROB.value, self.user_data.bread_num))


class GiveEvent(_Event):
    _instance = {}
    _has_init = {}
    _public_events = []
    _is_random = {}
    _is_random_global = True

    def __init__(self, group_id):
        super().__init__(group_id)
        self.given_id = None
        self.given_name = None
        self.given_data = BreadData(0, "0", 0, 0, 0)

    def set_given_id(self, robbed_id: str, robbed_name: str):
        self.given_id = robbed_id
        self.given_name = robbed_name
        self.given_data = self.bread_db.get_bread_data(robbed_id)

    def execute(self, num=None):
        if self.user_data.bread_num < MIN.GIVE.value or (num and self.user_data.bread_num < num):
            append_text = f"你的{THING}还不够赠送w，来买一些{THING}吧！"
            return append_text

        pre_error = self._pre_judge_random(num)
        if pre_error:
            return pre_error

        if self.user_id == self.given_id:
            append_text = f"送给自己肯定是不行的啦！送给我叭！你送了我{self.give_num}个{THING}嘿嘿！"
            self.bread_db.reduce_bread(self.user_id, self.give_num)
            self.bread_db.update_no(self.user_id)
            self.bread_db.cd_update_stamp(self.user_id, Action.GIVE)
            return append_text

        return_data = self._special_event()
        self.bread_db.add_user_log(self.user_id, Action.GIVE)

        if return_data:
            return return_data
        return self.normal_event()

    def normal_event(self):
        new_bread_num_given = self.bread_db.add_bread(self.given_id, self.give_num)
        new_bread_num_user = self.bread_db.reduce_bread(self.user_id, self.give_num)
        self.bread_db.update_no(self.given_id)
        self.bread_db.update_no(self.user_id)

        append_text = f"成功赠送了{self.give_num}个{THING}给{self.given_name}，你现在拥有{new_bread_num_user}个{THING}！" \
                      f"{self.given_name}有{new_bread_num_given}个{THING}！"
        self.bread_db.cd_update_stamp(self.user_id, Action.GIVE)
        return append_text

    def _pre_judge_random(self, num=None):
        if not self.is_random() and num is not None:
            if MIN.GIVE.value <= num <= MAX.GIVE.value:
                self.give_num = num
                return
            else:
                return "数量和限制不符！"
        self.give_num = random.randint(MIN.GIVE.value, min(MAX.GIVE.value, self.user_data.bread_num))


class BetEvent(_Event):
    _instance = {}
    _has_init = {}
    _public_events = []
    _is_random = {}
    _is_random_global = True

    class G(Enum):
        ROCK = 0
        PAPER = 1
        SCISSORS = 2

    class RES(Enum):
        DRAW = 0
        WIN = 1
        LOST = 2

    def __init__(self, group_id: str):
        super().__init__(group_id)
        self.user_gestures = None

    def set_user_gestures(self, ges: G):
        self.user_gestures = ges

    def execute(self, num=None):
        if self.user_data.bread_num < MIN.BET.value or (num and self.user_data.bread_num < num):
            append_text = f"你的{THING}还不够猜拳w，来买一些{THING}吧！"
            return append_text

        self.bread_db.add_user_log(self.user_id, Action.BET)

        pre_error = self._pre_judge_random(num)
        if pre_error:
            return pre_error

        return_data = self._special_event()
        if return_data:
            return return_data
        return self.normal_event()

    def normal_event(self):
        if self.outcome == self.RES.WIN:
            new_bread_num_user = self.bread_db.add_bread(self.user_id, self.bet_num)
            self.bread_db.update_no(self.user_id)
            append_text = f"{self.bot_ges_text}! 呜呜，我输了，给你{self.bet_num}个{THING}！你现在拥有{new_bread_num_user}个{THING}！"
            self.bread_db.cd_update_stamp(self.user_id, Action.BET)
        elif self.outcome == self.RES.DRAW:
            append_text = f"{self.bot_ges_text}!平局啦！{THING}都还给你啦！还可以再来一次w！"
        else:  # self.outcome == self.RES.LOST
            new_bread_num_user = self.bread_db.reduce_bread(self.user_id, self.bet_num)
            self.bread_db.update_no(self.user_id)
            append_text = f"{self.bot_ges_text}!嘿嘿，我赢啦！你的{self.bet_num}个{THING}归我了！你现在拥有{new_bread_num_user}个{THING}！"
            self.bread_db.cd_update_stamp(self.user_id, Action.BET)
        return append_text

    def _pre_judge_random(self, num=None):
        self.bot_ges = self.G(random.randint(0, 2))
        self.bot_ges_text = ("石头", "布", "剪刀")[self.bot_ges.value]
        val = self.user_gestures.value - self.bot_ges.value
        if val == -2 or val == -1:
            val = 3 + val
        self.outcome = self.RES(val)

        if not self.is_random() and num is not None:
            if MIN.BET.value <= num <= MAX.BET.value:
                self.bet_num = num
                return
            else:
                return "数量和限制不符！"
        self.bet_num = random.randint(MIN.BET.value, min(MAX.BET.value, self.user_data.bread_num))
