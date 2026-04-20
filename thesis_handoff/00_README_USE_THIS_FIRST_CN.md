# 毕业论文资料交接包使用说明

## 1. 这套资料包是什么
这不是毕业论文正文，而是一套面向“新 GPT 对话”的论文上下文资料包。它的目标是：即使下一个 GPT 看不到当前仓库，也能仅依据这些文档继续帮助你完成本科毕业论文写作。

本资料包只基于当前仓库的真实内容、当前可读取到的 `git` 历史、目录结构、`README.md`、ROS1 package 文件、launch/config/script 源码，以及本次检查中能直接确认的路径与环境前提来整理。没有自动解析 `原视频.mp4` 和 `识别视频.mp4` 的视频内容，因此任何实验效果结论都没有从视频中推导。

## 2. 文件清单与用途

| 文件名 | 作用 | 适合在新 GPT 中怎么用 |
| --- | --- | --- |
| `00_README_USE_THIS_FIRST_CN.md` | 本说明文件 | 先看，了解资料包结构与可信度边界 |
| `01_THESIS_CONTEXT_MASTER_CN.md` | 最重要的主文档，自包含项目说明 | 新 GPT 的首要上下文材料 |
| `02_THESIS_FACTS.json` | 结构化事实清单，方便机器读取 | 让新 GPT 快速提取节点、话题、命令、限制 |
| `03_THESIS_EVIDENCE_MAP_CN.md` | 事实和证据来源的映射 | 写论文时区分“代码确认”与“推断/待确认” |
| `04_THESIS_OUTLINE_CN.md` | 本科毕业论文提纲 | 让新 GPT 按章节帮你展开写作 |
| `05_NEW_CHAT_BOOTSTRAP_PROMPT_CN.md` | 给新 GPT 的启动提示词 | 直接复制到新对话框的第一条消息 |
| `06_MISSING_INFO_CHECKLIST_CN.md` | 论文还缺什么信息的清单 | 后续补实验、补截图、补参数时对照使用 |

## 3. 推荐发送顺序
如果你准备把资料复制到新的 GPT 对话，建议按下面顺序发送：

1. 先发送 `05_NEW_CHAT_BOOTSTRAP_PROMPT_CN.md` 的全文。
2. 再发送 `01_THESIS_CONTEXT_MASTER_CN.md`。
3. 再发送 `02_THESIS_FACTS.json`。
4. 如果新 GPT 要求“给我证据来源”或“不要写错”，再补发 `03_THESIS_EVIDENCE_MAP_CN.md`。
5. 如果你希望它直接进入章节写作，再补发 `04_THESIS_OUTLINE_CN.md`。
6. 等开始写“实验与结果分析”“不足与展望”时，再补发 `06_MISSING_INFO_CHECKLIST_CN.md`。

如果上下文长度有限，优先级最高的是：

1. `05_NEW_CHAT_BOOTSTRAP_PROMPT_CN.md`
2. `01_THESIS_CONTEXT_MASTER_CN.md`
3. `02_THESIS_FACTS.json`

## 4. 本资料包中的可信度标记怎么理解
为避免新 GPT 把未知内容写成既定事实，本资料包把内容分成三类：

| 标记 | 含义 |
| --- | --- |
| `代码确认事实` | 可以直接从代码、launch、config、package.xml、CMakeLists.txt、README、目录结构或 git 历史中看到 |
| `结构推断` / `根据当前代码推断` | 当前仓库没有直接说明，但从现有结构、调用关系、提交历史可以做出较稳妥判断 |
| `待人工确认` / `未知` | 当前仓库中没有证据，或者只有示例路径，没有真实文件/实测结果支撑 |

## 5. 这套资料包里最重要的事实边界

1. 当前仓库里确实已经存在融合后的源码，而不是只有两个独立系统。
2. 当前融合方式不是“重写一个全新的控制器”，而是“新增 YOLO 检测前端，并对原 `line_detector.py` 做了最小输入适配”。
3. `git` 历史可以确认一次名为 `Add seam tracking integration` 的提交，新增了 `yolo_seam_detector.py`、`seam_tracking.launch`、`README.md`，并修改了 `line_detector.py` 和 `robot_vision/package.xml`。
4. 根目录 `README.md` 给出了 `model_path:=../yolo/runs/train/exp17/weights/best.pt` 的运行示例，但当前仓库中并不存在这个权重文件，因此它只能视为“示例路径”，不能视为仓库内已交付文件。
5. 仓库中没有直接提供检测精度、跟踪误差、速度指标、实验截图、硬件型号表、相机详细参数表，因此论文的实验与结果部分仍然需要你后续人工补充。
6. 两个 mp4 文件只被当作“参考素材存在”来记录，没有从视频内容中自动得出任何实验结论。

## 6. 你接下来最该怎么用
如果你的目标是让新的 GPT 继续写毕业论文，最有效的方式是：

1. 把 `05_NEW_CHAT_BOOTSTRAP_PROMPT_CN.md` 复制为新对话第一条消息。
2. 紧接着把 `01_THESIS_CONTEXT_MASTER_CN.md` 和 `02_THESIS_FACTS.json` 发过去。
3. 然后直接说你要写哪一章，例如“请先写第三章系统总体设计”。
4. 如果它写到实验部分开始出现虚构倾向，再补发 `03_THESIS_EVIDENCE_MAP_CN.md` 和 `06_MISSING_INFO_CHECKLIST_CN.md`，要求它严格区分“已确认”和“待补”。

## 7. 本次整理时没有做的事情

1. 没有修改任何现有源码、launch、config、`package.xml` 或 `CMakeLists.txt`。
2. 没有改动 `原视频.mp4` 和 `识别视频.mp4`。
3. 没有依赖当前机器的 `build/`、`devel/` 产物来得出论文结论。
4. 没有在当前机器上完成 Ubuntu 18.04 + ROS1 的实机复现；本次主要完成的是源码级、结构级、提交历史级核对。
