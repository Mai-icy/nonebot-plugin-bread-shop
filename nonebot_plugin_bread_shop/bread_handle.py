#!/usr/bin/python
# -*- coding:utf-8 -*-
import sqlite3
import time

from collections import namedtuple
from enum import Enum
from functools import wraps
from inspect import signature
from pathlib import Path
from typing import List

from .config import LEVEL

DATABASE = Path() / "data" / "bread"


class Action(Enum):
    ALL = -1
    BUY = 0
    EAT = 1
    ROB = 2
    GIVE = 3
    BET = 4


BreadData = namedtuple("BreadData", ["no", "user_id", "bread_num", "bread_eaten", "level"])
LogData = namedtuple("LogData", ["user_id", "buy_times", "eat_times", "rob_times", "give_times", "bet_times"])


def type_assert(*ty_args, **ty_kwargs):
    """sql类型检查"""
    def decorate(func):
        sig = signature(func)
        bound_types = sig.bind_partial(*ty_args, **ty_kwargs).arguments

        @wraps(func)
        def wrapper(*args, **kwargs):
            bound_values = sig.bind(*args, **kwargs)
            for name, value in bound_values.arguments.items():
                if name in bound_types:
                    if bound_types[name] == "user_id":
                        if isinstance(value, str):
                            if not value.isdigit():
                                raise TypeError("user_id must consist of numeric characters.")
                        else:
                            raise TypeError('Argument {} must be {}'.format(name, str))
                    elif not isinstance(value, bound_types[name]):
                        raise TypeError('Argument {} must be {}'.format(name, bound_types[name]))
            return func(*args, **kwargs)
        return wrapper
    return decorate


