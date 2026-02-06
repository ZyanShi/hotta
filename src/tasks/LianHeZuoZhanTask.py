import time
from ok import Box
from qfluentwidgets import FluentIcon
from src.tasks.BaseQRSLTask import BaseQRSLTask


class LianHeZuoZhanTask(BaseQRSLTask):
    """联合作战自动化任务"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "联合作战"
        self.description = "矿砂"
        self.group_name = "精炼强化"
        self.group_icon = FluentIcon.VPN
        self.icon = FluentIcon.SYNC

        self.default_config.update({
            '循环次数': 10000,
            '副本超时': 180,
            '前进时间': 7,
            '自动战斗延迟': 2,
        })

        self.config_description = {
            '循环次数': '循环执行副本的次数',
            '副本超时': '副本超时时间（秒）',
            '前进时间': '按W键前进的时间（秒）',
            '自动战斗延迟': '前进后的等待时间（秒）',
        }

    def run(self):
        """联合作战自动化流程"""
        self.log_info("开始联合作战任务...", notify=True)

        max_loops = self.config.get('循环次数', 10000)
        chest_timeout = self.config.get('宝箱等待超时', 180)
        forward_time = self.config.get('前进时间', 7)
        forward_delay = self.config.get('前进后延迟', 2)

        self.log_info(f"配置参数: 循环次数={max_loops}, 宝箱超时={chest_timeout}秒, "
                      f"前进时间={forward_time}秒, 前进延迟={forward_delay}秒")

        loop_count = 0

        try:
            while loop_count < max_loops:
                loop_count += 1
                self.log_info(f"开始第 {loop_count}/{max_loops} 次循环")

                # 确保游戏在主页面
                self.log_info("检测是否在游戏主页面...")
                if not self.is_main_page():
                    self.log_error("无法进入游戏主页面，跳过本次循环")
                    self.sleep(5)
                    continue

                self.log_info("确认在主页面")

                # 进入副本
                self.log_info("尝试进入副本...")
                if not self.enter_dungeon():
                    self.log_error("进入副本失败，跳过本次循环")
                    self.sleep(5)
                    continue

                self.log_info("成功进入副本")

                # 前进指定时间
                self.log_info(f"前进 {forward_time} 秒...")
                self.send_key_safe('w', down_time=forward_time)
                self.log_info(f"前进完成，等待 {forward_delay} 秒延迟...")
                self.sleep(forward_delay)

                # 开启自动战斗
                self.log_info("开启自动战斗...")
                self.start_auto_combat()
                self.sleep(2)

                # 等待宝箱出现
                self.log_info(f"等待宝箱出现（超时{chest_timeout}秒）...")
                start_time = time.time()
                found_opened_chest = False
                found_unopened_chest = False
                chest_box = None

                while time.time() - start_time < chest_timeout:
                    frame = self.frame
                    if frame is None:
                        self.sleep(0.5)
                        continue
                    height, width = frame.shape[:2]
                    full_box = Box(0, 0, width, height)

                    opened_box = self.find_one('opened chest', threshold=0.7)
                    if opened_box:
                        self.log_info("检测到已打开的宝箱")
                        found_opened_chest = True
                        break

                    for name in ['chest1', 'chest2', 'chest3', 'chest4', 'chest5']:
                        result = self.find_feature(name, box=full_box, threshold=0.8)
                        if result:
                            chest_box = result[0]
                            self.log_info(f"检测到未打开的宝箱: {name}")
                            found_unopened_chest = True
                            break

                    if found_opened_chest or found_unopened_chest:
                        break

                    self.sleep(0.5)

                # 根据宝箱状态执行操作
                if found_opened_chest:
                    self.log_info("检测到已打开的宝箱，直接退出副本...")
                elif found_unopened_chest and chest_box:
                    self.log_info("检测到未打开的宝箱，尝试接近并打开...")
                    success = self.approach_chest(max_walk_time=chest_timeout - (time.time() - start_time))
                    if success:
                        self.log_info("成功打开宝箱")
                    else:
                        self.log_error("打开宝箱失败")
                else:
                    self.log_warning(f"{chest_timeout}秒内未找到任何宝箱，退出副本重试")

                # 退出副本
                self.log_info("退出副本...")
                self.exit_dungeon()

                self.log_info(f"第 {loop_count} 次循环完成，等待5秒后开始下一次...")
                self.sleep(5)

        except Exception as e:
            self.log_error(f"任务执行过程中出现异常: {e}", exception=e, notify=True)
            self.screenshot("lianhezuozhan_error")

        finally:
            self.log_info(f"联合作战任务执行完成！共完成 {loop_count} 次循环", notify=True)

    def log_warning(self, message):
        """记录警告级别的日志"""
        self.log_info(f"⚠️ {message}")