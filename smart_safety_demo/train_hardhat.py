"""
训练 YOLOv8n 安全帽检测模型（快速版）
使用数据子集 + 小尺寸图片，CPU 约 30-45 分钟
"""
import os
import sys
import random
import shutil
from pathlib import Path
from ultralytics import YOLO

# ============================================================
# 配置
# ============================================================
DATASET_DIR = os.path.expanduser(
    r"~\.cache\kagglehub\datasets\andrewmvd\hard-hat-detection\versions\1"
)
IMAGES_DIR = os.path.join(DATASET_DIR, "images")
ANNOTATIONS_DIR = os.path.join(DATASET_DIR, "annotations")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = os.path.join(SCRIPT_DIR, "hardhat_dataset")
MODEL_OUT = os.path.join(SCRIPT_DIR, "hardhat_model.pt")

# 快速训练参数
TRAIN_SAMPLES = 1000   # 训练集图片数
VAL_SAMPLES = 200       # 验证集图片数
EPOCHS = 15             # 训练轮数
IMG_SIZE = 416          # 图片尺寸
BATCH_SIZE = 16         # 批次大小

CLASSES = ["helmet", "head"]


def create_fast_dataset():
    """创建快速训练用的数据子集"""
    import xml.etree.ElementTree as ET

    # 随机选图
    all_images = sorted([
        f for f in os.listdir(IMAGES_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))
    ])
    random.seed(42)
    random.shuffle(all_images)

    total_needed = TRAIN_SAMPLES + VAL_SAMPLES
    selected = all_images[:total_needed]
    train_files = selected[:TRAIN_SAMPLES]
    val_files = selected[TRAIN_SAMPLES:]

    print(f"[信息] 训练集: {len(train_files)} 张, 验证集: {len(val_files)} 张")

    # 清空并重建输出目录
    for subset in ["train", "val"]:
        for sub in ["images", "labels"]:
            d = os.path.join(WORK_DIR, sub, subset)
            os.makedirs(d, exist_ok=True)

    # 复制图片并转换标注
    for subset_name, file_list in [("train", train_files), ("val", val_files)]:
        img_dst_dir = os.path.join(WORK_DIR, "images", subset_name)
        lbl_dst_dir = os.path.join(WORK_DIR, "labels", subset_name)
        converted = 0

        for fname in file_list:
            img_src = os.path.join(IMAGES_DIR, fname)
            xml_name = os.path.splitext(fname)[0] + ".xml"
            xml_src = os.path.join(ANNOTATIONS_DIR, xml_name)

            if not os.path.exists(xml_src):
                continue

            # 解析 XML
            tree = ET.parse(xml_src)
            root = tree.getroot()
            size = root.find("size")
            img_w = int(size.find("width").text) if size is not None else 416
            img_h = int(size.find("height").text) if size is not None else 416

            yolo_lines = []
            for obj in root.findall("object"):
                cls_name = obj.find("name").text
                if cls_name not in CLASSES:
                    continue
                cls_id = CLASSES.index(cls_name)
                bb = obj.find("bndbox")
                xmin = float(bb.find("xmin").text)
                ymin = float(bb.find("ymin").text)
                xmax = float(bb.find("xmax").text)
                ymax = float(bb.find("ymax").text)

                cx = ((xmin + xmax) / 2) / img_w
                cy = ((ymin + ymax) / 2) / img_h
                bw = (xmax - xmin) / img_w
                bh = (ymax - ymin) / img_h

                cx = max(0, min(1, cx))
                cy = max(0, min(1, cy))
                bw = max(0, min(1, bw))
                bh = max(0, min(1, bh))

                if bw > 0.002 and bh > 0.002:
                    yolo_lines.append(f"{cls_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")

            shutil.copy2(img_src, os.path.join(img_dst_dir, fname))
            with open(os.path.join(lbl_dst_dir, os.path.splitext(fname)[0] + ".txt"),
                      "w", encoding="utf-8") as f:
                f.write("\n".join(yolo_lines))
                if yolo_lines:
                    f.write("\n")
            converted += 1

        print(f"[信息] {subset_name}: 转换 {converted} 张")

    # 写 data.yaml
    yaml_path = os.path.join(WORK_DIR, "data.yaml")
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(f"""# 安全帽检测数据集 (快速版)
path: {WORK_DIR.replace(chr(92), '/')}
train: images/train
val: images/val
nc: 2
names: ['helmet', 'head']
""")
    return yaml_path


def main():
    print("=" * 60)
    print("  YOLOv8n 安全帽检测 - 快速训练")
    print(f"  训练 {TRAIN_SAMPLES} 张 + 验证 {VAL_SAMPLES} 张")
    print(f"  图片 {IMG_SIZE}px, 批次 {BATCH_SIZE}, {EPOCHS} 轮")
    print("=" * 60)
    print()

    # 准备数据集
    print("[1/2] 准备数据集...")
    yaml_path = create_fast_dataset()

    # 训练
    print("\n[2/2] 开始训练 (CPU, 预计 30-45 分钟)...")
    model = YOLO("yolov8n.pt")

    model.train(
        data=yaml_path,
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH_SIZE,
        project=os.path.join(WORK_DIR, "runs"),
        name="train",
        exist_ok=True,
        device="cpu",
        workers=2,
        patience=5,            # 5轮不提升则早停
        save=True,
        pretrained=True,
        verbose=True,
        # 轻量数据增强
        hsv_h=0.01,
        hsv_s=0.3,
        hsv_v=0.15,
        degrees=3.0,
        translate=0.1,
        scale=0.2,
        fliplr=0.5,
        mosaic=0.3,
    )

    # 复制最佳模型
    best = os.path.join(WORK_DIR, "runs", "train", "weights", "best.pt")
    if os.path.exists(best):
        shutil.copy2(best, MODEL_OUT)
        print(f"\n模型已保存: {MODEL_OUT}")
        print("运行: python main.py <视频文件>")
    else:
        print("\n[错误] 训练未生成模型文件")


if __name__ == "__main__":
    main()
