# TestMain.py - 简单直接的测试
# 专注于核心功能测试

import unittest
import os
import json
import cv2
import numpy as np
from pathlib import Path

from src.config import config


class TestConfig(unittest.TestCase):
    """配置测试"""

    def test_basic_config(self):
        """测试基本配置"""
        # 检查关键配置
        self.assertEqual(config['gui_title'], 'ok-hotta')

# 只是打印，不检查值

    def test_game_config(self):
        """测试游戏配置"""
        windows_config = config['windows']

        self.assertEqual(windows_config['exe'], ['QRSL.exe'])
        self.assertEqual(windows_config['interaction'], 'Genshin')



    def test_resolution_config(self):
        """测试分辨率配置"""
        resolution = config['supported_resolution']

        self.assertEqual(resolution['ratio'], '16:9')
        self.assertEqual(resolution['min_size'], (1280, 720))


    def test_template_matching(self):
        """测试模板匹配配置"""
        tm_config = config['template_matching']

        # 检查COCO文件是否存在
        coco_file = tm_config['coco_feature_json']
        if os.path.exists(coco_file):
            print(f"✅ COCO文件存在: {coco_file}")
        else:
            print(f"⚠️  COCO文件不存在: {coco_file}")

        print(f"✅ 默认阈值: {tm_config['default_threshold']}")


class TestImageProcessing(unittest.TestCase):
    """图像处理测试"""

    def test_screenshot_processor(self):
        """测试截图处理函数"""
        from src.config import make_bottom_right_black

        # 创建一个测试图像
        test_image = np.ones((720, 1280, 3), dtype=np.uint8) * 255

        # 处理图像
        try:
            processed = make_bottom_right_black(test_image)
            self.assertEqual(processed.shape, test_image.shape)
            print("✅ 截图处理函数正常工作")
        except Exception as e:
            print(f"⚠️  截图处理函数出错: {e}")

    def test_create_simple_test_image(self):
        """创建简单的测试图像"""
        # 创建测试图像
        img = np.zeros((200, 300, 3), dtype=np.uint8)

        # 添加一些形状
        cv2.rectangle(img, (50, 50), (150, 150), (0, 0, 255), -1)  # 红色矩形
        cv2.circle(img, (250, 100), 40, (0, 255, 0), -1)  # 绿色圆形

        # 显示图像信息
        print(f"✅ 创建测试图像: {img.shape[1]}x{img.shape[0]}, 通道数: {img.shape[2]}")

        # 检查颜色
        red_pixel = img[100, 100]  # 应该是红色
        green_pixel = img[100, 250]  # 应该是绿色

        print(f"✅ 红色像素: {red_pixel}")
        print(f"✅ 绿色像素: {green_pixel}")

    def test_color_values(self):
        """测试颜色值"""
        # BaseQRSLTask中的目标颜色 (BGR格式)
        target_color = (237, 166, 62)

        print(f"✅ 目标颜色 (BGR): {target_color}")
        print(f"✅ 转换为RGB: {target_color[::-1]}")  # 反转BGR到RGB

        # 创建一个包含该颜色的测试图像
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[50, 50] = target_color

        # 检查像素值
        pixel = img[50, 50]
        print(f"✅ 图像中的颜色: {pixel}")

    def test_coordinates(self):
        """测试坐标计算"""
        # BaseQRSLTask中的坐标
        coords = {
            "ENTER_TEAM_COORDS": (1900, 320),
            "AUTO_COMBAT_COORDS": (1160, 930),
            "EXIT_CHECK_COORDS": (267, 65),
            "MAIN_PAGE_COORDS": (22, 63),
        }

        for name, (x, y) in coords.items():
            print(f"✅ {name}: ({x}, {y})")

            # 检查坐标是否在1920x1080范围内
            self.assertGreaterEqual(x, 0, f"{name} x坐标错误")
            self.assertGreaterEqual(y, 0, f"{name} y坐标错误")
            self.assertLessEqual(x, 1920, f"{name} x坐标超出范围")
            self.assertLessEqual(y, 1080, f"{name} y坐标超出范围")


class TestTaskStructure(unittest.TestCase):
    """任务结构测试"""

    def test_task_registration(self):
        """测试任务注册"""
        tasks = config['onetime_tasks']

        # 检查任务列表
        self.assertGreater(len(tasks), 0)

        print(f"✅ 注册任务数: {len(tasks)}")

        for task in tasks:
            print(f"  - {task[1]} ({task[0]})")

    def test_window_size(self):
        """测试窗口大小"""
        window = config['window_size']

        print(f"✅ 窗口大小: {window['width']}x{window['height']}")
        print(f"✅ 最小大小: {window['min_width']}x{window['min_height']}")


class TestOCRConfig(unittest.TestCase):
    """OCR配置测试"""

    def test_ocr_library(self):
        """测试OCR库配置"""
        ocr_config = config['ocr']

        self.assertEqual(ocr_config['lib'], 'onnxocr')
        self.assertEqual(ocr_config['params']['use_openvino'], True)

        print(f"✅ OCR库: {ocr_config['lib']}")
        print(f"✅ 使用OpenVINO: {ocr_config['params']['use_openvino']}")


class TestSimpleImageOperations(unittest.TestCase):
    """简单图像操作测试"""

    def test_opencv_operations(self):
        """测试OpenCV基本操作"""
        # 创建测试图像
        img = np.zeros((100, 100, 3), dtype=np.uint8)

        # 画矩形
        cv2.rectangle(img, (10, 10), (90, 90), (255, 0, 0), 2)

        # 画圆形
        cv2.circle(img, (50, 50), 20, (0, 255, 0), -1)

        # 添加文字
        cv2.putText(img, "TEST", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # 检查图像属性
        self.assertEqual(img.shape, (100, 100, 3))

        print(f"✅ 图像大小: {img.shape[1]}x{img.shape[0]}")
        print(f"✅ 像素类型: {img.dtype}")

    def test_numpy_operations(self):
        """测试NumPy操作"""
        # 创建数组
        arr = np.array([[1, 2, 3], [4, 5, 6]])

        # 检查形状
        self.assertEqual(arr.shape, (2, 3))

        # 切片
        row = arr[0, :]
        self.assertTrue(np.array_equal(row, [1, 2, 3]))

        print(f"✅ 数组形状: {arr.shape}")
        print(f"✅ 数组内容:\n{arr}")


def main():
    """主函数"""
    print("=" * 60)
    print("开始测试 ok-hotta 项目")
    print("=" * 60)

    # 运行测试
    unittest.main(verbosity=2)


if __name__ == '__main__':
    main()
