import time
from ok import TriggerTask, TaskDisabledException
from qfluentwidgets import FluentIcon
from src.config import key_config_option  # 从同一配置项读取

class AutoSkillTask(TriggerTask):
    """自动释放技能触发器"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "自动技能"
        self.description = "每隔一段时间自动按下技能键"
        self.icon = FluentIcon.SYNC
        self.default_config.update({
            '技能间隔': 30,  # 默认30秒
        })
        self.config_description = {
            '技能间隔': '自动按下技能键的时间间隔（秒）',
        }
        self.last_skill_time = 0

    def run(self):
        try:
            # 从游戏按键配置中获取技能键
            global_config = self.get_global_config(key_config_option)
            skill_key = global_config.get('技能键', 'e')
            interval = self.config.get('技能间隔', 30)

            current_time = time.time()
            if current_time - self.last_skill_time >= interval:
                self.log_info(f"自动按下技能键 [{skill_key}]")
                self.send_key_down(skill_key)
                self.sleep(0.1)
                self.send_key_up(skill_key)
                self.last_skill_time = current_time
        except TaskDisabledException:
            pass
        except Exception as e:
            self.log_error(f"自动技能执行异常: {e}")