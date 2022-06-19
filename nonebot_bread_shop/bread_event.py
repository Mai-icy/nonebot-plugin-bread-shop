#!/usr/bin/python
# -*- coding:utf-8 -*-
import random
from .bread_handle import Action
from .bread_operate import Rob, Eat, Buy
from functools import wraps

rob_events = []
eat_events = []
buy_events = []


def probability(value, action: Action):
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if random.random() < value:
                return func(*args, **kwargs)
            else:
                return None
        event_list = (buy_events, eat_events, rob_events)[action.value]
        event_list.append(inner)
        return inner
    return wrapper


@probability(0.09, Action.ROB)
def rob_event_fail(event: Rob):
    if event.user_data.bread_num < 7:
        loss_num = random.randint(0, event.user_data.bread_num)
    else:
        loss_num = random.randint(1, 7)
    new_bread_num = event.bread_db.reduce_bread(event.user_id, loss_num)
    event.bread_db.update_no(event.user_id)
    append_text = f"抢面包失败啦！被{event.robbed_name}反击，你丢失{loss_num}个面包！你现在拥有{new_bread_num}个面包！"
    event.bread_db.update_cd_stamp(event.user_id, Action.ROB)
    return append_text











