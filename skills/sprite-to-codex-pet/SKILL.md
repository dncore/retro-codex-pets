---
name: sprite-to-codex-pet
description: >-
  Converts arbitrary, non-standard sprite sheets (retro games, SNES, GBA, Arcade, MUGEN, fan art)
  into fully compliant, perfectly aligned ChatGPT / OpenAI Codex v2 desktop pets (AgentPet).
  Use this skill whenever a user provides an existing character sprite sheet or image to turn into a
  Codex desktop pet, or when fixing/tuning animations, alignment, jitter, loops, or cursor tracking.
---

# Sprite to Codex Pet (v2 Specification)

本 Skill 用于指导 Agent 将任意来源的非标准角色精灵图（如 SNES/GBA/Arcade 复古游戏贴图、MUGEN 图包、自定义像素画）高保真地转换、补全、装配并安装为标准 **ChatGPT / OpenAI Codex v2 桌面宠物（AgentPet）**。

> [!IMPORTANT]
> **核心工作原则**：严禁直接使用生图 AI（如 Imagen/DALL-E）去重新生成已有角色的多帧动画！AI 生成会导致相邻帧比例失调、五官撕裂、色卡溢色及风格崩坏。正确的做法是：**100% 从原图提取原始像素切片 + 4x 最近邻缩放 + 算法合成缺失动作 + 严格图集装配与校验**。

---

## 知识库与规范索引

在开始制作前，建议查阅以下核心文档：
- [Codex v2 图集规范与状态帧数矩阵](./references/codex_v2_pet_spec.md)
- [踩坑经验与黄金解决方案](./references/common_pitfalls_and_fixes.md)

---

## 1. Codex v2 图集基础参数 (Master Spec)

- **总分辨率**：`1536 × 2288` 像素（11 行 × 8 列网格）
- **单元格尺寸**：`192 × 208` 像素
- **基准地面线**：`BASELINE_Y = 186`（角色脚底所在垂直坐标）
- **配置文件**：`pet.json`
  ```json
  {
    "id": "<pet_id>",
    "displayName": "<Pet Name>",
    "description": "<one-line description>",
    "spriteVersionNumber": 2,
    "spritesheetPath": "spritesheet.webp"
  }
  ```
- **行帧数限制表 (必须严格执行，超出或非透明填充将校验失败)**：
  - **Row 0 (`idle`)**：6 帧待机（Col 0~5）+ 第 6 列中立槽（扩展图集必需，空则该列报 `empty or too sparse`；第 7 列必须完全透明）
  - **Row 1 (`running-right`)**：8 帧无缝循环奔跑（全满）
  - **Row 2 (`running-left`)**：8 帧向左奔跑（由 Row 1 水平镜像）
  - **Row 3 (`waving`)**：**严格 4 帧**（第 4~7 列必须 100% 透明）
  - **Row 4 (`jumping`)**：**严格 5 帧**（第 5~7 列必须 100% 透明）
  - **Row 5 (`failed`)**：8 帧受击倒地（逆时针旋转后仰）
  - **Row 6 (`waiting`)**：**严格 6 帧**（第 6~7 列必须透明，戒备站姿/呼吸灯/慢眨眼）
  - **Row 7 (`running` 任务状态)**：**严格 6 帧**（第 6~7 列必须透明，6 帧对称奔跑）
  - **Row 8 (`review` 检查状态)**：**严格 6 帧**（第 6~7 列必须透明，平射开火/子弹飞出屏幕）
  - **Row 9 (`look-000-to-157.5`)**：8 帧顺时针上方到右下方注视（0° 至 157.5°）
  - **Row 10 (`look-180-to-337.5`)**：8 帧顺时针正下方到左上方注视（180° 至 337.5°）

---

## 2. 标准化操作流程 (Step-by-Step Workflow)

