import time
import re
from qfluentwidgets import FluentIcon
from ok import BaseTask
from src.tasks.BaseQRSLTask import BaseQRSLTask


class TaoFaZuoZhanTask(BaseQRSLTask):
    """讨伐作战自动化任务"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "讨伐作战"
        self.description = "碳粉"
        self.group_name = "精炼强化"
        self.group_icon = FluentIcon.VPN
        self.icon = FluentIcon.SYNC

        # 添加自定义配置
        self.default_config.update({
            '选择副本': "中层控制室",
            '循环次数': 10000,
            '战斗超时': 300,
        })
        self.config_type["选择副本"] = {'type': "drop_down",
                                            'options': ['中层控制室']}

    def enter_taofa_dungeon(self):
        """进入讨伐作战副本"""
        self.log_info("开始进入讨伐作战副本...")

        # 1. 确保在主页面
        if not self.is_main_page():
            self.log_error("不在主页面，无法进入副本")
            return False

        # 2. 进入队伍
        success, attend_box = self.enter_team()
        if not success or not attend_box:
            self.log_error("进入队伍失败")
            return False

        # 3. 等待attend图片并点击
        self.log_info("点击'参加'按钮...")
        self.click_box(attend_box, after_sleep=1.5)

        # 4. 等待5s
        self.log_info("等待5秒...")
        self.sleep(5)

        # 5. 使用基类的等待退出按钮变为白色方法
        return self.wait_for_exit_button_white(timeout=30)

    def execute_combat_sequence(self):
        """执行战斗序列"""
        self.log_info("开始执行战斗序列...")

        # 开启自动战斗
        self.start_auto_combat()

        # 按a键0.3s
        self.log_info("按A键0.3秒")
        self.send_key('a', down_time=0.3, after_sleep=0.5)

        # 按w键2.7s
        self.log_info("按W键2.7秒")
        self.send_key('w', down_time=2.7, after_sleep=0.5)

        # 按f键
        self.log_info("按F键")
        self.send_key('f', after_sleep=0.5)

        # 按d键0.8s
        self.log_info("按D键0.8秒")
        self.send_key('d', down_time=0.8, after_sleep=0.5)

        # 按f键
        self.log_info("按F键")
        self.send_key('f', after_sleep=0.5)

        self.log_info("战斗序列执行完成")

    def exit_taofa_dungeon(self):
        """退出讨伐作战副本"""
        self.log_info("开始退出副本...")

        # 延迟4s
        self.sleep(4)

        # 点击(267, 65)
        check_x, check_y = self._get_scaled_coordinates(267, 65)
        self.click(check_x, check_y, after_sleep=1)

        # 再次点击(267, 65)
        self.click(check_x, check_y, after_sleep=1)

        # 按alt+(267, 65)+松开alt
        success = self._click_with_alt(check_x, check_y, alt_down_delay=0.8, click_delay=1.5)
        if success:
            self.sleep(10)
            return True

        return False

    def run(self):
        """讨伐作战自动化流程"""
        self.log_info("开始讨伐作战任务...", notify=True)

        max_loops = self.config.get('循环次数', 10000)
        combat_timeout = self.config.get('战斗超时', 300)

        self.log_info(f"配置参数: 循环次数={max_loops}, 战斗超时={combat_timeout}秒")

        loop_count = 0

        try:
            while loop_count < max_loops:
                loop_count += 1
                self.log_info(f"开始第 {loop_count}/{max_loops} 次循环")

                # 进入副本
                if not self.enter_taofa_dungeon():
                    self.log_error("进入副本失败，跳过本次循环")
                    self.sleep(5)
                    continue

                # 执行战斗序列
                self.execute_combat_sequence()

                # 等待目标颜色（使用基类方法）
                if not self.wait_for_target_color(combat_timeout):
                    self.log_error(f"{combat_timeout}秒内未检测到目标颜色，退出副本")
                    if not self.exit_taofa_dungeon():
                        self.log_error("退出副本失败")
                    continue

                # 退出副本
                if not self.exit_taofa_dungeon():
                    self.log_error("退出副本失败")

                self.log_info(f"第 {loop_count} 次循环完成，等待5秒后开始下一次...")
                self.sleep(5)

        except Exception as e:
            self.log_error(f"任务执行过程中出现异常: {e}", exception=e, notify=True)

        finally:
            self.log_info(f"讨伐作战任务执行完成！共完成 {loop_count} 次循环", notify=True)