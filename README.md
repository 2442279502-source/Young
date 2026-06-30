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

## 训练自己的模型

```bash
cd smart_safety_demo
python train_hardhat.py
```

基于 Kaggle Hard Hat Detection 数据集微调 YOLOv8n，CPU 约 30-45 分钟，训练完自动生成 `hardhat_model.pt`。

## 技术栈

Python 3.9+ / OpenCV / Ultralytics YOLOv8 / NumPy

## 许可证

仅用于教育与演示目的。