### 第一步：原始图分析与色彩去底 (Chroma Cleaning)
1. 观察原图背景色（如纯品红 `#FF00FF`、纯青 `#00FFFF` 或纯黑）。
2. 调用清洗脚本，消除背景并抹去文本水印：
   ```bash
   python3 scripts/chroma_cleaner.py \
     input_sheet.png clean_sheet.png --tolerance 15
   ```
3. 确保所有 `Alpha == 0` 的区域其 RGB 绝对清零为 `(0, 0, 0, 0)`。

---

### 第二步：切片提取与黄金步态选择 (Frame Harvesting)
1. **确定缩放倍率**：复古 Sprite 高度通常在 30~48px 之间，在 208px 单元格中，最佳缩放比为 **4x**（`Image.NEAREST` 整数最近邻倍率）。
2. **奔跑黄金循环 (Row 1, 2, 7)**：
   - 绝大多数游戏原图包含 1 帧起跑推蹬动作（第 0 帧）和 10 帧交替奔跑循环（1~10 帧）。
   - **8 帧奔跑 (`running-right`)**：必须采用左右腿各 4 阶段的黄金序列：
     `[2, 3, 4, 5, 7, 8, 9, 10]`
     - 腿 A：2(前摆) $\rightarrow$ 3(着地) $\rightarrow$ 4(后蹬) $\rightarrow$ 5(回收向前)
     - 腿 B：7(前摆) $\rightarrow$ 8(着地) $\rightarrow$ 9(后蹬) $\rightarrow$ 10(回收向前)
     > **注意**：切勿漏掉 5 和 10（回收相），否则蹬地后直接跨步会导致严重断帧卡顿！
   - **6 帧奔跑 (`running` 任务状态)**：采用 `[2, 3, 5, 7, 8, 10]` 对称步态。

---

### 第三步：解剖学中心锚定（彻底杜绝抖动与漂移）
严禁使用整图 Bounding Box 居中，必须根据解剖学特征实施**绝对锚定**：

1. **站立/等待/招手/注视状态 (Row 0, 3, 6, 9, 10)**：
   - 提取站立基准帧双脚支撑面中线 `feet_center = (xs.min() + xs.max()) / 2.0`。
   - 计算对齐位移：`custom_target_x = int(round(96.0 - feet_center * SCALE))`。
   - 所有站立姿态（包括眨眼、待机、呼吸、看各个方向）双脚支撑中心严格锁定在 `96.0px ~ 97.0px`，漂移量必须严格为 `0.0px`！

2. **奔跑状态 (Row 1, 2, 7) —— 水平与垂直零抖动黄金法则**：
   - **垂直绝对地面锁定 (Ground Invariant)**：
     真实跑步中地面绝对不动！所有脚底着地帧的纵坐标必须死死锁定在基准地面线 `BASELINE_Y = 186`（`target_y = BASELINE_Y - sc.height`，确保 `bot_y = 185`）。严禁强制固定面部高度 `target_face_y`，否则会导致脚底在地面上下跳动 8px！仅摆腿回收帧（Passing Frame）允许脚底自然离地 3px（`bot_y = 182`）。
   - **水平面部锚点 (排除金翼/金甲高光污染)**：
     提取头部区域前 40% 高度（`arr[:int(bh * 0.40)]`），使用色相差 `r - g >= 25` 精准检测真实面部肉色，100% 滤除高光金甲/金翼（金黄 `r - g <= 18`）。将面部中线稳定锁定于 `target_face_x = 110.0 ~ 114.0px`（向左镜像为 `192 - target_face_x`），全行动作头部水平漂移量严格 `<= 1.0px`。
   - **拖拽方向物理校验**：
     Row 1（`running-right`）必须面朝屏幕右侧（前进向右）；Row 2（`running-left`）必须面朝屏幕左侧（前进向左），避免拖拽时反向倒车。

