# Codex / ChatGPT Pet v2 Specification & Atlas Reference

本文档定义了适用于 ChatGPT / OpenAI Codex 桌面宠物系统（如 `AgentPet`）及 CLI 的完整 **v2 规格图集（Spritesheet Atlas）** 标准。

---

## 1. 图集基础规格 (Atlas Geometry)

- **总分辨率**：`1536 × 2288` 像素（11 行 × 8 列）
- **单单元格尺寸 (Cell Size)**：`192 × 208` 像素
  - 宽度（Column Width）：`192` px
  - 高度（Row Height）：`208` px
- **基础地面参考线 (Baseline Y)**：`y = 186` px（相对于单元格顶部，角色双脚踩在地面的垂直坐标，留出底部安全裕量）
- **文件格式**：
  - 首选：`spritesheet.webp`（Lossless 8-bit RGBA WebP，体积极小，加载极快）
  - 备用：`spritesheet.png`（32-bit RGBA PNG，未压缩）
- **配置文件**：`pet.json`，放置在宠物同级目录下：
  ```json
  {
    "id": "my-pet-name",
    "displayName": "My Pet Name",
    "description": "One line about the pet.",
    "spriteVersionNumber": 2,
    "spritesheetPath": "spritesheet.webp"
  }
  ```

---

## 2. 状态映射与帧数约束 (Row & Frame Mapping)

每个状态占用图集的一整行（Row 0 到 Row 10）。**必须严格遵守各行的有效帧数（Frame Count）与透明填充规则**：

| 行索引 (Row) | 状态标识 (`state`) | 帧数限制 | 单元格范围 | 说明与要求 |
|:---:|:---|:---:|:---:|:---|
| **0** | `idle` | **6 + 1** | Col 0~5 (待机循环)<br>Col 6 (注视中立帧)<br>Col 7 (透明) | 常规呼吸、微闭眼等放松待机动画。<br>Col 6 必须存放正面中立姿态（扩展图集的中立槽，官方校验 `--require-v2` 下留空会报 `idle row 0 column 6 is empty or too sparse`），供装配时量取身份、比例与基线参考。<br>**Col 7 必须完全透明**（否则报 `idle row 0 unused column 7 is not transparent`）。<br>注：16 个注视方向全部在 Row 9/10，`000` 表示正上方；指针无方向的中立态回落到 idle，而不是这一格。 |
| **1** | `running-right` | **8** | Col 0~7 (全满) | 向右奔跑完整闭环步态动画，8 帧首尾无缝循环。 |
| **2** | `running-left` | **8** | Col 0~7 (全满) | 向左奔跑完整闭环步态动画，通常由 Row 1 进行逐帧水平镜像（Horizontal Mirror）。 |
| **3** | `waving` | **4** | Col 0~3 (招手致意)<br>Col 4~7 (透明) | 招手、打招呼、胜利致意动画。<br>**Col 4~7 必须 100% 完全透明**，多余像素将导致校验报错。 |
| **4** | `jumping` | **5** | Col 0~4 (跳跃弧线)<br>Col 5~7 (透明) | 蓄力、起跳升空、最高极点、下落、落地缓冲。<br>**Col 5~7 必须 100% 完全透明**。 |
| **5** | `failed` | **8** | Col 0~7 (全满) | 任务失败/报错反应。标准流程：受击后仰 $\rightarrow$ 逆时针翻滚/失衡 $\rightarrow$ 倒地定格。 |
| **6** | `waiting` | **6** | Col 0~5 (等待输入)<br>Col 6~7 (透明) | 等待用户输入/交互。姿态需明显区别于 Idle（例如战斗戒备、托腮深思、环顾四周、呼吸灯闪烁等）。<br>**Col 6~7 必须完全透明**。 |
| **7** | `running` | **6** | Col 0~5 (任务计算)<br>Col 6~7 (透明) | Codex 后台正在执行任务/计算。使用 6 帧对称奔跑或能量蓄力推进循环。<br>**Col 6~7 必须完全透明**。 |
| **8** | `review` | **6** | Col 0~5 (审核检查)<br>Col 6~7 (透明) | 检查输出/审查状态。平举手炮连续射击、翻阅文件、向下专注审视。<br>**Col 6~7 必须完全透明**。 |
| **9** | `look-000-to-157.5` | **8** | Col 0~7 (全满) | 光标注视上半圈顺时针方向：<br>000° (直上), 022.5°, 045°, 067.5°, 090° (直右), 112.5°, 135°, 157.5° (右下)。 |
| **10** | `look-180-to-337.5` | **8** | Col 0~7 (全满) | 光标注视下半圈顺时针方向：<br>180° (直下), 202.5°, 225°, 247.5°, 270° (直左), 292.5°, 315°, 337.5° (左上)。 |

---

## 3. 严格校验规范 (`validate_atlas.py --require-v2`)

官方验证脚本对图集施加了 3 个绝对不允许违背的硬性限制：

1. **未用单元格纯净度 (Unused Column Purity)**：
   - Row 3 的 Col 4~7、Row 4 的 Col 5~7、Row 6 的 Col 6~7、Row 7 的 Col 6~7、Row 8 的 Col 6~7 **不能包含任何一个非透明像素**（哪怕只有 1 个 alpha > 0 的半透明像素也会直接报错抛出 `unused column is not transparent`）。
2. **零透明残留像素 (Zero Transparent RGB Residue)**：
   - 在 RGBA 图像中，很多图像编辑器在保存透明区域时会保留底层的 RGB 数据（例如 `(255, 255, 255, 0)` 或 `(0, 255, 255, 0)`）。
   - 校验器检查：若 `A == 0`，则 RGB 必须全为 0（即 `[0, 0, 0, 0]`）。
   - 任何非零 RGB 残留都会报 `transparent_rgb_residue_pixels > 0` 警告/错误。
3. **色彩渗漏与边缘光晕 (Chroma Leak & Chroma Fringe)**：
   - 必须彻底清除原始 Sprite Sheet 背景色抠图留下的边缘毛刺（Chroma Fringe）。
