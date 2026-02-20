#!/usr/bin/env python3
"""
检查 LIBERO 训练数据中动作的格式和模型输出

关键发现：从 norm_stats.json 可以看出：
- actions mean: [0.027, 0.089, -0.100, ...]
- actions std: [0.331, 0.372, 0.452, ...]  
- actions q01/q99: [-0.747~0.937, -0.796~0.859, -0.938~0.937, ...]

这些数值范围很大，说明训练数据中的动作不是小的 delta，
而可能是归一化后的某种目标位置或其他表示。
"""

import json
import numpy as np

# 读取归一化统计信息
norm_stats_path = "pi05_libero_ckpt/assets/physical-intelligence/libero/norm_stats.json"
with open(norm_stats_path) as f:
    norm_stats = json.load(f)["norm_stats"]

print("=" * 80)
print("LIBERO OpenPI 0.5 动作空间分析")
print("=" * 80)

print("\n归一化统计信息 (Actions):")
actions_stats = norm_stats["actions"]
print(f"  Mean:  {np.array(actions_stats['mean'])}")
print(f"  Std:   {np.array(actions_stats['std'])}")
print(f"  Q01:   {np.array(actions_stats['q01'])}")
print(f"  Q99:   {np.array(actions_stats['q99'])}")

print("\n归一化统计信息 (State):")
state_stats = norm_stats["state"]
print(f"  Mean:  {np.array(state_stats['mean'])}")
print(f"  Std:   {np.array(state_stats['std'])}")
print(f"  Q01:   {np.array(state_stats['q01'])}")
print(f"  Q99:   {np.array(state_stats['q99'])}")

print("\n" + "=" * 80)
print("分析流程：")
print("=" * 80)
print("""
1. 训练时动作被归一化：
   normalized_action = (raw_action - mean) / (std + 1e-6)
   
2. 模型学习输出归一化的动作值（约在 [-3, 3] 范围）

3. 推理时反归一化：
   raw_action = normalized_action * (std + 1e-6) + mean
   
4. raw_action（反归一化后）被发送到环境

问题：raw_action 是什么？
- 如果是 delta EEF pose → 应该在 ±0.05 范围内
- 如果是 absolute EEF pose → 可能在工作空间范围内（如 [0.3, 0.8]）
- 如果是 normalized delta → 需要进一步转换
""")

# 模拟一个推理例子
print("\n" + "=" * 80)
print("模拟推理示例：")
print("=" * 80)

# 假设模型输出的归一化动作（通常在 [-2, 2] 范围内）
normalized_action = np.array([0.5, 1.0, -1.5, 0.1, 0.2, -0.3, 0.8])
print(f"\n1. 模型输出（归一化）: {normalized_action}")

# 反归一化
mean = np.array(actions_stats["mean"])
std = np.array(actions_stats["std"])
raw_action = normalized_action * (std + 1e-6) + mean
print(f"2. 反归一化后:         {raw_action}")
print(f"   - 位置部分 [0:3]:   {raw_action[:3]}")
print(f"   - 旋转部分 [3:6]:   {raw_action[3:6]}")
print(f"   - 夹爪 [6]:         {raw_action[6]}")

print("\n" + "=" * 80)
print("关键问题：")
print("=" * 80)
print("""
从用户的日志可以看到：
  pos[0:3]=[0.15059906, 0.4091188, -0.50334028]

这些值太大，不像是 delta（增量）！

可能的解释：
1. **训练数据使用的是目标位置（target pose）而不是 delta**
   - 训练时：action = target_eef_pose  
   - 推理时：policy 输出 target_eef_pose
   - 问题：这与 robosuite OSC_POSE 控制器期望的 delta 不匹配！
   
2. **有额外的转换步骤未执行**
   - 应该有：target_pose →  delta = target - current
   - 但这个转换可能缺失
   
3. **训练数据的归一化方式不同**
   - 可能训练数据本身就有问题

建议：检查原始 LIBERO 数据集的动作格式！
""")
