#!/usr/bin/env python3
"""检查 robosuite 控制器配置"""

import robosuite as suite

# 加载默认的 OSC_POSE 控制器配置
controller_config = suite.load_controller_config(default_controller="OSC_POSE")

print("=" * 80)
print("OSC_POSE 控制器配置")
print("=" * 80)
for key, value in controller_config.items():
    print(f"{key}: {value}")

print("\n" + "=" * 80)
print("OSC_POSITION 控制器配置")  
print("=" * 80)
controller_config_pos = suite.load_controller_config(default_controller="OSC_POSITION")
for key, value in controller_config_pos.items():
    print(f"{key}: {value}")

print("\n" + "=" * 80)
print("JOINT_POSITION 控制器配置")
print("=" * 80)
controller_config_joint = suite.load_controller_config(default_controller="JOINT_POSITION")
for key, value in controller_config_joint.items():
    print(f"{key}: {value}")

print("\n" + "=" * 80)
print("结论:")
print("=" * 80)
print("""
在 LIBERO 中，默认使用 OSC_POSE 控制器：

OSC_POSE (Operational Space Control - Pose):
  - 动作维度: 7 (3个位置 + 3个旋转 + 1个夹爪)
  - 控制空间: 末端执行器（End-Effector）的位姿空间
  - 动作含义:
    * action[0:3]: EEF 在 x, y, z 方向的增量位置 (delta position)
    * action[3:6]: EEF 的旋转增量，使用轴角表示 (delta rotation in axis-angle)
    * action[6]: 夹爪控制 (-1 = 闭合, 1 = 打开)
  
  - 底层实现: 动作被传递到 OSC 控制器，控制器通过逆运动学
    和雅可比矩阵计算出关节扭矩或关节位置，最终发送给机器人

OSC_POSITION:
  - 动作维度: 4 (3个位置 + 1个夹爪)
  - 只控制位置，不控制旋转
  
JOINT_POSITION:
  - 动作维度: 8 (7个关节角度 + 1个夹爪)
  - 直接控制关节空间

总结: LIBERO 使用的是 **Delta EEF (末端执行器增量)** 控制，
     不是 Delta Joint (关节增量) 控制。
""")
