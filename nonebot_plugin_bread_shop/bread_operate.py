#!/usr/bin/python
# -*- coding:utf-8 -*-
import time
import random
from .bread_handle import BreadDataManage, Action, BreadData
from .config import MAX, MIN, CD, LEVEL, bread_config
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
    event_type = Action.ALL
    _instance = {}
    _has_init = {}
    _public_events = []
    _is_random = {}
    _is_random_global = True

    def __new__(cls, group_id: str):
        """事件关于群单例，每个群只能有一个事件实例"""
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
            self.thing = bread_config.special_thing_group.get(group_id, bread_config.bread_thing)
            if isinstance(self.thing, list):
                self.thing = self.thing[0]

    @classmethod
    def add_event(cls, func):
        """添加单个特殊事件"""
        if not func.group_id_list:
            cls._public_events.append(func)
        else:
            for group_id in func.group_id_list:
                cls(group_id)._private_events.append(func)

    @classmethod
    def add_events(cls, func_list):
        """添加多个特殊事件"""
        for func in func_list:
            cls.add_event(func)

    @classmethod
    def set_random_global(cls, flag):
        """全局是否随机"""
        cls._is_random_global = flag

    def set_random(self, flag):
        """设置是否随机操作数量，若为False，可以通过指令指定数量"""
        self._is_random[self.group_id] = flag

    def is_random(self):
        """获取 self.group_id 群组是否随机"""
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
        """设置用户id以及获取用户数据以待判断"""
        self.user_id = user_id
        self.user_data = self.bread_db.get_bread_data(self.user_id)

    def execute(self, num=None):
        """事件执行"""
        pre_error = self._pre_event(num)
        if pre_error:
            return pre_error

        return_data = self._special_event()
        self.bread_db.add_user_log(self.user_id, self.event_type)
        if return_data:
            return return_data

        return self.normal_event()

    def normal_event(self):
        """正常事件流程 （虚函数）"""

    def _pre_event(self, num=None):
        """预处理事件，提前生成随机值或其它值。 num 为非随机情况下得指定数量值"""
        self.thing = bread_config.special_thing_group.get(self.group_id, bread_config.bread_thing)
        if isinstance(self.thing, list):
            self.thing = self.thing[0]

        # 获取操作最大值或者最小值
        max_num = getattr(MAX, self.event_type.name).value
        min_num = getattr(MIN, self.event_type.name).value

        if not self.is_random() and num is not None:
            if min_num <= num <= max_num:
                self.action_num = num
                return
            else:
                return "数量和限制不符！"
        # self.action_num = random.randint(min_num, min(max_num, self.user_data.bread_num))


class _Event2(_Event):
    """双用户事件"""

    def __init__(self, group_id: str):
        super().__init__(group_id)
        self.other_id = None
        self.other_name = None
        self.other_data = BreadData(0, "0", 0, 0, 0)

    def set_other_id(self, other_id: str, other_name: str):
        """设置第二个用户id 通常为”被操作“的用户"""
        self.other_id = other_id
        self.other_name = other_name
        self.other_data = self.bread_db.get_bread_data(other_id)


class BuyEvent(_Event):
    """
    买事件，用户增加面包
    """
    event_type = Action.BUY
    _instance = {}
    _has_init = {}
    _public_events = []
    _is_random = {}
    _is_random_global = True

    def normal_event(self):
        new_bread_num = self.bread_db.add_bread(self.user_id, self.action_num)
        new_bread_no = self.bread_db.update_no(self.user_id)
        append_text = f"成功购买了{self.action_num}个{self.thing}w，现在一共拥有{new_bread_num}个{self.thing}！您的{self.thing}排名为:{new_bread_no}"
        self.bread_db.cd_update_stamp(self.user_id, Action.BUY)
        return append_text

    def _pre_event(self, num=None):
        self.action_num = random.randint(MIN.BUY.value, MAX.BUY.value)
        return super(BuyEvent, self)._pre_event(num)


class EatEvent(_Event):
    """
    吃事件，用户减少面包，增加“已吃面包”数量，在一定值等级会随之提高
    """
    event_type = Action.EAT
    _instance = {}
    _has_init = {}
    _public_events = []
    _is_random = {}
    _is_random_global = True

    def normal_event(self):
        now_bread = self.bread_db.reduce_bread(self.user_id, self.action_num)
        eaten_bread = self.bread_db.add_bread(self.user_id, self.action_num, Action.EAT)
        append_text = f"成功吃掉了{self.action_num}个{self.thing}w！现在你还剩{now_bread}个{self.thing}w！您目前的等级为Lv.{eaten_bread // LEVEL}"
        self.bread_db.cd_update_stamp(self.user_id, Action.EAT)
        self.bread_db.update_no(self.user_id)
        return append_text

    def _pre_event(self, num=None):
        if self.user_data.bread_num < MIN.EAT.value or (num and self.user_data.bread_num < num):
            append_text = f"你的{self.thing}还不够吃w，来买一些{self.thing}吧！"
            return append_text

        self.action_num = random.randint(MIN.EAT.value, min(MAX.EAT.value, self.user_data.bread_num))
        return super(EatEvent, self)._pre_event(num)


