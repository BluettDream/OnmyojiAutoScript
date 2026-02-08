# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import string

from pydantic import BaseModel, Field

from tasks.Restart.config_scheduler import RestartScheduler
from tasks.Component.config_base import ConfigBase, DateTime, MultiLine


class TasksReset(BaseModel):
    reset_task_datetime_enable: bool = Field(default=False, description='reset_task_datetime_enable_help')
    reset_task_datetime: DateTime = Field(default="2023-01-01 00:00:00", description='rest_task_datetime_help')


class LoginCharacterConfig(BaseModel):
    # 同账号同服务器多个角色时,需要登录的角色名/服务器名
    character: str = Field(default="")


class Restart(ConfigBase):
    scheduler: RestartScheduler = Field(default_factory=RestartScheduler)
    tasks_config_reset: TasksReset = Field(default_factory=TasksReset)
    login_character_config: LoginCharacterConfig = Field(default_factory=LoginCharacterConfig)