class BreadDataManage:
    _instance = {}
    _has_init = {}
    CD_COLUMN = ("BUY_CD", "EAT_CD", "ROB_CD", "GIVE_CD", "BET_CD")
    DATA_COLUMN = ("BREAD_NUM", "BREAD_EATEN")
    LOG_COLUMN = ("BUY_TIMES", "EAT_TIMES", "ROB_TIMES", "GIVE_TIMES", "BET_TIMES")

    def __new__(cls, group_id):
        if group_id is None:
            return None
        if cls._instance.get(group_id) is None:
            cls._instance[group_id] = super(BreadDataManage, cls).__new__(cls)
        return cls._instance[group_id]

    def __init__(self, group_id):
        if not BreadDataManage._has_init.get(group_id):
            BreadDataManage._has_init[group_id] = True
            self.database_path = DATABASE / group_id
            if not self.database_path.exists():
                self.database_path.mkdir(parents=True)
                self.database_path /= "bread.db"
                self.conn = sqlite3.connect(self.database_path)
                self._create_file()
            else:
                self.database_path /= "bread.db"
                self.conn = sqlite3.connect(self.database_path)
            print(f"群组{group_id}数据库连接！")

    def close(self):
        self.conn.close()
        print("数据库关闭！")

    def _create_file(self) -> None:
        """创建数据库文件"""
        c = self.conn.cursor()
        c.execute('''CREATE TABLE BREAD_DATA
                           (NO            INTEGER PRIMARY KEY UNIQUE,
                           USERID         TEXT     ,
                           BREAD_NUM      INTEGER  ,
                           BREAD_EATEN    INTEGER  
                           );''')
        c.execute('''CREATE TABLE BREAD_LOG
                           (USERID         TEXT     ,
                           BUY_TIMES      INTEGER  ,
                           EAT_TIMES      INTEGER  ,
                           ROB_TIMES      INTEGER  ,
                           GIVE_TIMES     INTEGER  ,
                           BET_TIMES      INTEGER  
                           );''')
        c.execute('''CREATE TABLE BREAD_CD
                           (USERID        TEXT     ,
                           BUY_CD         INTEGER  ,
                           EAT_CD         INTEGER  ,
                           ROB_CD         INTEGER  ,
                           GIVE_CD        INTEGER  ,
                           BET_CD         INTEGER  
                           );''')
        self.conn.commit()

    def _get_id(self) -> int:
        """获取下一个id"""
        cur = self.conn.cursor()
        cur.execute('select * from BREAD_DATA')
        result = cur.fetchall()
        return len(result) + 1

    @classmethod
    def close_dbs(cls):
        for group_id in cls._instance.keys():
            BreadDataManage(group_id).close()

    @type_assert(object, "user_id")
    def _create_user(self, user_id: str) -> None:
        """在数据库中创建用户并初始化"""
        new_id = self._get_id()
        c = self.conn.cursor()
        sql = f"INSERT INTO BREAD_DATA (NO,USERID,BREAD_NUM,BREAD_EATEN) VALUES (?,?,0,0)"
        c.execute(sql, (new_id, user_id))
        sql = f"INSERT INTO BREAD_LOG (USERID,BUY_TIMES,EAT_TIMES,ROB_TIMES,GIVE_TIMES,BET_TIMES)" \
              f" VALUES (?,0,0,0,0,0)"
        c.execute(sql, (user_id,))
        sql = f"INSERT INTO BREAD_CD (USERID,BUY_CD,EAT_CD,ROB_CD,GIVE_CD,BET_CD) VALUES (?,0,0,0,0,0)"
        c.execute(sql, (user_id,))
        self.conn.commit()

    @type_assert(object, "user_id", Action)
    def cd_refresh(self, user_id: str, action: Action) -> None:
        """刷新用户操作cd"""
        if action == Action.ALL:
            cur = self.conn.cursor()
            for key in self.CD_COLUMN:
                sql = f"update BREAD_CD set {key}=? where USERID=?"
                cur.execute(sql, (1, user_id))
            self.conn.commit()
            return
        op_key = self.CD_COLUMN[action.value]
        sql = f"update BREAD_CD set {op_key}=? where USERID=?"
        cur = self.conn.cursor()
        cur.execute(sql, (1, user_id))
        self.conn.commit()

    @type_assert(object, "user_id", Action)
    def cd_get_stamp(self, user_id: str, action: Action) -> int:
        """获取用户上次操作时间戳"""
        cur = self.conn.cursor()
        sql = f"select * from BREAD_CD where USERID=?"
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        if not result:
            self._create_user(user_id)
            result = (user_id, 0, 0, 0, 0, 0)
        self.conn.commit()
        return result[action.value + 1]

    @type_assert(object, "user_id", Action, int)
    def cd_reduce_action(self, user_id: str, action: Action, reduce_time) -> None:
        """单次剪短cd，单位为秒"""
        op_key = self.CD_COLUMN[action.value]
        sql = f"update BREAD_CD set {op_key}=? where USERID=?"
        cur = self.conn.cursor()
        cur.execute(sql, (int(time.time()) - reduce_time, user_id))
        self.conn.commit()

    @type_assert(object, "user_id", Action, int)
    def cd_ban_action(self, user_id: str, action: Action, ban_time) -> None:
        """禁止用户一段时间操作，单次延长cd，单位为秒"""
        op_key = self.CD_COLUMN[action.value]
        sql = f"update BREAD_CD set {op_key}=? where USERID=?"
        cur = self.conn.cursor()
        cur.execute(sql, (int(time.time()) + ban_time, user_id))
        self.conn.commit()

    @type_assert(object, "user_id", Action)
    def cd_update_stamp(self, user_id: str, action: Action) -> None:
        """重置用户操作CD(重新开始记录冷却)"""
        op_key = self.CD_COLUMN[action.value]
        sql = f"update BREAD_CD set {op_key}=? where USERID=?"
        stamp = int(time.time())
        cur = self.conn.cursor()
        cur.execute(sql, (stamp, user_id))
        self.conn.commit()

    @type_assert(object, "user_id", int, Action)
    def add_bread(self, user_id: str, add_num: int, action: Action = Action.BUY) -> int:
        """添加用户面包数量，可以添加已经吃了的面包数量，返回增加后的数量"""
        if action == Action.EAT:
            col_name = self.DATA_COLUMN[1]
        else:
            col_name = self.DATA_COLUMN[0]
        cur = self.conn.cursor()
        sql = f"select * from BREAD_DATA where USERID=?"
        cur.execute(sql, (user_id,))
        data = cur.fetchone()
        if not data:
            self._create_user(user_id)
            data = (0, user_id, 0, 0)
        if col_name == self.DATA_COLUMN[1]:
            ori_num = data[3]
        else:
            ori_num = data[2]
        new_num = ori_num + add_num
        sql = f"update BREAD_DATA set {col_name}=? where USERID=?"
        cur.execute(sql, (new_num, user_id))
        self.conn.commit()
        return new_num

    @type_assert(object, "user_id", int, Action)
    def reduce_bread(self, user_id: str, red_num: int, action: Action = Action.BUY) -> int:
        """减少用户面包数量，可以减少已经吃的数量，返回减少后的数量"""
        if action == Action.EAT:
            col_name = self.DATA_COLUMN[1]
        else:
            col_name = self.DATA_COLUMN[0]
        cur = self.conn.cursor()
        sql = "select * from BREAD_DATA where USERID=?"
        cur.execute(sql, (user_id,))
        data = cur.fetchone()
        if not data:
            self._create_user(user_id)
            data = (0, user_id, 0, 0)
        if col_name == "BREAD_EATEN":
            ori_num = data[3]
        else:
            ori_num = data[2]
        new_num = ori_num - red_num
        sql = f"update BREAD_DATA set {col_name}=? where USERID=?"
        cur.execute(sql, (new_num, user_id))
        self.conn.commit()
        return new_num

    @type_assert(object, "user_id")
    def update_no(self, user_id: str) -> int:
        """更新用户排名并返回"""
        cur = self.conn.cursor()
        sql = "select * from BREAD_DATA where USERID=?"
        cur.execute(sql, (user_id,))
        data = cur.fetchone()
        now_no = data[0]
        user_num = (data[3] // LEVEL, data[2])
        while now_no != 1:
            cur.execute("select * from BREAD_DATA where NO=?", (now_no - 1,))
            data = cur.fetchone()
            up_num = (data[3] // LEVEL, data[2])
            if user_num > up_num:
                cur.execute(f"update BREAD_DATA set NO={0} where NO={now_no}")
                cur.execute(f"update BREAD_DATA set NO={now_no} where NO={now_no - 1}")
                cur.execute(f"update BREAD_DATA set NO={now_no - 1} where NO={0}")
            else:
                break
            now_no -= 1
        while now_no != self._get_id() - 1:
            cur.execute("select * from BREAD_DATA where NO=?", (now_no + 1,))
            data = cur.fetchone()
            down_num = (data[3] // LEVEL, data[2])
            if user_num < down_num:
                cur.execute("update BREAD_DATA set NO=? where NO=?", (0, now_no))
                cur.execute("update BREAD_DATA set NO=? where NO=?", (now_no, now_no + 1))
                cur.execute("update BREAD_DATA set NO=? where NO=?", (now_no + 1, 0))
            else:
                break
            now_no += 1
        self.conn.commit()
        return now_no

    @type_assert(object, "user_id")
    def get_bread_data(self, user_id: str) -> BreadData:
        """获取用户面包数据并返回"""
        cur = self.conn.cursor()
        cur.execute("select * from BREAD_DATA where USERID=?", (user_id,))
        data = cur.fetchone()
        if not data:
            self._create_user(user_id)
            data = (0, user_id, 0, 0)
        self.conn.commit()
        return BreadData(*data, level=data[3] // LEVEL)

    def get_all_data(self) -> List[BreadData]:
        """获取一个数据库内的所有用户数据"""
        cur = self.conn.cursor()
        cur.execute(f"select * from BREAD_DATA")
        data = cur.fetchall()
        self.conn.commit()
        return [BreadData(*item, level=item[3] // LEVEL) for item in data]

    @type_assert(object, "user_id", Action)
    def add_user_log(self, user_id: str, action: Action) -> int:
        """记录用户操作次数递增1并返回"""
        op_key = self.LOG_COLUMN[action.value]
        cur = self.conn.cursor()
        cur.execute("select * from BREAD_LOG where USERID=?", (user_id,))
        data = cur.fetchone()
        log_times = data[action.value + 1]
        log_times += 1
        cur.execute(f"update BREAD_LOG set {op_key}=? where USERID=?", (log_times, user_id))
        self.conn.commit()
        return log_times

    @type_assert(object, "user_id", Action)
    def reduce_user_log(self, user_id: str, action: Action) -> int:
        """记录用户操作次数递减1并返回"""
        op_key = self.LOG_COLUMN[action.value]
        cur = self.conn.cursor()
        cur.execute("select * from BREAD_LOG where USERID=?", (user_id,))
        data = cur.fetchone()
        log_times = data[action.value + 1]
        log_times -= 1
        cur.execute(f"update BREAD_LOG set {op_key}=? where USERID=?", (log_times, user_id))
        self.conn.commit()
        return log_times

    @type_assert(object, "user_id")
    def get_log_data(self, user_id: str) -> LogData:
        """获取用户操作次数记录数据"""
        cur = self.conn.cursor()
        cur.execute(f"select * from BREAD_LOG where USERID=?", (user_id,))
        data = cur.fetchone()
        self.conn.commit()
        return LogData(*data)

    @type_assert(object, Action)
    def get_action_log(self, action: Action) -> LogData:
        """获取某个操作次数最多用户的数据"""
        col = self.LOG_COLUMN[action.value]
        cur = self.conn.cursor()
        sql = f"SELECT * FROM BREAD_LOG WHERE {col}= (SELECT MAX({col}) FROM BREAD_LOG) LIMIT 1;"
        cur.execute(sql)
        data = cur.fetchone()
        self.conn.commit()
        return LogData(*data)


if __name__ == "__main__":
    DATABASE = Path() / ".." / ".." / ".." / "data" / "bread"