3. **跳跃状态 (Row 4 Jumping / 鼠标悬停触发动作)**：
   - **防截断与起跳着地蹲姿**：
     Frame 0（起跳预备）与 Frame 4（着地缓冲）**必须选用原画中双脚完全平踏地面的着地蹲姿（Landing Crouch）**，脚底绝对对齐 `BASELINE_Y = 186`（`bot_y = 185`），鞋头白罩、装甲扣、防滑鞋底 100% 完整保留，严禁使用原图撕图残缺的空中飞踢帧当作地面起跳帧！
   - **安全起跳弧线**：
     垂直偏移配置为 `jump_offsets = [0, -8, -14, -8, 0]`，顶点处预留足够头顶安全空间（`top_y >= 4`），水平以重心（Center of Mass）对称居中 `96.0px`。

4. **开火/审核状态 (Row 8)**：
   - 人物身体与双脚严格对齐站立中心（如 `char_x = 32` 或 `48`，脚底中心等于 96.0px）。
   - 武器子弹与等离子冲击波层独立向前平移，允许飞出右边界（Off-screen Clipping）。
   - **防列污染截断**：向右延伸的武器或冲击波在粘贴时必须严格截断于本单元格右边界（`min(sw, CELL_W - tx)`），严禁溢出粘贴到相邻右侧单元格导致鬼影！
   - **严禁整图 Clamp**：严禁使用 `clamped_x = min(CELL_W - sw, target_x)`！攻击动作手臂伸展时 `sw`变大，此 clamp 会将整个人物强行向左推移 10~40px，引发灾难级水平抖动！

5. **待机微动 (Row 0 Idle) 与 等待呼吸 (Row 6 Waiting)**：
   - **严禁切片粗暴位移**：严禁将人物胸部以上直接横向切开平移！这会导致手臂、手肘、拳头与武器在接缝处断裂撕裂。
   - **呼吸微动实现**：优先采用原图自带的 Idle 喘息循环；若原图为单帧，必须在胸腔轮廓内做像素扩张与色阶脉冲，肢体与关节轮廓保持闭合。
   - **Waiting 发光点精准定位**：洛克人/X等机体 waiting 状态严格仅闪烁**头顶/眼睛正上方的额头红色能量指示灯（Forehead Gem）**，严禁闪烁耳罩指示灯（Ear Pods）、护肩或强行覆盖眨眼黑框！
   - **拒绝 6 帧纯静态**：Waiting 必须具备 6 帧完整的能量呼吸脉冲循环，严禁 6 帧完全复制黏贴！

---

### 第四步：解剖学无缝合成（彻底杜绝身体撕裂与断头）

1. **光标注视 16 方向 (Row 9 & Row 10)**：
   - **双半球姿态协调**：右半球（0°~157.5°）采用右向站立身体基底；左半球（180°~337.5°）采用左向镜像身体基底，避免向后注视时“180度反向拧脖子”。
   - **颈部分离点与缝合**：在下巴轮廓与领口交界处严格横切。仰视（`off_y < 0`）时必须向上延展领口像素（Neck Fill），确保任何角度零空隙、零突刺、零断头。
2. **招手状态 Waving (Row 3)**：
   - 严格选择角色**正面朝向**的胜利/举手动作，严禁将背身抓投或蹲伏拔刀动作错选为招手！
   - 必须构成往复循环序列：`[s1, s2, s3, s2]`（抬手 $\rightarrow$ 高举欢呼 $\rightarrow$ 放下 $\rightarrow$ 抬手），杜绝在第 4 帧骤变姿势或带有相邻精灵图的脚部残影。
3. **受击/失败状态 Failed (Row 5)**：
   - 保证 8 帧完整受挫进程（受击后仰 $\rightarrow$ 金黄闪烁 $\rightarrow$ 倒地缓冲 $\rightarrow$ 贴地瘫倒），杜绝 2~3 帧粗糙闪现。
4. **奔跑动作等步长对称采样 (Row 1, 2, 7)**：
   - 16 帧原画奔跑转换为 8 帧时，必须采用**等步长步态**（`[1, 3, 5, 7, 9, 11, 13, 15]` 或 `[0, 2, 4, 6, 8, 10, 12, 14]`），步长均为恒定 2 帧，首尾无缝咬合，彻底杜绝步频不均与循环卡顿。
   - 6 帧奔跑对称采样：左右腿各 3 帧（如 `[1, 5, 7, 9, 13, 15]`）。

