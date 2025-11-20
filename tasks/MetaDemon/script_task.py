# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import time

import random
from datetime import datetime
from module.atom.image import RuleImage

from tasks.Component.GeneralBattle.general_battle import GeneralBattle
from tasks.Component.SwitchSoul.switch_soul import SwitchSoul
from tasks.GameUi.game_ui import GameUi
from tasks.MetaDemon.config import MetaDemon, BossType
from tasks.MetaDemon.assets import MetaDemonAssets
import tasks.MetaDemon.inner_page as ipages

from module.logger import logger
from module.exception import TaskEnd


class ScriptTask(GeneralBattle, SwitchSoul, GameUi, MetaDemonAssets):
    """超鬼王"""

    class State:
        done: bool = False
        switch_soul_done: bool = False

    conf: MetaDemon = None
    cur_boss_type: BossType = None
    total_count: int = 0

    @property
    def enable_powerful_fire(self):
        powerful_list = self.conf.meta_demon_config.powerful_list_v
        return self.cur_boss_type is not None and self.cur_boss_type in powerful_list

    def before_run(self):
        self.ui_close.append(self.I_MD_GET_YESTERDAY_REWARD)
        self.conf = self.config.meta_demon
        self.limit_time = self.conf.meta_demon_config.limit_time_v
        self.limit_count = self.conf.meta_demon_config.limit_count
        # 更改式神录跳转
        ipages.page_shikigami_records.links.clear()
        ipages.page_shikigami_records.link(button=self.I_BACK_Y, destination=ipages.page_meta_demon_boss)
        ipages.page_meta_demon_boss.link(button=MetaDemonAssets.I_MD_SHIKIGAMI, destination=ipages.page_shikigami_records)
        del ipages.page_main.links[ipages.page_shikigami_records]

    def run(self):
        self.before_run()
        self.ui_goto_page(ipages.page_meta_demon_boss)
        while True:
            self.update_global_state()
            if self.State.done:
                break
            self.screenshot()
            current_page = self.ui_get_current_page()
            match current_page:
                case ipages.page_meta_demon:
                    self.ui_goto_page(ipages.page_meta_demon_boss)
                case ipages.page_meta_demon_boss:
                    if self.check_and_prepare_battle():
                        self.start_battle()
                case ipages.page_battle:
                    self.battle_wait(self.conf.general_battle.random_click_swipt_enable)
                case ipages.page_reward | ipages.page_failed:
                    self.click(ipages.random_click(), interval=0.6)
                case _:
                    time.sleep(random.uniform(0.7, 1.4))
        self.set_next_run(task="MetaDemon", success=True)
        self.finish_task()

    def start_battle(self):
        logger.hr('Click fire, start battle')
        while True:
            self.screenshot()
            if self.is_in_battle(False):
                self.total_count += 1
                self.run_general_battle(self.conf.switch_soul.get_general_battle_conf(self.cur_boss_type))
                break
            if self.appear(self.I_MD_DRINK_TEA, interval=1.2):  # 出现喝茶弹窗
                if self.conf.meta_demon_config.auto_tea:
                    self.click(self.I_MD_DRINK_TEA)  # 喝茶
                    continue
                # 不喝茶则结束任务安排下一次运行
                self.ui_click_until_disappear(self.I_MD_CLOSE_POPUP, interval=0.6)
                self.set_next_run('MetaDemon', target=datetime.now() + self.conf.scheduler.wait_interval)
                self.finish_task()
            if self.appear_then_click(self.I_MD_FIRE, interval=0.8):
                continue

    def battle_wait(self, random_click_swipt_enable: bool) -> bool:
        self.device.stuck_record_add('BATTLE_STATUS_S')
        self.device.click_record_clear()
        logger.info(f"Start battle process on {self.cur_boss_type.name if self.cur_boss_type else 'None'}")
        win = False
        while True:
            self.screenshot()
            if self.appear(self.I_MD_SUMMON_BOSS, interval=0.8) or \
                    self.appear(self.I_MD_SWITCH_TICKET, interval=0.8) or \
                    self.appear(self.I_MD_FIRE, interval=0.8):
                break
            if self.appear(self.I_WIN, interval=0.8):
                win = True
                self.click(ipages.random_click())
                continue
            if self.appear(self.I_FALSE, interval=0.8):
                win = False
                self.click(ipages.random_click())
                continue
            if self.appear(self.I_MD_SETTLING, interval=3.5):
                logger.info('wait result')
                time.sleep(random.uniform(3, 5))
                continue
        total_run_time = datetime.now() - self.start_time
        logger.info(f'battle win: {win}')
        logger.info(f'battle count: {self.total_count}/{self.limit_count}')
        logger.info(f'time count: {total_run_time.total_seconds():.1f}s/{self.limit_time.total_seconds()}s')
        return win

    def update_global_state(self):
        if datetime.now() - self.start_time >= self.limit_time or \
                self.total_count >= self.limit_count:
            self.State.done = True

    def check_and_prepare_battle(self) -> bool:
        """检查并做战斗前的准备工作
        :return: True可以战斗, False不能战斗
        """
        logger.hr('battle prepare', 2)
        return self.check_and_switch_ticket() and self.check_and_switch_powerful() and self.check_and_switch_soul()

    def check_and_switch_ticket(self):
        """切换鬼王门票"""
        logger.hr('Summon boss')
        # 打开切换门票弹窗
        while True:
            self.screenshot()
            if self.appear(self.I_MD_FIRE, interval=1.2):  # 可以直接挑战鬼王则退出
                return True
            if self.appear(self.I_MD_GET_BOSS, interval=0.6):  # 打开弹窗了
                break
            if self.appear_then_click(self.I_MD_SWITCH_TICKET, interval=0.6):
                continue
        type_ticket_dict: dict[BossType, RuleImage] = {
            BossType.ONE_STAR: self.I_MD_ONE_STAR,
            BossType.TWO_STARS: self.I_MD_TWO_STARS,
            BossType.THREE_STARS: self.I_MD_THREE_STARS,
            BossType.FOUR_STARS: self.I_MD_FOUR_STARS,
            BossType.FIVE_STARS: self.I_MD_FIVE_STARS,
            BossType.SIX_STARS: self.I_MD_SIX_STARS,
        }
        # 获取所有存在的鬼王门票
        can_fire_list = [boss_type for boss_type, ticket_rule_image in type_ticket_dict.items() if
                         self.appear(ticket_rule_image)]
        if len(can_fire_list) <= 0:
            self.State.done = True
            logger.info('No remain boss ticket, exit')
            self.ui_click_until_disappear(self.I_MD_CLOSE_POPUP, interval=0.6)
            return False
        # 根据存在的鬼王门票和配置的鬼王序列过滤出需要召唤的鬼王门票
        need_fire_list = [boss_type for boss_type in self.conf.meta_demon_config.fire_sequence_v if
                          boss_type in can_fire_list]
        if len(need_fire_list) <= 0:
            self.State.done = True
            logger.info('There is no boss that needs to be attacked, exit')
            self.ui_click_until_disappear(self.I_MD_CLOSE_POPUP, interval=0.6)
            return False
        # 第一次进来或上次一鬼王类型与这一次不同, 则需要切换御魂和预设
        if self.cur_boss_type is None or self.cur_boss_type != need_fire_list[0]:
            if not self.conf.switch_soul.switch_once:
                self.State.switch_soul_done = False
            self.current_count = 0
        self.cur_boss_type = need_fire_list[0]
        target_ticket_rule_image = type_ticket_dict[self.cur_boss_type]
        selected = False
        logger.info(f'Summon {self.cur_boss_type.name.lower()} boss')
        while True:
            self.screenshot()
            if self.appear(self.I_MD_FIRE):  # 可以挑战鬼王则退出
                return True
            if selected and self.appear(self.I_MD_CHECK_SELECTED, interval=0.6):
                selected_x, selected_y = self.I_MD_CHECK_SELECTED.coord()
                x, y, w, h = target_ticket_rule_image.roi_front
                if x <= selected_x <= x + w:  # 确定选中目标鬼王门票, 召唤鬼王
                    self.ui_click_until_disappear(self.I_MD_GET_BOSS, interval=0.6)
                    continue
            if self.appear_then_click(target_ticket_rule_image, interval=0.6):  # 选择对应鬼王门票
                selected = True
                continue
        return False

    def check_and_switch_powerful(self) -> bool:
        """检查并切换是否开启强力"""
        logger.hr('process power fire')
        if not self.appear(self.I_MD_FIRE):
            self.ui_goto_page(ipages.page_meta_demon_boss)
            self.screenshot()
            if not self.appear(self.I_MD_FIRE):  # 处于boss界面但是没有挑战按钮
                return False
        powerful_list = self.conf.meta_demon_config.powerful_list_v
        # 当前boss类型未知或不在强力列表中则使用普通追击
        if self.cur_boss_type is None or self.cur_boss_type not in powerful_list:
            self.ui_click(self.I_MD_ENABLE_POWERFUL_FIRE, self.I_MD_DISABLE_POWERFUL_FIRE, interval=0.6)
            return True
        # 已知类型且在强力列表中则开启强力追击
        self.ui_click(self.I_MD_DISABLE_POWERFUL_FIRE, self.I_MD_ENABLE_POWERFUL_FIRE, interval=0.6)
        return True

    def check_and_switch_soul(self) -> bool:
        """切换御魂"""
        if self.State.switch_soul_done:
            return True
        logger.hr('Switch soul')
        self.State.switch_soul_done = True
        self.ui_goto_page(ipages.page_shikigami_records)
        if self.conf.switch_soul.switch_once:  # 只切换一次则将配置的鬼王御魂全部切换
            for boss_type in self.conf.meta_demon_config.fire_sequence_v:
                switch_type, (group, team) = self.conf.switch_soul.get_switch_by_enum(boss_type)
                if switch_type is None:
                    continue
                if switch_type == 'int':
                    self.run_switch_soul((group, team))
                if switch_type == 'str':
                    self.run_switch_soul_by_name(group, team)
            self.ui_goto_page(ipages.page_meta_demon_boss)
            return True
        # 当前鬼王类型未知, 无法切换御魂
        if self.cur_boss_type is None:
            logger.error(f'cur_boss_type is None')
            self.ui_goto_page(ipages.page_meta_demon_boss)
            return False
        switch_type, (group, team) = self.conf.switch_soul.get_switch_by_enum(self.cur_boss_type)
        if switch_type is None:
            logger.error(f'Switch soul format is invalid on {self.cur_boss_type.name.lower()}')
            self.ui_goto_page(ipages.page_meta_demon_boss)
            return False
        if switch_type == 'int':
            self.run_switch_soul((group, team))
        if switch_type == 'str':
            self.run_switch_soul_by_name(group, team)
        self.ui_goto_page(ipages.page_meta_demon_boss)
        return True

    def finish_task(self):
        # 恢复式神录跳转
        del ipages.page_meta_demon_boss.links[ipages.page_shikigami_records]
        ipages.page_main.link(button=self.I_MAIN_GOTO_SHIKIGAMI_RECORDS, destination=ipages.page_shikigami_records)
        ipages.page_shikigami_records.link(button=self.I_BACK_Y, destination=ipages.page_main)
        self.ui_goto_page(ipages.page_main)
        raise TaskEnd


if __name__ == '__main__':
    from module.config.config import Config
    from module.device.device import Device

    c = Config('oas1')
    d = Device(c)
    t = ScriptTask(c, d)

    t.run()
