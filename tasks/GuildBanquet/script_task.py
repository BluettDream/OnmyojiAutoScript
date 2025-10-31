# This Python file uses the following encoding: utf-8
# @author ohspecial
# github https://github.com/ohspecial
from datetime import datetime, timedelta
import time

from module.exception import TaskEnd
from module.logger import logger
from module.base.timer import Timer

from tasks.GameUi.game_ui import GameUi
from tasks.GameUi.page import page_guild, page_main
from tasks.GuildBanquet.assets import GuildBanquetAssets
from tasks.GuildBanquet.config import Weekday


class ScriptTask(GameUi, GuildBanquetAssets):

    def run(self):
        banquet_time = self.config.guild_banquet.guild_banquet_time
        # 宴会日1的星期下标
        banquet_day_1 = list(Weekday).index(Weekday(banquet_time.day_1.value))
        # 宴会日2的星期下标
        banquet_day_2 = list(Weekday).index(Weekday(banquet_time.day_2.value))

        if datetime.now().weekday() not in [banquet_day_1, banquet_day_2]:
            logger.info('Today is not guild banquet day, exit')
            self.plan_next_run([banquet_day_1, banquet_day_2])
            self.ui_goto_page(page_main)
            raise TaskEnd

        self.ui_goto_page(page_guild)

        def guild_start() -> bool:
            self.screenshot()
            self.ui_goto_page(page_guild)
            if self.appear(self.I_FLAG):
                return True
            self.ui_goto(page_main)
            logger.info('Waiting for guild banquet start')
            return False

        if not self.wait_until(guild_start, timeout=self.config.guild_banquet.scheduler.max_wait_time * 60,
                               interval=(50, 70)):
            logger.warning('Wait for guild banquet start timeout')
            self.plan_next_run([banquet_day_1, banquet_day_2])
            self.ui_goto_page(page_main)
            raise TaskEnd

        wait_count = 0
        wait_timer = Timer(230)
        wait_timer.start()
        logger.info("Start guild banquet!")
        self.device.stuck_record_add('BATTLE_STATUS_S')

        last_check_time = 0  # 记录上次实际检测时间
        last_log_time = 0  # 记录上次日志输出时间
        last_flag_status = False  # 记录上次真实检测结果

        while True:
            self.screenshot()
            # 条件1: 强制检测间隔管理
            current_time = time.time()
            if current_time - last_check_time >= 10:
                # 达到间隔要求时执行真实检测
                actual_status = self.appear(self.I_FLAG)
                last_flag_status = actual_status
                last_check_time = current_time
                logger.debug(f"Actual detection at {current_time}, status: {actual_status}")
                
                # 重置日志计时器
                last_log_time = current_time
            else:
                # 未达间隔时沿用上次结果
                logger.debug(f"Using cached status: {last_flag_status}")

            # 条件2: 状态判断逻辑
            if last_flag_status:
                if current_time - last_log_time >= 10:
                    logger.info("Banquet ongoing, waiting...")
                    last_log_time = current_time
            else:
                logger.info("Guild banquet end")
                break  # 退出循环

            # 条件3: 超时保护
            if wait_timer.reached():
                wait_timer.reset()
                if wait_count >= 3:
                    # 宴会最长15分钟
                    logger.info('Guild banquet timeout')
                    break
                wait_count += 1
                logger.info(f'Banquet ongoing, waiting... (Count: {wait_count})')
                self.device.stuck_record_clear()
                self.device.stuck_record_add('BATTLE_STATUS_S')
        self.device.stuck_record_clear()
        self.plan_next_run([banquet_day_1, banquet_day_2])
        self.ui_goto_page(page_main)
        raise TaskEnd

    def plan_next_run(self, day_list: list[int] = None):
        today_weekday = datetime.now().weekday()
        # 计算距离今天的天数差并排序
        days_ahead = sorted(((day_of_week - today_weekday + 7) % 7 for day_of_week in day_list))
        non_zero_days = [d for d in days_ahead if d != 0]
        # 如果过滤后还有未来的日期，取最小的那个；否则全部是今天则+7天
        delta_days = non_zero_days[0] if non_zero_days else 7
        logger.info(f"Plan next run: {(self.start_time + timedelta(days=delta_days)).strftime('%Y-%m-%d')}")
        self.custom_next_run(task='GuildBanquet', custom_time=self.start_time, time_delta=delta_days)


if __name__ == '__main__':
    from module.config.config import Config
    from module.device.device import Device
    c = Config('oas1')
    d = Device(c)
    t = ScriptTask(c, d)
    t.run()
