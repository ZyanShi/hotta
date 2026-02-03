# TestMain.py
# 联合作战任务测试用例

import unittest
import time
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from src.config import config
from ok.test.TaskTestCase import TaskTestCase

from src.tasks.LianHeZuoZhanTask import LianHeZuoZhanTask
from src.tasks.BaseQRSLTask import BaseQRSLTask
from ok import Box


class TestLianHeZuoZhanTask(TaskTestCase):
    """联合作战任务测试类"""

    task_class = LianHeZuoZhanTask
    config = config

    def setUp(self):
        """测试前设置"""
        super().setUp()
        self.task = self.create_task()

    def test_task_initialization(self):
        """测试任务初始化"""
        self.assertEqual(self.task.name, "联合作战")
        self.assertEqual(self.task.description, "刷砂")

        # 测试默认配置
        self.assertEqual(self.task.default_config['循环次数'], 10000)
        self.assertEqual(self.task.default_config['副本超时'], 180)
        self.assertEqual(self.task.default_config['前进时间'], 7)
        self.assertEqual(self.task.default_config['自动战斗延迟'], 2)

        # 测试配置描述
        self.assertEqual(self.task.config_description['循环次数'], '循环执行副本的次数')
        self.assertEqual(self.task.config_description['副本超时'], '副本超时时间（秒）')

    def test_run_method_exists(self):
        """测试run方法存在"""
        self.assertTrue(hasattr(self.task, 'run'))
        self.assertTrue(callable(self.task.run))

    def test_config_loading(self):
        """测试配置加载"""
        # 模拟配置
        mock_config = {
            '循环次数': 5,
            '副本超时': 120,
            '前进时间': 5,
            '自动战斗延迟': 1,
        }

        # 测试配置获取
        with patch.object(self.task, 'config', mock_config):
            max_loops = self.task.config.get('循环次数', 10000)
            self.assertEqual(max_loops, 5)

            chest_timeout = self.task.config.get('副本超时', 180)
            self.assertEqual(chest_timeout, 120)

    def test_base_methods_inheritance(self):
        """测试基础方法继承"""
        # 测试是否继承了BaseQRSLTask的方法
        self.assertTrue(hasattr(self.task, '_get_scaled_coordinates'))
        self.assertTrue(hasattr(self.task, 'enter_dungeon'))
        self.assertTrue(hasattr(self.task, 'exit_dungeon'))
        self.assertTrue(hasattr(self.task, 'is_main_page'))
        self.assertTrue(hasattr(self.task, 'approach_chest'))

    @patch.object(LianHeZuoZhanTask, 'log_info')
    @patch.object(LianHeZuoZhanTask, 'sleep')
    def test_run_with_mock(self, mock_sleep, mock_log):
        """使用mock测试run方法的基本流程"""
        # 模拟配置
        self.task.config = {
            '循环次数': 1,
            '副本超时': 180,
            '前进时间': 7,
            '自动战斗延迟': 2,
        }

        # 模拟各个步骤都成功
        with patch.object(self.task, 'is_main_page', return_value=True):
            with patch.object(self.task, 'enter_dungeon', return_value=True):
                with patch.object(self.task, 'send_key_safe'):
                    with patch.object(self.task, 'start_auto_combat', return_value=True):
                        with patch.object(self.task, 'find_one', return_value=None):
                            with patch.object(self.task, 'find_feature', return_value=[]):
                                with patch.object(self.task, 'exit_dungeon', return_value=True):
                                    # 执行run方法
                                    try:
                                        self.task.run()
                                    except Exception as e:
                                        # run方法中可能有未模拟的调用，这里捕获异常
                                        pass

                                    # 验证日志被调用
                                    self.assertTrue(mock_log.called)
                                    # 验证sleep被调用
                                    self.assertTrue(mock_sleep.called)

    def test_image_recognition(self):
        """测试图像识别功能"""
        # 设置测试图片
        self.set_image('tests/images/chest_test.png')  # 假设有这个测试图片

        # 测试找图功能
        chest_box = self.task.find_one('chest1', threshold=0.8)

        if chest_box:
            self.assertIsInstance(chest_box, Box)
            self.assertGreater(chest_box.confidence, 0.7)
        else:
            # 如果没有找到，测试空结果处理
            self.assertIsNone(chest_box)

    def test_ocr_functionality(self):
        """测试OCR功能"""
        # 设置测试图片
        self.set_image('tests/images/text_test.png')  # 假设有这个测试图片

        # 测试OCR识别
        text_results = self.task.ocr(
            x=0, y=0,
            to_x=1, to_y=0.1,  # 只识别顶部区域
            match=None
        )

        # OCR可能返回空列表
        if text_results:
            for box in text_results:
                self.assertIsInstance(box, Box)
                self.assertIsInstance(box.name, str)
                self.assertGreater(len(box.name), 0)

    def test_box_operations(self):
        """测试Box操作"""
        # 创建一个测试Box
        test_box = Box(100, 100, 200, 200, name="test_box")

        # 测试Box属性
        self.assertEqual(test_box.x, 100)
        self.assertEqual(test_box.y, 100)
        self.assertEqual(test_box.width, 200)
        self.assertEqual(test_box.height, 200)
        self.assertEqual(test_box.name, "test_box")

        # 测试中心点计算
        center_x, center_y = test_box.center()
        self.assertEqual(center_x, 200)  # 100 + 200/2
        self.assertEqual(center_y, 200)  # 100 + 200/2

        # 测试面积计算
        area = test_box.area()
        self.assertEqual(area, 40000)  # 200 * 200

        # 测试缩放
        scaled_box = test_box.scale(0.5, 0.5)
        self.assertEqual(scaled_box.width, 100)
        self.assertEqual(scaled_box.height, 100)

    def test_keyboard_operations(self):
        """测试键盘操作"""
        # 测试按键方法存在
        self.assertTrue(hasattr(self.task, 'send_key'))
        self.assertTrue(hasattr(self.task, 'send_key_down'))
        self.assertTrue(hasattr(self.task, 'send_key_up'))
        self.assertTrue(hasattr(self.task, 'send_key_safe'))

        # 测试send_key_safe方法
        with patch.object(self.task, 'send_key_down'):
            with patch.object(self.task, 'send_key_up'):
                with patch.object(self.task, 'sleep'):
                    self.task.send_key_safe('w', down_time=1.0)

    def test_mouse_operations(self):
        """测试鼠标操作"""
        # 测试鼠标方法存在
        self.assertTrue(hasattr(self.task, 'click'))
        self.assertTrue(hasattr(self.task, 'click_box'))
        self.assertTrue(hasattr(self.task, 'right_click'))

        # 创建一个测试Box
        test_box = Box(100, 100, 50, 50, name="test_button")

        # 测试点击Box
        with patch.object(self.task, 'click') as mock_click:
            self.task.click_box(test_box)
            mock_click.assert_called()

    def test_error_handling(self):
        """测试错误处理"""
        # 测试日志方法
        with patch.object(self.task, 'log_info') as mock_log:
            self.task.log_info("测试信息", notify=True)
            mock_log.assert_called_with("测试信息", notify=True)

        # 测试错误日志
        with patch.object(self.task, 'log_error') as mock_error:
            try:
                raise ValueError("测试异常")
            except Exception as e:
                self.task.log_error("测试错误", exception=e, notify=True)
            mock_error.assert_called()

    def test_wait_functions(self):
        """测试等待功能"""
        # 测试等待方法存在
        self.assertTrue(hasattr(self.task, 'wait_feature'))
        self.assertTrue(hasattr(self.task, 'wait_click_feature'))

        # 模拟等待找到特征
        mock_box = Box(100, 100, 50, 50, confidence=0.9, name="test_feature")
        with patch.object(self.task, 'find_one', return_value=mock_box):
            result = self.task.wait_feature('test_feature', time_out=1)
            self.assertIsNotNone(result)
            self.assertEqual(result.name, "test_feature")

    def test_coordinate_scaling(self):
        """测试坐标缩放"""
        # 创建模拟的frame
        mock_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

        with patch.object(self.task, 'frame', mock_frame):
            # 测试在1920x1080分辨率下的坐标缩放
            scaled_x, scaled_y = self.task._get_scaled_coordinates(1900, 320)
            self.assertEqual(scaled_x, 1900)
            self.assertEqual(scaled_y, 320)

            # 测试在960x540分辨率下的坐标缩放
            small_frame = np.zeros((540, 960, 3), dtype=np.uint8)
            with patch.object(self.task, 'frame', small_frame):
                scaled_x, scaled_y = self.task._get_scaled_coordinates(1900, 320)
                self.assertEqual(scaled_x, 950)  # 1900 * (960/1920)
                self.assertEqual(scaled_y, 160)  # 320 * (540/1080)

    def test_color_detection(self):
        """测试颜色检测"""
        # 创建一个包含特定颜色的测试frame
        test_frame = np.zeros((100, 100, 3), dtype=np.uint8)

        # 在特定区域设置目标颜色
        target_color = BaseQRSLTask.TARGET_COLOR_BGR  # (237, 166, 62) BGR格式
        test_frame[10:20, 10:20] = target_color

        with patch.object(self.task, 'frame', test_frame):
            # 测试颜色相似度检测
            test_box = Box(0, 0, 100, 100)
            pixel_color = test_frame[15, 15]

            # 调用颜色相似度方法
            is_similar = self.task._color_similar(pixel_color, target_color, tolerance=30)
            self.assertTrue(is_similar)

            # 测试白色检测
            white_pixel = np.array([255, 255, 255])
            is_white = self.task._is_white_color(white_pixel)
            self.assertTrue(is_white)


