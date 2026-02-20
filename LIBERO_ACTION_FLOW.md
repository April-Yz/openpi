# LIBERO 动作执行流程详解

## 核心问题：模型输出的是 Delta Action 吗？

**答案：是的！模型直接输出 Delta Actions（增量），控制器自动加上当前状态。**

## 完整流程

### 1. 模型输出 (policy.py)
```python
# 模型输出 7 维 delta actions
outputs = {
    "actions": self._sample_actions(...)  # shape: (action_horizon, 7)
}
# 前 3 维: delta position (dx, dy, dz)
# 中间 3 维: delta rotation (轴角表示)
# 最后 1 维: gripper (-1=闭合, 1=打开)
```

### 2. 动作传递到环境 (main.py)
```python
action_chunk = client.infer(element)["actions"]
action = action_plan.popleft()  # 单步动作: [dx, dy, dz, drx, dry, drz, gripper]
obs, reward, done, info = env.step(action.tolist())
```

### 3. 控制器处理 (robosuite/controllers/osc.py)

在 OSC_POSE 控制器的 `set_goal()` 方法中：

```python
def set_goal(self, action, set_pos=None, set_ori=None):
    # action 是模型输出的 delta values
    delta = action  # 在 impedance_mode='fixed' 时
    
    # 缩放 delta
    scaled_delta = self.scale_action(delta)
    
    # **关键步骤**: 计算目标位置 = 当前位置 + delta
    self.goal_pos = set_goal_position(
        scaled_delta[:3],      # delta position
        self.ee_pos,           # current position
        position_limit=self.position_limits,
        set_pos=set_pos
    )
    
    # 同样，计算目标旋转 = 当前旋转 + delta rotation
    self.goal_ori = set_goal_orientation(
        scaled_delta[3:],      # delta rotation (axis-angle)
        self.ee_ori_mat,       # current orientation
        orientation_limit=self.orientation_limits,
        set_ori=set_ori
    )
```

### 4. 核心函数 (robosuite/utils/control_utils.py)

```python
def set_goal_position(delta, current_position, position_limit=None, set_pos=None):
    """
    计算目标位置，将 delta 加到当前位置上
    
    Args:
        delta: 期望的相对位置变化 (模型输出)
        current_position: 当前位置 (机器人状态)
    
    Returns:
        goal_position: 目标位置 (绝对坐标)
    """
    if set_pos is not None:
        goal_position = set_pos
    else:
        # **这里是关键**: current + delta
        goal_position = current_position + delta
    
    # 裁剪到限制范围
    if position_limit is not None:
        goal_position = np.clip(goal_position, position_limit[0], position_limit[1])
    
    return goal_position
```

### 5. 控制器计算关节扭矩

```python
def run_controller(self):
    """
    基于目标位置，计算需要的关节扭矩
    """
    # 计算位置误差
    position_error = self.goal_pos - self.ee_pos
    
    # 通过雅可比矩阵和 PD 控制计算关节扭矩
    torques = self._compute_joint_torques(position_error, ...)
    
    return torques
```

## 总结

```
模型输出 (Delta EEF)
    ↓
[dx, dy, dz, drx, dry, drz, gripper]
    ↓
控制器接收 delta
    ↓
goal_position = current_position + delta_position
goal_orientation = current_orientation + delta_orientation
    ↓
计算位置/旋转误差
    ↓
通过逆运动学 + 雅可比矩阵计算关节扭矩/位置
    ↓
发送到机器人执行
```

## 关键点

1. ✅ **模型输出**: Delta Actions（相对增量）
2. ✅ **自动累加**: 控制器内部自动执行 `goal = current + delta`
3. ✅ **控制空间**: 末端执行器（EEF）位姿空间，不是关节空间
4. ✅ **坐标系**: 世界坐标系（全局坐标）

## 数值范围参考

从训练数据看，delta actions 的典型范围：
- Delta Position: [-0.05, 0.05] (米)
- Delta Rotation: [-0.5, 0.5] (弧度，轴角表示)
- Gripper: {-1.0, 1.0}

如果你在推理时看到的动作值在这个范围内，说明模型正常输出 delta actions。
