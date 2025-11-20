# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from datetime import timedelta, time
from tasks.Component.GeneralBattle.config_general_battle import GeneralBattleConfig

from tasks.Component.config_base import ConfigBase, TimeDelta, Time, dynamic_hide
from pydantic import Field
from enum import IntEnum
from tasks.Component.config_scheduler import Scheduler


class BossType(IntEnum):
    ONE_STAR = 1
    TWO_STARS = 2
    THREE_STARS = 3
    FOUR_STARS = 4
    FIVE_STARS = 5
    SIX_STARS = 6
    MONEY = 7


class MetaDemonConfig(ConfigBase):
    limit_time: Time = Field(default=Time(minute=45), description='limit_time_help')
    limit_count: int = Field(default=50, description='limit_count_help')
    auto_tea: bool = Field(default=False, description='疲劳度满时是否自动喝茶, 关闭则自动根据调度器等待间隔时间安排下一次调度')
    fire_sequence: str = Field(default='1 2 3 4', description='攻击顺序:从左到右,空格分隔(1:一星鬼王,2:二星鬼王...)\n例:3 2(先攻击三星鬼王然后二星鬼王)')
    powerful_list: str = Field(default='', description='开启强力鬼王列表(空格分隔),例:4 5(四星鬼王和五星鬼王开启强力追击)')

    @property
    def limit_time_v(self) -> timedelta:
        if isinstance(self.limit_time, time):
            return timedelta(hours=self.limit_time.hour, minutes=self.limit_time.minute, seconds=self.limit_time.second)
        return self.limit_time

    @property
    def fire_sequence_v(self) -> list[BossType]:
        sequence_text = self.fire_sequence.strip()
        if sequence_text == '':
            return []
        fire_num_list = sequence_text.split(' ')
        fire_boss_type_list = [BossType(int(num_text)) for num_text in fire_num_list]
        return fire_boss_type_list

    @property
    def powerful_list_v(self) -> list[BossType]:
        powerful_list_text = self.powerful_list.strip()
        if powerful_list_text == '':
            return []
        powerful_num_list = powerful_list_text.split(' ')
        powerful_boss_type_list = [BossType(int(num_text)) for num_text in powerful_num_list]
        return powerful_boss_type_list


class MetaDemonSwitchSoulConfig(ConfigBase):
    enable: bool = Field(default=False, description='是否启用自动切换御魂,清空则不会切换对应御魂\n若是数字,则以编号方式切换御魂(组号,队伍号),组1-7,队伍1-4\n若非数字,则以ocr方式切换御魂(组名,队伍名)')
    switch_once: bool = Field(default=False, description='启用该项会一次性切换所有需要攻击的鬼王御魂(建议全部独立御魂再启用), 否则当鬼王级别变更时会自动切换对应级别御魂')
    one_star: str = Field(default='', description='一星鬼王切换御魂配置')
    enable_one_star_preset: bool = Field(default=False, description='是否战斗内切换一星鬼王预设,仅限数字切换御魂可用,否则无效,下面同理')
    two_stars: str = Field(default='', description='二星鬼王切换御魂配置')
    enable_two_stars_preset: bool = Field(default=False, description='是否战斗内切换二星鬼王预设')
    three_stars: str = Field(default='', description='三星鬼王切换御魂配置')
    enable_three_stars_preset: bool = Field(default=False, description='是否战斗内切换三星鬼王预设')
    four_stars: str = Field(default='', description='四星鬼王切换御魂配置')
    enable_four_stars_preset: bool = Field(default=False, description='是否战斗内切换四星鬼王预设')
    five_stars: str = Field(default='', description='五星鬼王切换御魂配置')
    enable_five_stars_preset: bool = Field(default=False, description='是否战斗内切换五星鬼王预设')
    six_stars: str = Field(default='', description='六星鬼王切换御魂配置')
    enable_six_stars_preset: bool = Field(default=False, description='是否战斗内切换六星鬼王预设')
    # money: str = Field(default='', description='氪金鬼王切换御魂配置')
    # enable_money_preset: bool = Field(default=False, description='是否切换氪金鬼王预设')

    def get_switch_by_enum(self, boss_type: BossType) -> tuple[str, tuple[str | int, str | int]]:
        """根据枚举获取对应的 切换类型, (group,team)"""
        return self.get_switch_by_name(boss_type.name.lower())

    def get_switch_by_name(self, switch_name: str) -> tuple[str, tuple[str | int, str | int]]:
        """根据名称获取对应的御魂预设"""
        group_team = getattr(self, switch_name, None)
        if group_team is None or group_team.strip() == '' or ',' not in group_team or len(group_team.split(',')) != 2:
            return None, (None, None)
        group, team = group_team.split(',')
        if group.isdigit() and team.isdigit():
            return 'int', (int(group), int(team))
        return 'str', (group, team)

    def get_general_battle_conf(self, boss_type: BossType) -> GeneralBattleConfig:
        """获取通用战斗配置"""
        if boss_type is None:
            return GeneralBattleConfig()
        enable_preset = getattr(self, f'enable_{boss_type.name.lower()}_preset', False)
        if not enable_preset:
            return GeneralBattleConfig()
        switch_type, (group, team) = self.get_switch_by_enum(boss_type)
        if switch_type is None or switch_type == 'str':
            return GeneralBattleConfig()
        if switch_type == 'int':
            return GeneralBattleConfig(lock_team_enable=False, preset_enable=True, preset_group=group, preset_team=team)
        return GeneralBattleConfig()


class MetaDemonScheduler(Scheduler):
    wait_interval: TimeDelta = Field(default=TimeDelta(hours=1, minutes=40), description='疲劳度满时等多长时间后再次运行本任务,建议设置等待完全恢复疲劳度所需的时间\n例:100分钟恢复100点疲劳度,再次运行必定可以继续战斗')

    hide_fields = dynamic_hide('server_update', 'delay_date')


class MetaDemon(ConfigBase):
    scheduler: MetaDemonScheduler = Field(default_factory=MetaDemonScheduler)
    meta_demon_config: MetaDemonConfig = Field(default_factory=MetaDemonConfig)
    switch_soul: MetaDemonSwitchSoulConfig = Field(default_factory=MetaDemonSwitchSoulConfig)
