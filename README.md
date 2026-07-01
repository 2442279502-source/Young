# Smart Safety Demo — 智慧工地安全帽检测

基于 YOLOv8 的工地安全帽佩戴检测系统。支持视频文件、摄像头实时检测，输出标注视频和检测统计报告。

- 🟢 **绿色框 SAFE** — 已佩戴安全帽
- 🔴 **红色框 UNSAFE-HARDHAT** — 未佩戴安全帽

## 快速启动

```bash
cd smart_safety_demo

# 安装依赖（首次）
pip install -r requirements.txt

# 自动查找视频检测
python main.py

# 摄像头实时检测
python main.py --camera

# 指定视频 + 保存标注结果
python main.py 视频.mp4 -o result.mp4

# 调整检测灵敏度（默认 0.35）
python main.py 视频.mp4 --conf 0.5
```

Windows 用户也可以直接双击 `smart_safety_demo/run.bat`，或把视频拖到 bat 文件上。

## 检测原理

| 模式 | 模型 | 说明 |
|------|------|------|
| 专用模型 | `hardhat_model.pt` | 直接检测 helmet/head，精度高 |
| 回退模式 | `yolov8n.pt` + HSV | 检测 person 后对头部区域做安全帽颜色分析 |

## 项目结构

```
├── smart_safety_demo/
│   ├── main.py             # 主程序（检测、标注、统计报告）
│   ├── hardhat_model.pt    # 训练好的安全帽检测模型 (~24MB)
│   ├── yolov8n.pt          # YOLOv8n 回退模型 (~6MB)
│   ├── train_hardhat.py    # 模型训练脚本
│   ├── requirements.txt    # Python 依赖
│   ├── run.bat / run.sh    # 一键启动脚本
│   └── README.md
└── .gitignore
```

## 模型性能

基于 YOLOv8n，在 Kaggle Hard Hat Detection 数据集上微调 6 轮的结果：

| Epoch | mAP50 | 较上一轮 |
|-------|-------|----------|
| 1 | 0.793 | — |
| 2 | 0.795 | +0.2% |
| 3 | 0.844 | +4.9% |
| 4 | 0.832 | −1.2% |
| 5 | 0.861 | +2.9% |
| 6 | **0.874** | +1.3% |

mAP50 达到 **87.4%**，已具备工程落地精度。如需进一步提升，建议继续训练至 15–20 轮，预计可突破 0.90。

## 重新训练

```bash
cd smart_safety_demo
python train_hardhat.py
```

基于 Kaggle Hard Hat Detection 数据集微调 YOLOv8n，CPU 约 30–45 分钟。训练完成后自动生成 `hardhat_model.pt`。如需 GPU 训练，修改脚本中 `device="cuda"`。

## 技术栈

Python 3.9+ / OpenCV / Ultralytics YOLOv8 / NumPy

## 许可证

本项目基于 **MIT License** 开源，可自由用于商业和工程落地项目。详见 [LICENSE](LICENSE)。