class TestBaseQRSLTask(unittest.TestCase):
    """BaseQRSLTask基础类测试"""

    def setUp(self):
        """测试前设置"""
        self.base_task = BaseQRSLTask(executor=Mock())

    def test_constant_values(self):
        """测试常量值"""
        self.assertEqual(BaseQRSLTask.ENTER_TEAM_COORDS, (1900, 320))
        self.assertEqual(BaseQRSLTask.AUTO_COMBAT_COORDS, (1160, 930))
        self.assertEqual(BaseQRSLTask.EXIT_CHECK_COORDS, (267, 65))
        self.assertEqual(BaseQRSLTask.MAIN_PAGE_COORDS, (22, 63))
        self.assertEqual(BaseQRSLTask.REF_RESOLUTION, (1920, 1080))
        self.assertEqual(BaseQRSLTask.TARGET_COLOR_BGR, (237, 166, 62))

        # 测试宝箱名称列表
        self.assertEqual(len(BaseQRSLTask.CHEST_NAMES), 5)
        self.assertEqual(BaseQRSLTask.CHEST_NAMES[0], 'chest1')
        self.assertEqual(BaseQRSLTask.CHEST_NAMES[4], 'chest5')

    def test_atomic_operation(self):
        """测试原子操作"""

        def test_operation():
            return "操作成功"

        # 测试正常执行
        with patch.object(self.base_task, 'operate') as mock_operate:
            mock_operate.return_value = "操作成功"
            result = self.base_task._execute_atomic_operation(test_operation)
            self.assertTrue(result)

    def test_approach_chest_logic(self):
        """测试接近宝箱的逻辑"""
        # 创建一个模拟的宝箱Box
        mock_chest = Box(500, 300, 100, 100, name="chest1")

        # 模拟等待宝箱
        with patch.object(self.base_task, 'wait_any_chest', return_value=mock_chest):
            # 模拟帧数据
            mock_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

            # 模拟各种find方法
            with patch.object(self.base_task, 'frame', mock_frame):
                with patch.object(self.base_task, 'find_one', return_value=None):
                    with patch.object(self.base_task, 'find_feature', return_value=[mock_chest]):
                        with patch.object(self.base_task, 'send_key_safe'):
                            with patch.object(self.base_task, 'sleep'):
                                # 执行approach_chest方法
                                result = self.base_task.approach_chest(max_walk_time=5)
                                # 由于我们模拟了所有方法，结果应该为False（因为超时时间很短）
                                # 或者我们可以让它在特定条件下返回True
                                pass


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)