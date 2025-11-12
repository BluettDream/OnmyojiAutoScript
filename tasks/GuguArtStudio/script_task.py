# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import time

import random
from module.base.timer import Timer
from module.exception import TaskEnd
from module.logger import logger
from tasks.Component.GeneralBattle.general_battle import GeneralBattle
from tasks.Component.SwitchSoul.switch_soul import SwitchSoul
from tasks.GameUi.game_ui import GameUi
import tasks.GameUi.page as pages
from tasks.GuguArtStudio.assets import GuguArtStudioAssets
from tasks.GuguArtStudio.config import GuguArtStudio
from tasks.Restart.assets import RestartAssets

""" 灵染 试炼 """


class ScriptTask(GeneralBattle, GameUi, SwitchSoul, GuguArtStudioAssets):
    conf: GuguArtStudio = None

    def before_run(self):
        pages.page_gugu_act = pages.Page(self.I_CHECK_GUGU_ACT)
        pages.page_gugu_act.link(button=self.I_BACK_Y, destination=pages.page_main)
        pages.page_act_list_gugu_act.link(button=self.I_ACT_LIST_GOTO_ACT, destination=pages.page_gugu_act)

    def run(self):
        self.before_run()
        self.conf = self.config.gugu_art_studio
        self.switch_soul()
        self.ui_goto_page(pages.page_gugu_act)
        self.get_paint()
        self.submit_paint()
        self.ui_goto_page(pages.page_main)
        self.set_next_run(task='GuguArtStudio', success=True, finish=True)
        raise TaskEnd('GuguArtStudio')

    def switch_soul(self):
        """切换御魂"""
        if self.conf.switch_soul_config.enable:
            self.ui_goto_page(pages.page_shikigami_records)
            self.run_switch_soul(self.conf.switch_soul_config.switch_group_team)
        if self.conf.switch_soul_config.enable_switch_by_name:
            self.ui_goto_page(pages.page_shikigami_records)
            self.run_switch_soul_by_name(self.conf.switch_soul_config.group_name,
                                         self.conf.switch_soul_config.team_name)

    def get_paint(self):
        can_fire = False
        while True:
            self.screenshot()
            if self.appear(self.I_GAS_CANNOT_FIRE, interval=0.8):
                break
            if self.appear(self.I_GAS_CAN_FIRE, interval=0.8):
                can_fire = True
                break
            self.ui_click_until_disappear(self.I_OBTAIN_PAINT, interval=1.2)
        if not can_fire:
            logger.info('Cannot fire, not need to get paint')
            return
        while True:
            self.screenshot()
            if self.appear(self.I_SUBMIT_PAINT, interval=0.8):
                break
            if self.appear(self.I_GAS_CANNOT_FIRE, interval=0.8):
                self.ui_click(self.I_BACK_Y, self.I_SUBMIT_PAINT, interval=2.5)
                continue
            if self.appear_then_click(self.I_GOTO_SUBMIT, interval=0.8):
                break
            if self.appear_then_click(self.I_GAS_CAN_FIRE, interval=0.8):
                self.run_general_battle()

    def submit_paint(self):
        self.ui_goto_page(pages.page_gugu_act)
        cnt, submit_cnt = 0, random.randint(2, 3)
        while True:
            if cnt >= submit_cnt:
                logger.info('Submit paint success')
                break
            self.screenshot()
            if self.appear_then_click(self.I_SUBMIT_PAINT, interval=0.8):
                cnt += 1
                continue


if __name__ == '__main__':
    from module.config.config import Config
    from module.device.device import Device

    c = Config('oas3')
    d = Device(c)
    t = ScriptTask(c, d)
    t.screenshot()

    t.run()
