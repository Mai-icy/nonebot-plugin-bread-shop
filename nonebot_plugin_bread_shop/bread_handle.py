#!/usr/bin/python
# -*- coding:utf-8 -*-
import sqlite3
import time
from enum import Enum
from pathlib import Path
from typing import List
from collections import namedtuple

DATABASE = Path() / "data" / "bread"


class Action(Enum):
    BUY = 0
    EAT = 1
    ROB = 2
    GIVE = 3
    BET = 4


BreadData = namedtuple("BreadData", ["no", "user_id", "bread_num", "bread_eaten", "level"])
LogData = namedtuple("LogData", ["user_id", "buy_times", "eat_times", "rob_times", "give_times", "bet_times"])


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
                self.database_path.mkdir()
                self.database_path /= "bread.db"
                self.conn = sqlite3.connect(self.database_path)
                self._create_file()
            else:
                self.database_path /= "bread.db"
                self.conn = sqlite3.connect(self.database_path)
            print("数据库连接！")

    def __del__(self):
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

    def _create_user(self, user_id: str) -> None:
        """在数据库中创建用户并初始化"""
        new_id = self._get_id()
        c = self.conn.cursor()
        c.execute(f"INSERT INTO BREAD_DATA (NO,USERID,BREAD_NUM,BREAD_EATEN) VALUES ({new_id},'{user_id}',0,0)")
        c.execute(f"INSERT INTO BREAD_LOG (USERID,BUY_TIMES,EAT_TIMES,ROB_TIMES,GIVE_TIMES,BET_TIMES)"
                  f" VALUES ('{user_id}',0,0,0,0,0)")
        c.execute(f"INSERT INTO BREAD_CD (USERID,BUY_CD,EAT_CD,ROB_CD,GIVE_CD,BET_CD)"
                  f" VALUES ('{user_id}',0,0,0,0,0)")
        self.conn.commit()

    def cd_refresh(self, user_id: str, action: Action) -> None:
        """刷新用户操作cd"""
        if not isinstance(action, Action):
            raise KeyError("the parameter operate must be Operate")
        op_key = self.CD_COLUMN[action.value]
        cur = self.conn.cursor()
        cur.execute(f"update BREAD_CD set {op_key}={1} where USERID='{user_id}'")
        self.conn.commit()

    def cd_get_stamp(self, user_id: str, action: Action) -> int:
        """获取用户上次操作时间戳"""
        if not isinstance(action, Action):
            raise KeyError("the parameter operate must be Operate")
        cur = self.conn.cursor()
        cur.execute(f"select * from BREAD_CD where USERID={user_id}")
        result = cur.fetchone()
        if not result:
            self._create_user(user_id)
            result = (user_id, 0, 0, 0, 0, 0)
        self.conn.commit()
        return result[action.value + 1]

    def cd_ban_action(self, user_id: str, action: Action, ban_time) -> None:
        """禁止用户一段时间操作，单次延长cd，单位为秒"""
        if not isinstance(action, Action):
            raise KeyError("the parameter operate must be Operate")
        op_key = self.CD_COLUMN[action.value]
        cur = self.conn.cursor()
        cur.execute(f"update BREAD_CD set {op_key}={int(time.time()) + ban_time} where USERID={user_id}")
        self.conn.commit()

    def cd_update_stamp(self, user_id: str, action: Action) -> None:
        """重置用户操作CD(重新开始记录冷却)"""
        if not isinstance(action, Action):
            raise KeyError("the parameter operate must be Operate")
        op_key = self.CD_COLUMN[action.value]
        stamp = int(time.time())
        cur = self.conn.cursor()
        cur.execute(f"update BREAD_CD set {op_key}={stamp} where USERID='{user_id}'")
        self.conn.commit()

    def add_bread(self, user_id: str, add_num: int, action: Action = Action.BUY) -> int:
        """添加用户面包数量，可以添加已经吃了的面包数量，返回增加后的数量"""
        if action == Action.EAT:
            col_name = self.DATA_COLUMN[1]
        else:
            col_name = self.DATA_COLUMN[0]
        cur = self.conn.cursor()
        cur.execute(f"select * from BREAD_DATA where USERID='{user_id}'")
        data = cur.fetchone()
        if not data:
            self._create_user(user_id)
            data = (0, user_id, 0, 0, 0, 0)
        if col_name == self.DATA_COLUMN[1]:
            ori_num = data[3]
        else:
            ori_num = data[2]
        new_num = ori_num + add_num
        cur.execute(f"update BREAD_DATA set {col_name}={new_num} where USERID='{user_id}'")
        self.conn.commit()
        return new_num

    def reduce_bread(self, user_id: str, red_num: int, action: Action = Action.BUY) -> int:
        """减少用户面包数量，可以减少已经吃的数量，返回减少后的数量"""
        if action == Action.EAT:
            col_name = self.DATA_COLUMN[1]
        else:
            col_name = self.DATA_COLUMN[0]
        cur = self.conn.cursor()
        cur.execute(f"select * from BREAD_DATA where USERID='{user_id}'")
        data = cur.fetchone()
        if not data:
            self._create_user(user_id)
            data = (0, user_id, 0, 0, 0, 0)
        if col_name == "BREAD_EATEN":
            ori_num = data[3]
        else:
            ori_num = data[2]
        new_num = ori_num - red_num
        cur.execute(f"update BREAD_DATA set {col_name}={new_num} where USERID='{user_id}'")
        self.conn.commit()
        return new_num

    def update_no(self, user_id: str) -> int:
        """更新用户排名并返回"""
        cur = self.conn.cursor()
        cur.execute(f"select * from BREAD_DATA where USERID='{user_id}'")
        data = cur.fetchone()
        now_no = data[0]
        user_num = (data[3] // 10, data[2])
        while now_no != 1:
            cur.execute(f"select * from BREAD_DATA where NO={now_no - 1}")
            data = cur.fetchone()
            up_num = (data[3] // 10, data[2])
            if user_num > up_num:
                cur.execute(f"update BREAD_DATA set NO={0} where NO={now_no}")
                cur.execute(f"update BREAD_DATA set NO={now_no} where NO={now_no - 1}")
                cur.execute(f"update BREAD_DATA set NO={now_no - 1} where NO={0}")
            else:
                break
            now_no -= 1
        while now_no != self._get_id() - 1:
            cur.execute(f"select * from BREAD_DATA where NO={now_no + 1}")
            data = cur.fetchone()
            down_num = (data[3] // 10, data[2])
            if user_num < down_num:
                cur.execute(f"update BREAD_DATA set NO={0} where NO={now_no}")
                cur.execute(f"update BREAD_DATA set NO={now_no} where NO={now_no + 1}")
                cur.execute(f"update BREAD_DATA set NO={now_no + 1} where NO={0}")
            else:
                break
            now_no += 1
        self.conn.commit()
        return now_no

    def get_bread_data(self, user_id: str) -> BreadData:
        """获取用户面包数据并返回"""
        cur = self.conn.cursor()
        cur.execute(f"select * from BREAD_DATA where USERID='{user_id}'")
        data = cur.fetchone()
        self.conn.commit()
        return BreadData(*data, level=(data[3] // 10))

    def get_all_data(self) -> List[BreadData]:
        """获取一个数据库内的所有用户数据"""
        cur = self.conn.cursor()
        cur.execute(f"select * from BREAD_DATA")
        data = cur.fetchall()
        self.conn.commit()
        return [BreadData(*item, level=item[3] // 10) for item in data]

    def log_user_action(self, user_id: str, action: Action) -> int:
        """记录用户操作次数递增1并返回"""
        if not isinstance(action, Action):
            raise KeyError("the parameter operate must be Operate")
        op_key = self.LOG_COLUMN[action.value]
        cur = self.conn.cursor()
        cur.execute(f"select * from BREAD_LOG where USERID='{user_id}'")
        data = cur.fetchone()
        log_times = data[action.value + 1]
        log_times += 1
        cur.execute(f"update BREAD_LOG set {op_key}={log_times} where USERID={user_id}")
        self.conn.commit()
        return log_times

    def get_log_data(self, user_id: str):
        cur = self.conn.cursor()
        cur.execute(f"select * from BREAD_LOG where USERID='{user_id}'")
        data = cur.fetchone()
        self.conn.commit()
        return LogData(*data)

    def get_action_log(self, action: Action):
        col = self.LOG_COLUMN[action.value]
        cur = self.conn.cursor()
        cur.execute(f"SELECT * FROM BREAD_LOG WHERE {col}= (SELECT MAX({col}) FROM BREAD_LOG) LIMIT 1;")
        data = cur.fetchone()
        self.conn.commit()
        return LogData(*data)


if __name__ == "__main__":
    DATABASE = Path() / ".." / ".." / ".." / "data" / "bread"
    db = BreadDataManage("893015705")
    print(db.get_action_log(Action.EAT))
    pass
