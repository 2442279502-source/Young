# Smart Safety Demo — 智慧工地安全帽检测

基于 YOLOv8 的工地安全帽佩戴检测系统，支持视频文件、摄像头实时检测，输出标注视频和检测统计报告。

- 🟢 **绿色框 SAFE** — 已佩戴安全帽
- 🔴 **红色框 UNSAFE-HARDHAT** — 未佩戴安全帽

## 功能特性

| 功能 | 说明 |
|------|------|
| 视频检测 | 支持 mp4/avi/mov/mkv 等常见格式 |
| 摄像头实时检测 | `--camera` 一键切换 |
| 输出标注视频 | `-o result.mp4` 保存检测结果 |
| 双模型策略 | 专用安全帽模型 + YOLO通用模型+HVS颜色回退 |
| 检测统计报告 | 处理完毕后输出安全/不安全人数及占比 |
| 拖拽启动 | 把视频拖到 `run.bat` 上即可检测 |

## 快速启动

### 方式一：双击运行（推荐）

直接在文件夹里双击 **`run.bat`**，首次运行会自动配置环境。

也可以把视频文件**拖到 `run.bat` 上**来检测指定视频。

### 方式二：命令行运行

```bash
# 自动查找当前目录的视频
python main.py

# 指定视频文件
python main.py 工地视频.mp4

# 使用摄像头实时检测
python main.py --camera

# 指定视频 + 输出标注后的视频
python main.py 视频.mp4 -o result.mp4

# 调整检测灵敏度（默认 0.35，越大越严格）
python main.py 视频.mp4 --conf 0.5
```

### 首次使用需要安装依赖

```bash
pip install -r requirements.txt
```

## 检测原理

### 模式一：专用安全帽模型（`hardhat_model.pt`）
直接检测 `helmet`（已佩戴安全帽）和 `head`（未佩戴安全帽头部）两类目标，精度更高。

### 模式二：YOLO + HSV 颜色回退（`yolov8n.pt`）
用通用 YOLO 检测 `person`，再对人头部区域做 HSV 颜色分析：识别黄/白/蓝/红安全帽颜色，同时检测肤色占比辅助判断。当专用模型不可用时自动启用。

## 操作

| 按键 | 功能 |
|------|------|
| `q` | 退出程序 |

## 训练自己的模型

如果需要重新训练或微调模型：

```bash
python train_hardhat.py
```

脚本会自动从 Kaggle Hard Hat Detection 数据集下载并训练。CPU 约 30-45 分钟，建议有 GPU 的环境更快（修改 `device="cuda"`）。
训练完成后生成 `hardhat_model.pt`，自动覆盖旧模型。

## 技术栈

- **Python 3.9+** / **OpenCV** / **Ultralytics YOLOv8** / **NumPy**
- YOLOv8n 预训练模型 + Kaggle Hard Hat Detection 数据集微调
- HSV 颜色空间安全帽颜色匹配（黄/白/蓝/红）
- 肤色占比辅助判断（回退模式）

## 项目结构

```
smart_safety_demo/
├── main.py             # 主程序（检测、标注、统计）
├── hardhat_model.pt    # 训练好的安全帽检测模型 (~24MB)
├── yolov8n.pt          # YOLOv8n 基础模型（回退方案，~6MB）
├── train_hardhat.py    # 模型训练脚本
├── requirements.txt    # Python 依赖
├── run.bat / run.sh    # 一键启动脚本（Windows / Linux / macOS）
└── README.md
```

## 许可证

本项目仅用于教育与演示目的。
