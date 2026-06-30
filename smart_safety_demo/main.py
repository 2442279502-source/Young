"""
Smart Safety Demo — 智慧工地安全帽检测
========================================
使用 YOLOv8 专用模型检测工地人员是否佩戴安全帽。
  🟢 绿色 = SAFE（已佩戴安全帽）
  🔴 红色 = UNSAFE-HARDHAT（未佩戴安全帽）

用法:
  python main.py                         # 自动查找当前目录下的视频文件
  python main.py <视频路径>                # 指定视频文件
  python main.py --camera                 # 使用摄像头实时检测
  python main.py <视频路径> -o result.mp4  # 输出标注后的视频
  python main.py <视频路径> --conf 0.5     # 调整检测置信度阈值 (默认 0.35)

技术栈: Python 3.9+ / OpenCV / Ultralytics YOLOv8 / NumPy
"""
import os
import sys
import time
import cv2
import numpy as np
from ultralytics import YOLO

# ============================================================
# 配置
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HARDHAT_MODEL = os.path.join(SCRIPT_DIR, "hardhat_model.pt")   # 专用安全帽模型
FALLBACK_MODEL = os.path.join(SCRIPT_DIR, "yolov8n.pt")        # 通用 YOLO 回退模型
DEFAULT_CONF = 0.35                                             # 默认置信度阈值

# HSV 安全帽颜色范围（回退方案用）
HELMET_COLOR_RANGES = [
    {"low": np.array([15, 50, 100]), "high": np.array([35, 255, 255])},   # 黄色
    {"low": np.array([0, 0, 180]),   "high": np.array([180, 30, 255])},   # 白色
    {"low": np.array([90, 50, 50]),  "high": np.array([130, 255, 255])},  # 蓝色
    {"low": np.array([0, 50, 50]),   "high": np.array([10, 255, 255])},   # 红色1
    {"low": np.array([160, 50, 50]), "high": np.array([180, 255, 255])},  # 红色2
]
SKIN_LOW = np.array([0, 20, 50])
SKIN_HIGH = np.array([25, 150, 255])
HEAD_RATIO = 0.40


# ============================================================
# 模型加载
# ============================================================

def load_model(conf_threshold: float):
    """
    加载检测模型。优先使用专用安全帽模型，不存在则回退到通用 YOLO。

    返回: (model, model_type)
      model_type: "hardhat" (直接检测 helmet/head) 或 "yolo" (检测 person + HSV 分析)
    """
    if os.path.exists(HARDHAT_MODEL):
        print(f"[模型] 加载安全帽专用模型: {HARDHAT_MODEL}")
        model = YOLO(HARDHAT_MODEL)
        # 验证模型类别
        names = getattr(model, 'names', {})
        if len(names) == 2 and 'helmet' in names.values():
            print("[模型] 检测模式: helmet/head 二分类")
            return model, "hardhat"
        # 类别不对，当通用模型用
        return model, "yolo"

    if os.path.exists(FALLBACK_MODEL):
        print("[模型] 安全帽模型未找到，使用通用 YOLO + HSV 颜色分析")
        print("[提示] 如需更高精度，请运行: python train_hardhat.py")
        return YOLO(FALLBACK_MODEL), "yolo"

    print("[错误] 未找到任何模型文件 (hardhat_model.pt / yolov8n.pt)")
    print("[提示] 请先下载 yolov8n.pt 或训练安全帽模型")
    sys.exit(1)


# ============================================================
# 视频输入
# ============================================================

def find_video():
    """在脚本目录和当前工作目录自动查找视频文件。"""
    exts = (".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm", ".ts")
    searched = set()
    for search_dir in (SCRIPT_DIR, os.getcwd()):
        if search_dir in searched:
            continue
        searched.add(search_dir)
        try:
            for fname in os.listdir(search_dir):
                if fname.lower().endswith(exts):
                    return os.path.join(search_dir, fname)
        except (OSError, PermissionError):
            pass
    return None


def open_video(source):
    """打开视频文件，返回 (VideoCapture, fps)。"""
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[错误] 无法打开视频: {source}")
        sys.exit(1)

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    name = source if isinstance(source, str) else f"摄像头 {source}"
    print(f"[视频] {name}")
    print(f"[视频] {w}x{h}  {fps:.1f}fps  {total}帧")
    return cap, fps