class BetEvent(_Event):
    """
    猜拳事件，由用户选择“石头”“剪刀”“石头”中的一个，bot将会随机生成一个手势
    若用户胜利，用户获得面包，若失败，则丢失面包。
    """
    event_type = Action.BET
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
        DRAW = 0  # 平局
        WIN = 1
        LOST = 2

    def __init__(self, group_id: str):
        super().__init__(group_id)
        self.user_gestures = None  # 额外初始化一个手势变量

    def set_user_gestures(self, ges: G):
        """猜拳，设置用户的手势"""
        self.user_gestures = ges

    def normal_event(self):
        if self.outcome == self.RES.WIN:
            new_bread_num_user = self.bread_db.add_bread(self.user_id, self.action_num)
            self.bread_db.update_no(self.user_id)
            append_text = f"{self.bot_ges_text}! 呜呜，我输了，给你{self.action_num}个{self.thing}！你现在拥有{new_bread_num_user}个{self.thing}！"
            self.bread_db.cd_update_stamp(self.user_id, Action.BET)
        elif self.outcome == self.RES.DRAW:
            append_text = f"{self.bot_ges_text}!平局啦！{self.thing}都还给你啦！还可以再来一次w！"
        else:  # self.outcome == self.RES.LOST
            new_bread_num_user = self.bread_db.reduce_bread(self.user_id, self.action_num)
            self.bread_db.update_no(self.user_id)
            append_text = f"{self.bot_ges_text}!嘿嘿，我赢啦！你的{self.action_num}个{self.thing}归我了！你现在拥有{new_bread_num_user}个{self.thing}！"
            self.bread_db.cd_update_stamp(self.user_id, Action.BET)
        return append_text

    def _pre_event(self, num=None):
        if self.user_data.bread_num < MIN.BET.value or (num and self.user_data.bread_num < num):
            append_text = f"你的{self.thing}还不够猜拳w，来买一些{self.thing}吧！"
            return append_text

        self.bot_ges = self.G(random.randint(0, 2))
        self.bot_ges_text = ("石头", "布", "剪刀")[self.bot_ges.value]
        val = self.user_gestures.value - self.bot_ges.value
        if val == -2 or val == -1:
            val = 3 + val
        self.outcome = self.RES(val)

        self.action_num = random.randint(MIN.BET.value, min(MAX.BET.value, self.user_data.bread_num))
        return super(BetEvent, self)._pre_event(num)


class RobEvent(_Event2):
    """
    抢劫事件，用户1获得面包，用户2减少面包
    """
    event_type = Action.ROB
    _instance = {}
    _has_init = {}
    _public_events = []
    _is_random = {}
    _is_random_global = True

    def normal_event(self):
        new_bread_num = self.bread_db.add_bread(self.user_id, self.action_num)
        self.bread_db.reduce_bread(self.other_id, self.action_num)
        new_bread_no = self.bread_db.update_no(self.user_id)
        self.bread_db.update_no(self.other_id)

        append_text = f"成功抢了{self.other_name}{self.action_num}个{self.thing}，你现在拥有{new_bread_num}个{self.thing}！" \
                      f"您的{self.thing}排名为:{new_bread_no}"
        self.bread_db.cd_update_stamp(self.user_id, Action.ROB)
        return append_text

    def _pre_event(self, num=None):
        if not self.other_data or self.other_data.bread_num < MIN.ROB.value\
                or (num and self.other_data.bread_num < num):
            append_text = f"{self.other_name}没有那么多{self.thing}可抢呜"
            return append_text

        self.action_num = random.randint(MIN.ROB.value, min(MAX.ROB.value, self.other_data.bread_num))
        pre_res = super(RobEvent, self)._pre_event(num)
        if pre_res:  # 有返回值代表事件提前结束
            return pre_res

        if self.user_id == self.other_id:
            reduce_num = min(self.action_num, self.user_data.bread_num)
            append_text = f"这么想抢自己哇，那我帮你抢！抢了你{reduce_num}个{self.thing}嘿嘿！"
            self.bread_db.reduce_bread(self.user_id, reduce_num)
            self.bread_db.update_no(self.other_id)
            self.bread_db.cd_update_stamp(self.user_id, Action.ROB)
            return append_text


class GiveEvent(_Event2):
    """
    赠送事件，用户1失去面包，用户2获得面包
    """
    event_type = Action.GIVE
    _instance = {}
    _has_init = {}
    _public_events = []
    _is_random = {}
    _is_random_global = True

    def normal_event(self):
        new_bread_num_given = self.bread_db.add_bread(self.other_id, self.action_num)
        new_bread_num_user = self.bread_db.reduce_bread(self.user_id, self.action_num)
        self.bread_db.update_no(self.other_id)
        self.bread_db.update_no(self.user_id)

        append_text = f"成功赠送了{self.action_num}个{self.thing}给{self.other_name}，你现在拥有{new_bread_num_user}个{self.thing}！" \
                      f"{self.other_name}有{new_bread_num_given}个{self.thing}！"
        self.bread_db.cd_update_stamp(self.user_id, Action.GIVE)
        return append_text

    def _pre_event(self, num=None):
        if self.user_data.bread_num < MIN.GIVE.value or (num and self.user_data.bread_num < num):
            append_text = f"你的{self.thing}还不够赠送w，来买一些{self.thing}吧！"
            return append_text

        self.action_num = random.randint(MIN.GIVE.value, min(MAX.GIVE.value, self.user_data.bread_num))
        pre_res = super(GiveEvent, self)._pre_event(num)
        if pre_res:  # 有返回值代表事件提前结束
            return pre_res

        if self.user_id == self.other_id:
            append_text = f"送给自己肯定是不行的啦！送给我叭！你送了我{self.action_num}个{self.thing}嘿嘿！"
            self.bread_db.reduce_bread(self.user_id, self.action_num)
            self.bread_db.update_no(self.user_id)
            self.bread_db.cd_update_stamp(self.user_id, Action.GIVE)
            return append_text
