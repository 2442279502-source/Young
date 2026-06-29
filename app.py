"""
智能图片检测 Web 应用 — 后端服务
===============================
这个文件是整个项目的"大脑"，负责：
1. 启动一个网页服务（用 Flask）
2. 接收用户上传的图片
3. 用 YOLO 模型检测图片里有什么物体
4. 把标注好的图片返回给用户看
"""

import os
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_file
from ultralytics import YOLO
from PIL import Image
import io

# ============ 1. 初始化 Flask 应用 ============
# Flask 就是我们的"网页服务器"，它负责接收浏览器发来的请求
app = Flask(__name__)

# ============ 2. 设置文件路径 ============
# 获取当前文件所在目录的绝对路径
BASE_DIR = Path(__file__).resolve().parent
# 上传的图片存在 uploads 文件夹里
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# ============ 3. 加载 YOLO 模型 ============
# YOLOv8n 中的 "n" 代表 nano（纳米），是最轻量的版本
# 第一次运行时，它会自动从网上下载预训练好的模型
# 预训练模型 = 别人已经用大量图片训练好的"大脑"，拿来就能用
print("正在加载 YOLO 模型...")
model = YOLO("yolov8n.pt")  # .pt 是 PyTorch 模型文件的后缀
print("YOLO 模型加载完成！可以开始检测了。")

# ============ 4. 定义网页路由 ============

@app.route("/")
def index():
    """首页：显示上传图片的网页界面"""
    return render_template("index.html")


@app.route("/detect", methods=["POST"])
def detect():
    """
    检测接口：接收上传的图片 → YOLO检测 → 返回标注后的图片
    用户点击"上传检测"按钮时，浏览器就会请求这个接口
    """
    # 检查请求里有没有文件
    if "image" not in request.files:
        return jsonify({"error": "没有找到上传的图片"}), 400

    file = request.files["image"]

    # 检查文件名是否为空
    if file.filename == "":
        return jsonify({"error": "未选择文件"}), 400

    # 保存用户上传的原始图片
    original_path = UPLOAD_DIR / file.filename
    file.save(str(original_path))
    print(f"收到上传图片: {file.filename}")

    # ---------- 核心：用 YOLO 检测图片 ----------
    # model() 会返回一个结果列表，每张图片一个结果
    results = model(str(original_path))

    # 获取第一张（也是唯一一张）图片的检测结果
    result = results[0]

    # 把检测结果画在图片上（框出物体 + 标名称）
    # result.plot() 返回一张 numpy 数组格式的标注图片
    annotated_img = result.plot()

    # 把 numpy 数组转成 PIL Image 对象
    annotated_pil = Image.fromarray(annotated_img[..., ::-1])  # BGR → RGB 颜色转换

    # 把标注好的图片保存到内存中（不写磁盘，直接发给用户）
    img_io = io.BytesIO()
    annotated_pil.save(img_io, format="JPEG", quality=90)
    img_io.seek(0)  # 把"读指针"移到开头，准备发送

    # ---------- 提取检测信息 ----------
    # 把英文标签翻译成中文（YOLO 默认输出英文）
    label_map = {
        "person": "人", "bicycle": "自行车", "car": "汽车",
        "motorcycle": "摩托车", "airplane": "飞机", "bus": "公交车",
        "train": "火车", "truck": "卡车", "boat": "船",
        "dog": "狗", "cat": "猫", "bird": "鸟",
        "horse": "马", "sheep": "羊", "cow": "牛",
        "elephant": "大象", "bear": "熊", "zebra": "斑马",
        "giraffe": "长颈鹿", "backpack": "背包", "umbrella": "雨伞",
        "handbag": "手提包", "tie": "领带", "suitcase": "行李箱",
        "frisbee": "飞盘", "skis": "滑雪板", "snowboard": "滑雪板",
        "sports ball": "球", "kite": "风筝", "baseball bat": "棒球棒",
        "baseball glove": "棒球手套", "skateboard": "滑板", "surfboard": "冲浪板",
        "tennis racket": "网球拍", "bottle": "瓶子", "wine glass": "酒杯",
        "cup": "杯子", "fork": "叉子", "knife": "刀", "spoon": "勺子",
        "bowl": "碗", "banana": "香蕉", "apple": "苹果",
        "sandwich": "三明治", "orange": "橙子", "broccoli": "西兰花",
        "carrot": "胡萝卜", "hot dog": "热狗", "pizza": "披萨",
        "donut": "甜甜圈", "cake": "蛋糕", "chair": "椅子",
        "couch": "沙发", "potted plant": "盆栽", "bed": "床",
        "dining table": "餐桌", "toilet": "马桶", "tv": "电视",
        "laptop": "笔记本电脑", "mouse": "鼠标", "remote": "遥控器",
        "keyboard": "键盘", "cell phone": "手机", "microwave": "微波炉",
        "oven": "烤箱", "toaster": "烤面包机", "sink": "水槽",
        "refrigerator": "冰箱", "book": "书", "clock": "时钟",
        "vase": "花瓶", "scissors": "剪刀", "teddy bear": "泰迪熊",
        "hair drier": "吹风机", "toothbrush": "牙刷",
    }

    # 统计检测到的物体
    detected_objects = []
    if result.boxes is not None:
        for box in result.boxes:
            # 获取类别ID和置信度
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            english_name = model.names[class_id]
            chinese_name = label_map.get(english_name, english_name)
            detected_objects.append({
                "name": chinese_name,
                "name_en": english_name,
                "confidence": round(confidence * 100, 1)  # 转为百分比
            })

    # 返回标注图片 + 检测信息
    return send_file(
        img_io,
        mimetype="image/jpeg",
        as_attachment=False,
    )


