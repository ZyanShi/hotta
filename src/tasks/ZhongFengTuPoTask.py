# file: src/tasks/ZhongFengTuPoTask.py
import time
from ok import TaskDisabledException
from qfluentwidgets import FluentIcon
from src.tasks.BaseQRSLTask import BaseQRSLTask


class ZhongFengTuPoTask(BaseQRSLTask):
    """众峰突破自动化任务"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "众峰突破"
        self.description = "自动完成众峰突破挑战"
        self.group_icon = FluentIcon.GAME
        self.icon = FluentIcon.GAME

        # 配置项
        self.default_config.update({
            '关卡选择': '当前关卡',
            '循环次数': 10000,
        })
        self.config_description = {
            '关卡选择': '选择要挑战的关卡',
            '循环次数': '任务执行的最大循环次数',
        }
        self.config_type['关卡选择'] = {
            'type': "drop_down",
            'options': ['当前关卡', '第一关', '第二关', '第三关', '第四关', '第五关', '第六关', '第七关', '第八关']
        }

    def _wait_and_click_feature(self, feature_name, timeout, after_sleep=0, raise_if_not_found=False):
        """等待特征出现并点击，返回是否成功"""
        box = self.wait_feature(feature_name, time_out=timeout, raise_if_not_found=False)
        if box:
            self.log_info(f"找到并点击 [{feature_name}]")
            self.click_box(box)
            if after_sleep > 0:
                self.sleep(after_sleep)
            return True
        self.log_error(f"等待 [{feature_name}] 超时 ({timeout}秒)")
        if raise_if_not_found:
            raise Exception(f"找不到特征 {feature_name}")
        return False

    def _wait_for_any_feature(self, feature_names, timeout, after_sleep=0):
        """等待多个特征中任意一个出现，返回第一个找到的box和名称，超时返回(None, None)"""
        start = time.time()
        while time.time() - start < timeout:
            for name in feature_names:
                box = self.find_one(name, threshold=0.7)
                if box:
                    self.log_info(f"检测到特征 [{name}]")
                    if after_sleep > 0:
                        self.sleep(after_sleep)
                    return box, name
            self.sleep(0.5)
        self.log_error(f"等待特征 {feature_names} 超时 ({timeout}秒)")
        return None, None

    def _wait_for_main_page_color(self, timeout=60):
        """等待主页颜色出现"""
        start = time.time()
        while time.time() - start < timeout:
            frame = self.frame
            if frame is None:
                self.sleep(0.5)
                continue
            x, y = self._get_scaled_coordinates(*self.MAIN_PAGE_COORDS)
            if y >= frame.shape[0] or x >= frame.shape[1]:
                self.sleep(0.5)
                continue
            pixel = frame[y, x]
            if self._color_similar(pixel, self.TARGET_COLOR_BGR, tolerance=30):
                self.log_info("检测到主页面颜色")
                return True
            self.sleep(0.5)
        self.log_error("等待主页面颜色超时")
        return False

    def run(self):
        try:
            self.log_info("===== 众峰突破任务启动 =====", notify=True)
            max_loops = self.config.get('循环次数', 10000)
            loop_count = 0

            while loop_count < max_loops:
                loop_count += 1
                self.log_info(f"--- 第 {loop_count}/{max_loops} 次循环开始 ---")

                # 第一步：确保在主页面
                if not self.is_main_page():
                    self.log_error("无法进入游戏主页面，跳过本次循环")
                    self.sleep(5)
                    continue

                # 第二步：发送esc键，延迟1s
                self.log_info("按ESC键打开菜单")
                self.send_key('esc')
                self.sleep(1)

                # 第三步：等待并点击“工会”图片
                if not self._wait_and_click_feature('gonghui', timeout=5, after_sleep=0):
                    self.log_error("未找到工会图标，跳过本次循环")
                    self.sleep(5)
                    continue

                # 第四步：等待并点击“活动”图片
                if not self._wait_and_click_feature('huodong', timeout=10, after_sleep=0):
                    self.log_error("未找到活动图标，跳过本次循环")
                    self.sleep(5)
                    continue

                # 第五步：等待并点击“众峰突破”图片
                if not self._wait_and_click_feature('zhongfengtupo', timeout=10, after_sleep=0):
                    self.log_error("未找到众峰突破图标，跳过本次循环")
                    self.sleep(5)
                    continue

                # 第六步：判断页面（等待back或jinruzhandou）
                box, name = self._wait_for_any_feature(['back', 'jinruzhandou'], timeout=10)
                if name is None:
                    self.log_error("既未出现返回按钮也未出现进入战斗按钮，跳过本次循环")
                    self.sleep(5)
                    continue

                if name == 'jinruzhandou':
                    self.log_info("检测到进入战斗按钮，点击它")
                    self.click_box(box)
                    self.sleep(1)  # 等待界面切换

                self.log_info("已进入众峰突破界面")

                # 第七步：根据关卡选择执行操作
                level = self.config.get('关卡选择', '当前关卡')
                if level == '当前关卡':
                    # 点击“进入挑战”按钮
                    if not self._wait_and_click_feature('enterchallenge', timeout=10, after_sleep=0):
                        self.log_error("未找到进入挑战按钮，跳过本次循环")
                        self.sleep(5)
                        continue
                else:
                    # 其他关卡逻辑暂未实现，直接提示并跳过循环
                    self.log_info(f"关卡 [{level}] 尚未实现，跳过本次循环")
                    self.sleep(5)
                    continue

                # 第八步：等待并点击“确认”按钮
                if not self._wait_and_click_feature('sure', timeout=5, after_sleep=10):
                    self.log_error("未找到确认按钮，跳过本次循环")
                    self.sleep(5)
                    continue

                # 第九步：等待退出按钮变白（表示进入副本/挑战成功）
                self.log_info("等待退出按钮变白...")
                if not self.wait_for_exit_button_white(timeout=60):
                    self.log_error("等待退出按钮变白超时，跳过本次循环")
                    self.sleep(5)
                    continue

                # 第十步：执行退出副本的函数
                self.log_info("退出副本")
                self.exit_dungeon()  # 基类方法，可复用
                self.sleep(2)

                # 第十一步：等待回到主页面
                self.log_info("等待返回主页面...")
                if not self._wait_for_main_page_color(timeout=60):
                    self.log_error("等待主页面超时，跳过本次循环")
                    self.sleep(5)
                    continue

                self.log_info(f"第 {loop_count} 次循环完成")

            self.log_info(f"===== 众峰突破任务结束，共完成 {loop_count} 次循环 =====", notify=True)

        except TaskDisabledException:
            self.log_info("众峰突破任务被用户手动停止")
        except Exception as e:
            self.log_error(f"众峰突破任务异常: {e}", notify=True)
            self.screenshot("zhongfengtupo_error")
            raise