---

### 第五步：尺度安全法则（彻底杜绝边界截断）
- **缩放倍率计算公式**：
  若原图最大精灵图宽度 $W_{max}$ 或高度 $H_{max}$ 满足：
  $W_{max} \times 4 > 180$ 或 $H_{max} \times 4 > 195$ 时，**严禁使用 4x 缩放**！必须降为 **3x 缩放**！
- 例如：PS1 Mega Man X 精灵图（宽 48px，高 49px）：
  $48 \times 4 = 192$（100% 占满单元格，必被截断） $\rightarrow$ 必须采用 **3x 缩放**（$48 \times 3 = 144$px，四周留出充足缓冲边距）。

---

### 第六步：装配、清理透明残留与编译
在保存图集前，执行关键清零与双格式导出：
```python
# 强制清除所有透明像素残留的 RGB 脏数据
arr = np.array(atlas)
arr[arr[:, :, 3] == 0] = [0, 0, 0, 0]
final_atlas = Image.fromarray(arr)

# 保存标准 WebP 与 PNG
final_atlas.save("spritesheet.webp", "WEBP", lossless=True)
final_atlas.save("spritesheet.png")
```

---

### 第七步：自动化质检诊断与交付门禁 (Automated Quality Gate)
生成图集后，必须依次运行**双重门禁校验**：

1. **全面深度体检（`pet_doctor.py`）**：
   ```bash
   python3 scripts/pet_doctor.py <spritesheet_path>
   ```
   **检查项矩阵**：
   - [x] **几何结构**：1536x2288，11 行 8 列，192x208 单元格。
   - [x] **透明纯净度**：透明像素零 RGB 残留，未用单元格 100% 透明。
   - [x] **边缘截断审计**：检测全部有效帧的 4 边缘（`x=0, 191`, `y=0, 207`）非零像素（Row 8 允许开火出界）。
   - [x] **重心与双脚晃动审计**：Row 0, 3, 6, 9, 10 双脚支撑中心漂移量严格 `<= 2.0px`。
   - [x] **奔跑循环步态审计**：检测 Row 1, 2, 7 是否存在重复停顿帧（Duplicate Frame Freeze）或过大抖动。
   - [x] **解剖学连续性审计**：注视行与动作行是否存在颈部断裂洞隙（Neck Gap）。

2. **官方图集规范验证（`validate_atlas.py`）**：
   ```bash
   # the validator ships with the separate hatch-pet skill, if you have it installed:
   python3 <skills-dir>/hatch-pet/scripts/validate_atlas.py <spritesheet_path> --require-v2
   ```
   输出必须为 `"ok": true`。

3. **安装并热重启验证**：
   ```bash
   mkdir -p ~/.codex/pets/<pet_name>
   cp pet.json spritesheet.webp spritesheet.png ~/.codex/pets/<pet_name>/
   killall AgentPet && sleep 1 && open -a /Applications/AgentPet.app
   ```

---

## 3. 附带辅助脚本清单

| 脚本路径 | 功能说明 |
|---|---|
| [`scripts/pet_doctor.py`](./scripts/pet_doctor.py) | **核心质量卫士**：自动化检测图集尺寸、透明纯净度、边缘截断、双脚/头部抖动漂移、解剖学撕裂、奔跑卡顿冻结 |
| [`scripts/chroma_cleaner.py`](./scripts/chroma_cleaner.py) | 自动色彩去底、保护内部调色板、强制透明区域 RGB 纯净清零 |
| [`scripts/check_pet.py`](./scripts/check_pet.py) | 基础图集参数与帧数占用快检 |
| [`scripts/test_loop_generator.py`](./scripts/test_loop_generator.py) | 快速将切片组合生成 GIF，用于循环平滑度与首尾衔接视觉验证 |
