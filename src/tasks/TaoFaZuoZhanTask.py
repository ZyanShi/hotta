import time
from qfluentwidgets import FluentIcon
from ok import TaskDisabledException
from src.tasks.BaseQRSLTask import BaseQRSLTask


class TaoFaZuoZhanTask(BaseQRSLTask):
    """讨伐作战自动化任务"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "讨伐作战"
        self.description = "碳粉"
        self.group_name = "精炼强化"
        self.group_icon = FluentIcon.SYNC
        self.icon = FluentIcon.GAME

        # 配置项
        self.default_config.update({
            '选择副本': "中层控制室",
            '循环次数': 10000,
            '战斗超时': 300,
        })
        self.config_type["选择副本"] = {'type': "drop_down", 'options': ['中层控制室']}

    def enter_taofa_dungeon(self):
        """进入讨伐作战副本"""
        self.log_info("开始进入讨伐作战副本...")

        if not self.is_main_page():
            self.log_error("不在主页面，无法进入副本")
            return False

        success, attend_box = self.enter_team()
        if not success or not attend_box:
            self.log_error("进入队伍失败")
            return False

        self.log_info("点击'参加'按钮...")
        self.click_box(attend_box, after_sleep=1.5)
        self.log_info("等待5秒...")
        self.sleep(5)
        return self.wait_for_exit_button_white(timeout=30)

    def execute_combat_sequence(self):
        """执行战斗序列"""
        self.log_info("开始执行战斗序列...")
        self.start_auto_combat()
        self.log_info("按A键0.3秒")
        self.send_key('a', down_time=0.3, after_sleep=0.5)
        self.log_info("按W键2.7秒")
        self.send_key('w', down_time=2.7, after_sleep=0.5)
        self.log_info("按F键")
        self.send_key('f', after_sleep=0.5)
        self.log_info("按D键0.8秒")
        self.send_key('d', down_time=0.8, after_sleep=0.5)
        self.log_info("按F键")
        self.send_key('f', after_sleep=0.5)
        self.log_info("战斗序列执行完成")

    def exit_taofa_dungeon(self):
        """退出讨伐作战副本"""
        self.log_info("开始退出副本...")
        self.sleep(4)
        check_x, check_y = self._get_scaled_coordinates(267, 65)
        self.click(check_x, check_y, after_sleep=1)
        self.click(check_x, check_y, after_sleep=1)
        success = self._click_with_alt(check_x, check_y, alt_down_delay=0.8, click_delay=1.5)
        if success:
            self.sleep(10)
            return True
        return False

    def run(self):
        """讨伐作战自动化流程"""
        try:
            self.log_info("===== 讨伐作战任务启动 =====", notify=True)

            max_loops = self.config.get('循环次数', 10000)
            combat_timeout = self.config.get('战斗超时', 300)

            self.log_info(f"配置参数: 循环次数={max_loops}, 战斗超时={combat_timeout}秒")

            loop_count = 0

            while loop_count < max_loops:
                loop_count += 1
                self.log_info(f"--- 第 {loop_count}/{max_loops} 次循环开始 ---")

                # 进入副本
                if not self.enter_taofa_dungeon():
                    self.log_error("进入副本失败，跳过本次循环")
                    self.sleep(5)
                    continue

                # 执行战斗序列
                self.execute_combat_sequence()

                # 等待目标颜色
                if not self.wait_for_target_color(combat_timeout):
                    self.log_error(f"{combat_timeout}秒内未检测到目标颜色，退出副本")
                    if not self.exit_taofa_dungeon():
                        self.log_error("退出副本失败")
                    continue

                # 退出副本
                if not self.exit_taofa_dungeon():
                    self.log_error("退出副本失败")

                # 新增：等待主页颜色，确保回到主页面
                if not self.wait_for_main_page_color(timeout=60):
                    self.log_error("等待主页颜色超时，跳过本次循环")
                    self.sleep(5)
                    continue

                self.log_info(f"第 {loop_count} 次循环完成")

            self.log_info(f"===== 讨伐作战任务结束，共完成 {loop_count} 次循环 =====", notify=True)

        except TaskDisabledException:
            self.log_info("讨伐作战任务被用户手动停止")
        except Exception as e:
            self.log_error(f"任务执行过程中出现异常: {e}", exception=e, notify=True)
            self.screenshot("taofazuozhan_error")
            raise