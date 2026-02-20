#!/usr/bin/env python3
"""
检查 LIBERO 环境中的动作空间和控制器配置
这个脚本会显示动作的具体形式和控制器类型
"""

import sys
sys.path.insert(0, "/home/e230112/yzj/openpi/LIBERO")

import robosuite as suite
import pathlib
from libero.libero import benchmark, get_libero_path
from libero.libero.envs import OffScreenRenderEnv

# 设置环境
task_suite = benchmark.get_benchmark_dict()["libero_object"]()
task = task_suite.get_task(0)
task_description = task.language
task_bddl_file = pathlib.Path(get_libero_path("bddl_files")) / task.problem_folder / task.bddl_file

# 创建环境 - 使用默认的 OSC_POSE 控制器
env_args = {"bddl_file_name": task_bddl_file, "camera_heights": 256, "camera_widths": 256}
env = OffScreenRenderEnv(**env_args)

# 输出控制器信息
print("=" * 80)
print("LIBERO 动作空间分析")
print("=" * 80)
print(f"\n任务描述: {task_description}")
print(f"\n任务 BDDL 文件: {task_bddl_file}")

# 检查机器人和控制器
for robot in env.robots:
    print(f"\n机器人: {robot.name}")
    print(f"控制器类型: {robot.controller.__class__.__name__}")
    print(f"控制器配置:")
    if hasattr(robot.controller, 'control_dim'):
        print(f"  - 控制维度: {robot.controller.control_dim}")
    if hasattr(robot.controller, 'input_max'):
        print(f"  - 输入最大值: {robot.controller.input_max}")
    if hasattr(robot.controller, 'input_min'):
        print(f"  - 输入最小值: {robot.controller.input_min}")
    if hasattr(robot.controller, 'output_max'):
        print(f"  - 输出最大值: {robot.controller.output_max}")
    if hasattr(robot.controller, 'output_min'):
        print(f"  - 输出最小值: {robot.controller.output_min}")
    
    # 检查控制器属性
    print(f"\n控制器详细信息:")
    controller = robot.controller
    for attr in dir(controller):
        if not attr.startswith('_') and attr not in ['update', 'reset_goal', 'run_controller', 'clip_control']:
            try:
                value = getattr(controller, attr)
                if not callable(value):
                    print(f"  - {attr}: {value}")
            except:
                pass

# 检查动作空间
print(f"\n动作空间信息:")
print(f"  - action_dim: {env.action_dim}")
print(f"  - action_spec: {env.action_spec}")

# 测试一个简单动作，看看它如何被传递
print("\n" + "=" * 80)
print("测试动作传递路径")
print("=" * 80)

# Reset 环境
env.reset()
initial_states = task_suite.get_task_init_states(0)
obs = env.set_init_state(initial_states[0])

# 创建一个测试动作 (7维: 3个位置 + 3个旋转 + 1个夹爪)
test_action = [0.01, 0.02, 0.03, 0.1, 0.2, 0.3, -1.0]
print(f"\n输入动作 (7维): {test_action}")
print(f"  - 位置增量 [0:3]: {test_action[:3]}")
print(f"  - 旋转增量 [3:6]: {test_action[3:6]}")
print(f"  - 夹爪动作 [6]: {test_action[6]}")

# 获取当前状态用于对比
print(f"\n执行前的机器人状态:")
print(f"  - EEF 位置: {obs['robot0_eef_pos']}")
print(f"  - EEF 四元数: {obs['robot0_eef_quat']}")
print(f"  - 关节位置: {obs['robot0_joint_pos']}")
print(f"  - 夹爪位置: {obs['robot0_gripper_qpos']}")

# 执行动作
obs_new, reward, done, info = env.step(test_action)

print(f"\n执行后的机器人状态:")
print(f"  - EEF 位置: {obs_new['robot0_eef_pos']}")
print(f"  - EEF 位置变化: {obs_new['robot0_eef_pos'] - obs['robot0_eef_pos']}")
print(f"  - EEF 四元数: {obs_new['robot0_eef_quat']}")
print(f"  - 关节位置: {obs_new['robot0_joint_pos']}")
print(f"  - 关节位置变化: {obs_new['robot0_joint_pos'] - obs['robot0_joint_pos']}")
print(f"  - 夹爪位置: {obs_new['robot0_gripper_qpos']}")

print("\n" + "=" * 80)
print("结论:")
print("=" * 80)
print("根据控制器类型和动作效果，可以判断:")
print("- 如果是 OSC_POSE: 动作是末端执行器（EEF）的增量位姿（delta pose）")
print("- 如果是 OSC_POSITION: 动作是末端执行器的增量位置（delta position）")
print("- 如果是 JOINT_POSITION: 动作是关节角度的增量（delta joint angles）")
print("\n动作的前3个值控制 EEF 的 x, y, z 增量")
print("动作的中间3个值控制 EEF 的旋转（轴角表示）")
print("动作的最后1个值控制夹爪开合（-1=闭合, 1=打开）")

env.close()