@app.route("/detect/info", methods=["POST"])
def detect_info():
    """
    检测信息接口：只返回检测到的物体列表（JSON格式），不返回图片
    这样前端可以先显示"检测到了什么"
    """
    if "image" not in request.files:
        return jsonify({"error": "没有找到上传的图片"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "未选择文件"}), 400

    # 保存图片
    original_path = UPLOAD_DIR / file.filename
    file.save(str(original_path))

    # YOLO 检测
    results = model(str(original_path))
    result = results[0]

    # 统计检测结果
    label_map = {
        "person": "人", "bicycle": "自行车", "car": "汽车",
        "motorcycle": "摩托车", "airplane": "飞机", "bus": "公交车",
        "train": "火车", "truck": "卡车", "boat": "船",
        "dog": "狗", "cat": "猫", "bird": "鸟",
        "horse": "马", "sheep": "羊", "cow": "牛",
        "elephant": "大象", "bear": "熊", "zebra": "斑马",
        "giraffe": "长颈鹿", "backpack": "背包", "umbrella": "雨伞",
        "handbag": "手提包", "tie": "领带", "suitcase": "行李箱",
        "frisbee": "飞盘", "skis": "滑雪板", "snowboard": "滑雪板",
        "sports ball": "球", "kite": "风筝", "baseball bat": "棒球棒",
        "baseball glove": "棒球手套", "skateboard": "滑板", "surfboard": "冲浪板",
        "tennis racket": "网球拍", "bottle": "瓶子", "wine glass": "酒杯",
        "cup": "杯子", "fork": "叉子", "knife": "刀", "spoon": "勺子",
        "bowl": "碗", "banana": "香蕉", "apple": "苹果",
        "sandwich": "三明治", "orange": "橙子", "broccoli": "西兰花",
        "carrot": "胡萝卜", "hot dog": "热狗", "pizza": "披萨",
        "donut": "甜甜圈", "cake": "蛋糕", "chair": "椅子",
        "couch": "沙发", "potted plant": "盆栽", "bed": "床",
        "dining table": "餐桌", "toilet": "马桶", "tv": "电视",
        "laptop": "笔记本电脑", "mouse": "鼠标", "remote": "遥控器",
        "keyboard": "键盘", "cell phone": "手机", "microwave": "微波炉",
        "oven": "烤箱", "toaster": "烤面包机", "sink": "水槽",
        "refrigerator": "冰箱", "book": "书", "clock": "时钟",
        "vase": "花瓶", "scissors": "剪刀", "teddy bear": "泰迪熊",
        "hair drier": "吹风机", "toothbrush": "牙刷",
    }

    detected_objects = []
    if result.boxes is not None:
        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            english_name = model.names[class_id]
            chinese_name = label_map.get(english_name, english_name)
            detected_objects.append({
                "name": chinese_name,
                "name_en": english_name,
                "confidence": round(confidence * 100, 1)
            })

    return jsonify({
        "filename": file.filename,
        "count": len(detected_objects),
        "objects": detected_objects
    })


# ============ 5. 启动应用 ============
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  智能图片检测应用已启动！")
    print("  请打开浏览器访问: http://127.0.0.1:5000")
    print("=" * 50 + "\n")
    # debug=True 表示开发模式：代码改了会自动重启，出错会显示详细信息
    app.run(debug=True, host="127.0.0.1", port=5000)