# ============================================================
# 检测处理：专用模型模式
# ============================================================

def process_hardhat(results, conf_threshold):
    """使用专用安全帽模型解析结果。返回检测列表。"""
    detections = []
    boxes_data = results[0].boxes
    if boxes_data is None:
        return detections

    for box in boxes_data:
        cls_id = int(box.cls[0])
        cls_name = results[0].names[cls_id]
        conf = float(box.conf[0])
        if conf < conf_threshold:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        detections.append({
            "bbox": (x1, y1, x2, y2),
            "confidence": conf,
            "has_helmet": (cls_name == "helmet"),
        })
    return detections


# ============================================================
# 检测处理：通用 YOLO + HSV 回退模式
# ============================================================

def is_wearing_helmet(person_crop: np.ndarray) -> bool:
    """HSV 颜色分析：判断人员头部区域是否包含安全帽颜色。"""
    if person_crop is None or person_crop.size == 0:
        return False
    h, w = person_crop.shape[:2]
    head_h = int(h * HEAD_RATIO)
    head_roi = person_crop[0:head_h, :]
    if head_roi.size == 0:
        return False

    hsv = cv2.cvtColor(head_roi, cv2.COLOR_BGR2HSV)
    total = hsv.shape[0] * hsv.shape[1]

    # 统计安全帽颜色像素
    helmet_px = 0
    for cr in HELMET_COLOR_RANGES:
        helmet_px += cv2.countNonZero(cv2.inRange(hsv, cr["low"], cr["high"]))

    # 肤色占比过高 → 大概率没戴帽子
    skin_px = cv2.countNonZero(cv2.inRange(hsv, SKIN_LOW, SKIN_HIGH))
    if skin_px / total > 0.6:
        return False

    return helmet_px / total >= 0.12


def process_yolo_fallback(model, results, frame, conf_threshold):
    """通用 YOLO 检测 person + 对每人做 HSV 安全帽分析。"""
    detections = []
    boxes_data = results[0].boxes
    if boxes_data is None:
        return detections

    for box in boxes_data:
        cls_id = int(box.cls[0])
        if model.names[cls_id] != "person":
            continue
        conf = float(box.conf[0])
        if conf < conf_threshold:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        person_crop = frame[y1:y2, x1:x2]
        detections.append({
            "bbox": (x1, y1, x2, y2),
            "confidence": conf,
            "has_helmet": is_wearing_helmet(person_crop),
        })
    return detections


# ============================================================
# 叠加绘制
# ============================================================

