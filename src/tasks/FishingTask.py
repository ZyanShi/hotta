import time
import numpy as np
from ok import Box, TaskDisabledException
from qfluentwidgets import FluentIcon
from src.tasks.BaseQRSLTask import BaseQRSLTask

class FishingTask(BaseQRSLTask):
    """钓鱼自动化任务"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 任务基本信息
        self.name = "钓鱼"
        self.description = "切到钓鱼界面后再点击开始"
        self.group_icon = FluentIcon.LEAF
        self.icon = FluentIcon.LEAF

        # 可自定义配置项
        self.default_config.update({
            '钓鱼按键': 'e',           # 抛竿/收杆按键
            '钓鱼循环次数': 100,        # 钓鱼循环次数
        })

        # 配置项描述
        self.config_description = {
            '钓鱼按键': '抛竿和收杆的按键',
            '钓鱼循环次数': '自动钓鱼的循环次数',
        }

        # 钓鱼核心坐标（1920x1080参考）
        # 格式：(x, y, to_x, to_y)
        self.FISH_HOOK_REF = (606, 40, 640, 124)      # 鱼上钩检测区
        self.FISH_TARGET_REF = (668, 72, 1251, 93)    # 遛鱼目标色检测区

        # 颜色检测参数
        self.COLOR_TOLERANCE = 15       # 颜色匹配容差
        self.ALIGN_THRESHOLD = 5        # 对齐阈值

        # 目标颜色（BGR格式）
        self.COLOR_HOOK = (255, 255, 140)      # 鱼上钩标识色
        self.COLOR_TARGET = (64, 176, 255)     # 遛鱼目标色
        self.COLOR_WHITE = (255, 255, 255)     # 遛鱼白色控制点

    def _check_fishing_interface(self):
        """检测钓鱼界面"""
        try:
            rod_box = self.find_one('fishing rod', threshold=0.6)
            bait_box = self.find_one('fishing bait', threshold=0.6)
            if rod_box and bait_box:
                self.log_info("检测到钓鱼界面，鱼竿+鱼饵已装备")
                return True
        except Exception:
            pass
        self.log_error("未检测到钓鱼界面，请先装备鱼竿和鱼饵")
        return False

    def _get_scaled_box(self, ref_x, ref_y, to_x, to_y):
        """参考坐标转当前窗口Box（支持x,y,to_x,to_y格式）"""
        x1, y1 = self._get_scaled_coordinates(ref_x, ref_y)
        x2, y2 = self._get_scaled_coordinates(to_x, to_y)
        width = max(1, int(x2 - x1))
        height = max(1, int(y2 - y1))
        return Box(int(x1), int(y1), width, height)

    def _color_similar(self, pixel, target, tolerance):
        """像素颜色相似度判断"""
        if len(pixel) != 3 or len(target) != 3:
            return False
        return all(abs(int(p) - int(t)) <= tolerance for p, t in zip(pixel, target))

    def _get_color_percentage(self, box, target_color, tolerance):
        """计算Box内目标颜色占比"""
        frame = self.frame
        if frame is None or box.width == 0 or box.height == 0:
            return 0.0
        x1, y1 = box.x, box.y
        x2, y2 = box.x + box.width, box.y + box.height
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x1 >= x2 or y1 >= y2:
            return 0.0

        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return 0.0

        mask = np.ones(roi.shape[:2], dtype=bool)
        for i in range(3):
            mask &= (roi[:, :, i] >= target_color[i] - tolerance) & \
                    (roi[:, :, i] <= target_color[i] + tolerance)

        match_pix = np.sum(mask)
        total_pix = roi.shape[0] * roi.shape[1]
        return (match_pix / total_pix) * 100 if total_pix > 0 else 0.0

    def _get_color_xy(self, box, target_color, tolerance):
        """获取目标颜色的横坐标列表和第一个白点坐标"""
        frame = self.frame
        if frame is None or box.width == 0 or box.height == 0:
            return [], (0, 0)
        x1, y1 = box.x, box.y
        x2, y2 = box.x + box.width, box.y + box.height
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x1 >= x2 or y1 >= y2:
            return [], (0, 0)

        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return [], (0, 0)

        target_x = []
        white_xy = (0, 0)

        target_mask = np.ones(roi.shape[:2], dtype=bool)
        for i in range(3):
            target_mask &= (roi[:, :, i] >= target_color[i] - tolerance) & \
                           (roi[:, :, i] <= target_color[i] + tolerance)

        white_mask = np.ones(roi.shape[:2], dtype=bool)
        for i in range(3):
            white_mask &= (roi[:, :, i] >= self.COLOR_WHITE[i] - tolerance) & \
                          (roi[:, :, i] <= self.COLOR_WHITE[i] + tolerance)

        white_positions = np.argwhere(white_mask)
        if len(white_positions) > 0:
            white_y, white_x = white_positions[0]
            white_xy = (x1 + white_x, y1 + white_y)

        target_positions = np.argwhere(target_mask)
        if len(target_positions) > 0:
            target_x = [x1 + pos[1] for pos in target_positions]

        return target_x, white_xy

    def _wait_fish_hook(self):
        """等待鱼上钩：检测遛鱼目标色#FFB040"""
        self.log_info("抛竿完成，等待鱼上钩...")
        start_time = time.time()
        target_box = self._get_scaled_box(*self.FISH_TARGET_REF)

        while time.time() - start_time < 30:
            if self._get_color_percentage(target_box, self.COLOR_TARGET, self.COLOR_TOLERANCE) > 0:
                self.log_info("鱼上钩了，开始遛鱼")
                return True
            self.sleep(0.05)

        self.log_error("等待鱼上钩超时")
        return False

    def _control_fishing(self):
        """遛鱼逻辑"""
        self.log_info("开始遛鱼")

        control_box = self._get_scaled_box(*self.FISH_TARGET_REF)
        hook_box = self._get_scaled_box(*self.FISH_HOOK_REF)

        current_key = None
        fishing_start_time = time.time()

        while True:
            if time.time() - fishing_start_time >= 5:
                if self._get_color_percentage(hook_box, self.COLOR_HOOK, self.COLOR_TOLERANCE) <= 0:
                    self.log_info("鱼体力耗尽，准备收杆")
                    if current_key:
                        self.send_key_up(current_key)
                    return True

            target_x, white_xy = self._get_color_xy(control_box, self.COLOR_TARGET, self.COLOR_TOLERANCE)
            white_x = white_xy[0]

            if not target_x or white_x == 0:
                if current_key:
                    self.send_key_up(current_key)
                    current_key = None
                self.sleep(0.05)
                continue

            target_center = (min(target_x) + max(target_x)) / 2

            if white_x < target_center - self.ALIGN_THRESHOLD:
                if current_key != 'd':
                    if current_key:
                        self.send_key_up(current_key)
                    self.send_key_down('d')
                    current_key = 'd'
            elif white_x > target_center + self.ALIGN_THRESHOLD:
                if current_key != 'a':
                    if current_key:
                        self.send_key_up(current_key)
                    self.send_key_down('a')
                    current_key = 'a'
            else:
                if current_key:
                    if (current_key == 'd' and white_x >= target_center) or \
                       (current_key == 'a' and white_x <= target_center):
                        self.send_key_up(current_key)
                        current_key = None
                        self.sleep(0.1)

            self.sleep(0.03)

    def run(self):
        """钓鱼主流程"""
        try:
            self.log_info("===== 钓鱼任务启动 =====", notify=True)

            fish_key = self.config.get('钓鱼按键', 'e')
            max_loops = self.config.get('钓鱼循环次数', 100)

            self.log_info(f"配置参数: 钓鱼按键={fish_key}, 循环次数={max_loops}")

            completed = 0

            for i in range(max_loops):
                self.log_info(f"--- 第 {i+1}/{max_loops} 次循环开始 ---")

                if not self._check_fishing_interface():
                    self.sleep(2)
                    continue

                # 抛竿
                self.log_info(f"发送抛竿按键 [{fish_key}]")
                self.send_key(fish_key, down_time=0.1)
                self.sleep(2)

                # 等待鱼上钩
                if not self._wait_fish_hook():
                    self.sleep(2)
                    continue

                # 遛鱼
                if not self._control_fishing():
                    self.sleep(2)
                    continue

                # 收杆
                self.sleep(1)
                self.log_info(f"发送收杆按键 [{fish_key}]")
                self.send_key(fish_key, down_time=0.1)
                self.sleep(2)
                self.click_relative(0.5, 0.5)
                self.sleep(1)

                completed += 1
                self.log_info(f"第 {i+1} 次钓鱼完成")
                self.sleep(1)

            self.log_info(f"===== 钓鱼任务结束，共完成 {completed}/{max_loops} 次 =====", notify=True)

        except TaskDisabledException:
            self.log_info("钓鱼任务被用户手动停止")
        except Exception as e:
            self.log_error(f"钓鱼任务异常: {e}", exception=e, notify=True)
            self.screenshot("fishing_error")
            raise
        finally:
            # 最终保障：松开所有按键
            self.send_key_up('a')
            self.send_key_up('d')
            if fish_key:
                self.send_key_up(fish_key)