import json
from maa.custom_action import CustomAction
from maa.context import Context
from maa.agent.agent_server import AgentServer


# ==========================================
# 使用方法3：通过 AgentServer 装饰器直接注册
# ==========================================
@AgentServer.custom_action("SkillCombo")
class SkillCombo(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        # 1. 提取你需要在配置里动态改变的长按时间 (毫秒)
        param = {}
        if argv.custom_action_param:
            try:
                param = json.loads(argv.custom_action_param)
            except Exception as e:
                print(f"参数解析失败，将使用默认参数。原因: {e}")

        # 获取配置的时间，默认 3000 毫秒（3秒）
        hold_time_ms = param.get("hold_time_ms", 3000)

        # 2. 纯通过字典动态生成流水线任务 (完全不触碰 Controller)
        # 将按键 e, b, 1, 2, 4 和长按的操作定义为标准 MaaFramework 任务
        override_pipeline = {
            "Task_Press_E": {
                "action": "Key",
                "key": [69],  # E 键的系统键码
                "post_delay": 50,  # 稍微延迟防吞键
                "next": ["Task_Press_B"]
            },
            "Task_Press_B": {
                "action": "Key",
                "key": [66],  # B 键
                "post_delay": 50,
                "next": ["Task_Press_1"]
            },
            "Task_Press_1": {
                "action": "Key",
                "key": [49],  # 1 键
                "post_delay": 50,
                "next": ["Task_Press_2"]
            },
            "Task_Press_2": {
                "action": "Key",
                "key": [50],  # 2 键
                "post_delay": 50,
                "next": ["Task_Press_4"]
            },
            "Task_Press_4": {
                "action": "Key",
                "key": [52],  # 4 键
                "post_delay": 50,
                "next": ["Task_Hold_Space"]
            },
            "Task_Hold_Space": {
                # 【长按的实现】
                # 通过 MaaFramework 标准的 Swipe(滑动) 机制模拟长按。
                # 假设你游戏内的“空格/跳跃”对应屏幕上的坐标 [600, 600]
                "action": "Swipe",
                "begin": [600, 600, 10, 10],
                "end": [600, 600, 10, 10],  # 起点和终点相同，即原地长按
                "duration": hold_time_ms  # 读取我们传入的动态时间
            }
        }

        # 3. 仅从 Context 中执行任务！将这套动态构建的流水线抛给 Maa 核心去跑
        print(f"AgentServer: 正在由 Context 执行按键任务流，长按时间={hold_time_ms}ms")
        result = context.run_task("Task_Press_E", override_pipeline)

        # 返回原生动作链路的最终成功/失败状态
        return result.success