def draw_detections(frame, detections):
    """在帧上绘制所有检测框和标签。"""
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        has_helmet = det["has_helmet"]
        conf = det["confidence"]

        if has_helmet:
            color = (0, 255, 0)
            label = f"SAFE {conf:.2f}"
        else:
            color = (0, 0, 255)
            label = f"UNSAFE-HARDHAT {conf:.2f}"

        # 边框
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        # 标签背景
        (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        cv2.rectangle(frame, (x1, y1 - lh - 6), (x1 + lw, y1), color, -1)
        # 标签文字
        cv2.putText(frame, label, (x1, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)


def draw_status(frame, detections, fps, model_type):
    """绘制状态栏信息。"""
    mode_text = "Model: Hardhat (helmet/head)" if model_type == "hardhat" else "Model: YOLO + HSV"
    cv2.putText(frame, mode_text, (10, 24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 48),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

    safe = sum(1 for d in detections if d["has_helmet"])
    unsafe = len(detections) - safe
    cv2.putText(frame, f"Safe: {safe}", (10, 72),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
    if unsafe > 0:
        cv2.putText(frame, f"Unsafe: {unsafe}", (10, 96),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)


# ============================================================
# 主循环
# ============================================================

def main():
    # ---- 解析参数 ----
    args = sys.argv[1:]
    i = 0
    video_source = None
    conf_threshold = DEFAULT_CONF
    use_camera = False
    output_path = None
    while i < len(args):
        if args[i] in ("--conf", "-c") and i + 1 < len(args):
            try:
                conf_threshold = float(args[i + 1])
                i += 2
            except ValueError:
                print(f"[警告] 无效置信度值: {args[i + 1]}，使用默认值")
                i += 2
        elif args[i] in ("--camera", "--cam"):
            use_camera = True
            i += 1
        elif args[i] in ("--output", "-o") and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        elif args[i].startswith("--"):
            i += 1  # 跳过未知 flag
        else:
            video_source = args[i]
            i += 1

    # ---- 确定视频源 ----
    if use_camera:
        video_source = 0  # 默认摄像头
        print("[信息] 使用摄像头实时检测")
    elif video_source is None:
        video_source = find_video()
        if video_source:
            print(f"[信息] 自动检测到视频: {os.path.basename(video_source)}")
        else:
            print("[错误] 未找到视频文件。")
            print("  将视频放到当前目录，或指定路径: python main.py <视频路径>")
            print("  或使用摄像头: python main.py --camera")
            sys.exit(1)

    # ---- 加载模型 ----
    model, model_type = load_model(conf_threshold)

    # ---- 打开视频 ----
    cap, video_fps = open_video(video_source)

    print(f"[参数] 置信度阈值: {conf_threshold}")

    # ---- 输出视频 ----
    video_writer = None
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        video_writer = cv2.VideoWriter(output_path, fourcc, video_fps,
                                       (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                                        int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))
        if not video_writer.isOpened():
            print(f"[错误] 无法创建输出视频: {output_path}")
            video_writer = None
        else:
            print(f"[输出] 标注视频将保存至: {output_path}")
    print("[运行] 按 'q' 键退出\n")

    # ---- 逐帧处理 ----
    frame_count = 0
    fps_timer = time.time()
    display_fps = video_fps
    stats = {"total_detections": 0, "safe_frames": 0, "unsafe_frames": 0, "frames_with_people": 0}

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            # ---- 推理 ----
            results = model(frame, verbose=False)

            # ---- 解析 ----
            if model_type == "hardhat":
                detections = process_hardhat(results, conf_threshold)
            else:
                detections = process_yolo_fallback(model, results, frame, conf_threshold)

            # ---- 统计 ----
            if detections:
                stats["total_detections"] += len(detections)
                stats["frames_with_people"] += 1
                safe = sum(1 for d in detections if d["has_helmet"])
                if len(detections) > safe:
                    stats["unsafe_frames"] += 1
                else:
                    stats["safe_frames"] += 1

            # ---- 绘制 ----
            draw_detections(frame, detections)
            draw_status(frame, detections, display_fps, model_type)

            # 顶部标题
            h, w = frame.shape[:2]
            cv2.putText(frame, "Smart Safety Demo — Hardhat Detection",
                        (w // 2 - 200, 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

            # ---- 输出 ----
            if video_writer:
                video_writer.write(frame)

            # ---- 显示 ----
            cv2.imshow("Smart Safety Demo - Hardhat Detection", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

            # 每秒更新一次实时 FPS
            if frame_count % 30 == 0:
                now = time.time()
                elapsed = now - fps_timer
                if elapsed > 0:
                    display_fps = 30 / elapsed
                fps_timer = now

    except KeyboardInterrupt:
        print("\n[信息] 用户中断")
    except Exception as e:
        print(f"[错误] {e}")
        import traceback
        traceback.print_exc()
    finally:
        cap.release()
        if video_writer:
            video_writer.release()
        cv2.destroyAllWindows()

        # ---- 检测统计报告 ----
        print()
        print("=" * 56)
        print("  检测统计报告")
        print("=" * 56)
        print(f"  处理帧数:        {frame_count}")
        print(f"  检测到人的帧数:  {stats['frames_with_people']}")
        if stats["frames_with_people"] > 0:
            total_people = stats["total_detections"]
            pct_safe = stats["safe_frames"] / stats["frames_with_people"] * 100
            print(f"  安全佩戴帧:      {stats['safe_frames']}  ({pct_safe:.1f}%)")
            print(f"  未佩戴安全帽帧:  {stats['unsafe_frames']}")
            print(f"  累计检出人数:    {total_people}")
        if output_path and video_writer:
            print(f"  输出视频:        {output_path}")
        print("=" * 56)
        print("[信息] 程序结束")


if __name__ == "__main__":
    print("=" * 56)
    print("  智慧工地安全方案演示 — Smart Safety Demo")
    print("=" * 56)
    print()
    main()
