# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from datetime import datetime
from pydantic import BaseModel, Field

from tasks.Component.config_scheduler import Scheduler
from tasks.Component.config_base import ConfigBase, dynamic_hide, DateTime
from enum import Enum


class SummonType(str, Enum):
    default = '普通召唤'
    recall = '今忆召唤'


class DoneRecord(ConfigBase):
    courtyard_affairs_dt: DateTime = Field(default=DateTime.fromisoformat("2023-01-01 00:00:00"))
    pickup_email_dt: DateTime = Field(default=DateTime.fromisoformat("2023-01-01 00:00:00"))
    summon_dt: DateTime = Field(default=DateTime.fromisoformat("2023-01-01 00:00:00"))
    guild_wish_dt: DateTime = Field(default=DateTime.fromisoformat("2023-01-01 00:00:00"))
    luck_msg_dt: DateTime = Field(default=DateTime.fromisoformat("2023-01-01 00:00:00"))
    store_sign_dt: DateTime = Field(default=DateTime.fromisoformat("2023-01-01 00:00:00"))
    sushi_dt: DateTime = Field(default=DateTime.fromisoformat("2023-01-01 00:00:00"))


class DailyTriflesConfig(BaseModel):
    # 庭院事务
    courtyard_affairs: bool = Field(default=True)
    # 收取邮件
    pickup_email: bool = Field(default=True)
    one_summon: bool = Field(title='One Summon', default=False)
    # 召唤类型
    summon_type: SummonType = Field(default=SummonType.default, description='召唤类型')
    # 是否绘制神秘图案
    draw_mystery_pattern: bool = Field(title='Draw Mystery Pattern', default=False, description='是否绘制神秘图案')
    guild_wish: bool = Field(title='Guild Wish', default=False)
    luck_msg: bool = Field(title='Luck Msg', default=False)
    store_sign: bool = Field(title='Store Sign', default=False, description='store_sign_help')
    # 每天购买体力数量
    buy_sushi_count: int = Field(title='Buy Sushi Count', default=-1)

    hide_fields = dynamic_hide('draw_mystery_pattern')


class DailyTrifles(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    trifles_config: DailyTriflesConfig = Field(default_factory=DailyTriflesConfig)
    done_record: DoneRecord = Field(default_factory=DoneRecord)

    hide_fields = dynamic_hide('done_record')

    def today_is_done(self, mode: str) -> bool:
        """对应mode今天是否已经完成"""
        done_dt = getattr(self.done_record, f'{mode}_dt', None)
        if done_dt is None:
            return False
        return done_dt.date() == datetime.today().date()
