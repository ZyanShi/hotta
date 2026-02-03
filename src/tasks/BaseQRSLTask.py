import time
from ok import BaseTask
from ok import Box


class BaseQRSLTask(BaseTask):
    """QRSL游戏专用基础任务类"""

    CHEST_NAMES = ['chest1', 'chest2', 'chest3', 'chest4', 'chest5']
    ENTER_TEAM_COORDS = (1900, 320)
    AUTO_COMBAT_COORDS = (1160, 930)
    EXIT_CHECK_COORDS = (267, 65)
    MAIN_PAGE_COORDS = (22, 63)
    REF_RESOLUTION = (1920, 1080)
    TARGET_COLOR_BGR = (237, 166, 62)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _get_scaled_coordinates(self, ref_x, ref_y):
        """根据参考分辨率计算当前分辨率下的坐标"""
        frame = self.frame
        if frame is None:
            return ref_x, ref_y

        height, width = frame.shape[:2]
        scale_x = width / self.REF_RESOLUTION[0]
        scale_y = height / self.REF_RESOLUTION[1]

        return int(ref_x * scale_x), int(ref_y * scale_y)

    def _execute_atomic_operation(self, operation_func):
        """执行原子操作，确保不被中断"""
        try:
            self.operate(operation_func)
            return True
        except Exception as e:
            self.log_error(f"原子操作执行失败: {e}")
            return False

    def _click_with_alt(self, x, y, alt_down_delay=0.2, click_delay=0.5, alt_key='alt'):
        """使用Alt+点击的通用方法"""
        def operation():
            self.send_key_down(alt_key)
            self.sleep(alt_down_delay)
            self.click(x, y, move=False, down_time=0.01)
            self.sleep(click_delay)
            self.send_key_up(alt_key)

        return self._execute_atomic_operation(operation)

    def _is_white_color(self, pixel_bgr, tolerance=10):
        """判断是否为白色"""
        return all(245 <= color <= 255 for color in pixel_bgr)

    def _color_similar(self, color1, color2, tolerance=30):
        """判断颜色是否相似"""
        return sum(abs(int(color1[i]) - color2[i]) for i in range(3)) < tolerance

    def enter_team(self, alt_down_delay=0.2, click_delay=0.5, alt_key='alt'):
        """使用 Alt+点击坐标(1900,320)的方法进入队伍"""
        target_x, target_y = self._get_scaled_coordinates(*self.ENTER_TEAM_COORDS)
        self.log_debug(f"队伍进入坐标: ({target_x}, {target_y})")

        success = self._click_with_alt(target_x, target_y, alt_down_delay, click_delay, alt_key)

        if success:
            self.log_debug("队伍进入操作完成")
        else:
            self.log_error("队伍进入操作失败")

        self.sleep(0.5)
        return success

    def start_auto_combat(self, alt_down_delay=0.2, click_delay=0.5, alt_key='alt'):
        """开启自动战斗"""
        target_x, target_y = self._get_scaled_coordinates(*self.AUTO_COMBAT_COORDS)
        self.log_debug(f"自动战斗按钮坐标: ({target_x}, {target_y})")

        success = self._click_with_alt(target_x, target_y, alt_down_delay, click_delay, alt_key)

        if success:
            self.log_debug("自动战斗已开启")
            self.sleep(5)
        else:
            self.log_error("开启自动战斗失败")

        return success

    def enter_dungeon(self):
        """进入副本流程"""
        start_time = time.time()
        attend_found = False

        while not attend_found:
            if time.time() - start_time > 10:
                self.log_error("10秒内未找到attend图片，进入副本失败")
                return False

            self.enter_team(alt_down_delay=0.5, click_delay=0.5)
            attend_box = self.find_one('attend', threshold=0.75)
            if attend_box:
                self.log_info("找到参与按钮")
                attend_found = True
            else:
                self.sleep(0.5)

        self.click_box(attend_box, after_sleep=0.5)

        enter_box = self.wait_feature('enter', time_out=10, threshold=0.75, raise_if_not_found=False)
        if not enter_box:
            self.log_error("10秒内未找到进入按钮")
            return False

        self.click_box(enter_box, after_sleep=0.5)

        chest_box = self.wait_feature('unopened chest', time_out=60, threshold=0.7, raise_if_not_found=False)
        if not chest_box:
            self.log_error("60秒内未进入副本")
            return False

        self.log_info("成功进入副本")
        self.sleep(2)
        return True

    def exit_dungeon(self):
        """退出副本"""
        frame = self.frame
        if frame is None:
            self.log_error("无法获取屏幕截图")
            return False

        check_x, check_y = self._get_scaled_coordinates(*self.EXIT_CHECK_COORDS)
        pixel_color = frame[check_y, check_x]

        if not self._is_white_color(pixel_color):
            self.log_debug("未检测到退出条件")
            return False

        self.log_info("检测到退出副本条件，开始退出")

        if not self._click_with_alt(check_x, check_y, alt_down_delay=0.2, click_delay=0.5):
            self.log_error("点击退出坐标失败")
            return False

        confirm_box = self.wait_feature('confirm', time_out=10, threshold=0.7, raise_if_not_found=False)
        if confirm_box:
            confirm_center = confirm_box.center()
            if not self._click_with_alt(confirm_center[0], confirm_center[1], alt_down_delay=0.2, click_delay=0.5):
                self.log_error("点击确认按钮失败")
                return False

            self.sleep(8)
            self.log_info("退出副本操作完成")
            return True
        else:
            self.log_error("10秒内未找到确认按钮")
            return False

    def click_with_mouse_mode(self, x, y, alt_down_delay=0.2, click_delay=0.5, alt_key='alt'):
        """调出鼠标点击功能"""
        return self._click_with_alt(x, y, alt_down_delay, click_delay, alt_key)

    def is_main_page(self):
        """判断是否在游戏主页面"""
        while True:
            frame = self.frame
            if frame is None:
                self.log_error("无法获取屏幕截图")
                self.sleep(1)
                continue

            height, width = frame.shape[:2]
            current_x, current_y = self._get_scaled_coordinates(*self.MAIN_PAGE_COORDS)
            pixel_color = frame[current_y, current_x]

            if self._color_similar(pixel_color, self.TARGET_COLOR_BGR):
                self.log_info(f"检测到主页面！分辨率: {width}x{height}")
                self.sleep(3)
                return True

            back_box = self.find_one('back', threshold=0.75)
            if back_box:
                self.click_box(back_box, after_sleep=0.5)
                continue

            check_x, check_y = self._get_scaled_coordinates(*self.EXIT_CHECK_COORDS)
            pixel_color = frame[check_y, check_x]

            if self._is_white_color(pixel_color):
                self.exit_dungeon()
                continue

            self.log_debug("尝试按ESC键返回...")
            self.send_key('esc', after_sleep=1)
            self.next_frame()

    def operate(self, func):
        """在原子操作中执行函数，不会被其他任务打断"""
        if hasattr(self, 'executor') and self.executor:
            self.executor.interaction.operate(func, block=True)
        else:
            self.log_warning("没有找到executor，直接执行操作")
            func()

    def wait_any_chest(self, time_out=30):
        """等待任意宝箱出现"""
        self.log_info(f"等待任意宝箱出现，超时{time_out}秒")
        start_time = time.time()

        while True:
            if time.time() - start_time > time_out:
                self.log_info("等待宝箱超时")
                return None

            frame = self.frame
            if frame is None:
                self.sleep(0.5)
                continue

            height, width = frame.shape[:2]
            full_box = Box(0, 0, width, height)

            for name in self.CHEST_NAMES:
                result = self.find_feature(name, box=full_box, threshold=0.8)
                if result:
                    target_chest = result[0]
                    self.log_info(f"找到{name}宝箱，位置: {target_chest.center()}")
                    return target_chest

            self.sleep(1)

    def approach_chest(self, max_walk_time=60):
        """自动走向并打开宝箱"""
        self.log_info("开始自动走向宝箱...")

        frame = self.frame
        if frame is None:
            self.log_error("无法获取屏幕截图")
            return False

        height, width = frame.shape[:2]
        screen_center_x = width // 2

        vertical_threshold_ratio = 800 / 1080
        vertical_threshold = int(height * vertical_threshold_ratio)

        left_boundary_ratio = 450 / 1920
        right_boundary_ratio = 1470 / 1920
        left_boundary = int(width * left_boundary_ratio)
        right_boundary = int(width * right_boundary_ratio)

        center_tolerance_ratio = 0.05
        center_tolerance = int(width * center_tolerance_ratio)
        center_min = screen_center_x - center_tolerance
        center_max = screen_center_x + center_tolerance

        # 等待并锁定一个宝箱
        target_chest = self.wait_any_chest(time_out=30)
        if target_chest is None:
            self.log_error("30秒内未找到任何宝箱")
            return False

        self.log_info(f"已锁定宝箱，初始位置: {target_chest.center()}")

        start_time = time.time()
        chest_disappear_count = 0
        max_disappear_count = 5
        last_key_press_time = 0
        key_press_interval = 0.15
        locked_chest_type = None

        try:
            while time.time() - start_time < max_walk_time:
                current_time = time.time()

                opened_box = self.find_one('opened chest', threshold=0.7)
                if opened_box:
                    self.log_info("宝箱已打开！")
                    self.sleep(0.5)
                    return True

                if current_time - last_key_press_time < key_press_interval:
                    self.sleep(0.05)
                    continue

                frame = self.frame
                if frame is None:
                    continue

                height, width = frame.shape[:2]
                full_box = Box(0, 0, width, height)
                current_chest = None

                if locked_chest_type:
                    results = self.find_feature(locked_chest_type, box=full_box, threshold=0.8)
                    if results:
                        if len(results) > 1:
                            last_center = target_chest.center()
                            distances = [abs(r.center()[0] - last_center[0]) + abs(r.center()[1] - last_center[1])
                                         for r in results]
                            closest_idx = distances.index(min(distances))
                            current_chest = results[closest_idx]
                        else:
                            current_chest = results[0]

                if current_chest is None:
                    for name in self.CHEST_NAMES:
                        results = self.find_feature(name, box=full_box, threshold=0.6)
                        if results:
                            locked_chest_type = name

                            if len(results) > 1:
                                last_center = target_chest.center()
                                distances = [abs(r.center()[0] - last_center[0]) + abs(r.center()[1] - last_center[1])
                                             for r in results]
                                closest_idx = distances.index(min(distances))
                                current_chest = results[closest_idx]
                            else:
                                current_chest = results[0]
                            break

                if current_chest is None:
                    chest_disappear_count += 1

                    if chest_disappear_count >= max_disappear_count:
                        self.log_debug("宝箱消失次数过多，重新搜索...")
                        found = False
                        for _ in range(100):
                            frame = self.frame
                            if frame is None:
                                continue

                            height, width = frame.shape[:2]
                            full_box = Box(0, 0, width, height)

                            for name in self.CHEST_NAMES:
                                results = self.find_feature(name, box=full_box, threshold=0.6)
                                if results:
                                    locked_chest_type = name
                                    current_chest = results[0]
                                    chest_disappear_count = 0
                                    found = True
                                    break

                            if found:
                                break

                        if not found:
                            self.log_info("无法重新找到宝箱，任务失败")
                            return False
                else:
                    chest_disappear_count = 0

                target_chest = current_chest
                chest_x, chest_y = target_chest.center()

                if chest_x < center_min or chest_x > center_max:
                    horizontal_error = chest_x - screen_center_x

                    if chest_x < left_boundary or chest_x > right_boundary:
                        if horizontal_error < 0:
                            self.log_debug("宝箱在左侧边界外，长按A")
                            self.send_key_safe('a', down_time=1.0)
                        else:
                            self.log_debug("宝箱在右侧边界外，长按D")
                            self.send_key_safe('d', down_time=1.0)
                    else:
                        if horizontal_error < 0:
                            self.log_debug("宝箱在左边(微调)，短按A")
                            self.send_key_safe('a', down_time=0.2)
                        else:
                            self.log_debug("宝箱在右边(微调)，短按D")
                            self.send_key_safe('d', down_time=0.2)

                    last_key_press_time = current_time
                    continue

                current_vertical_threshold = int(height * vertical_threshold_ratio)

                if chest_y < current_vertical_threshold:
                    self.log_debug("宝箱在前面，长按W")
                    self.send_key_safe('w', down_time=1.0)
                else:
                    self.log_debug("宝箱在后面，长按S")
                    self.send_key_safe('s', down_time=1.0)

                last_key_press_time = current_time

            opened_box = self.find_one('opened chest', threshold=0.7)
            if opened_box:
                self.log_info("超时前成功打开宝箱！")
                return True
            else:
                self.log_error(f"{max_walk_time}秒内未能打开宝箱")
                return False

        except Exception as e:
            self.log_error(f"接近宝箱过程中出现异常: {e}", exception=e)
            return False

    def send_key_safe(self, key, down_time=0.1):
        """安全的按键方法，避免触发鼠标移动"""
        try:
            self.send_key_down(key)
            self.sleep(down_time)
            self.send_key_up(key)
        except Exception as e:
            self.log_debug(f"安全按键失败，使用普通按键: {e}")
            self.send_key(key, down_time=down_time)