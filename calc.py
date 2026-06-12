# -*- coding: utf-8 -*-
"""
工程算量小助手 — Day 3
=====================
功能：
  1. 混凝土方量计算
  2. 钢筋估重
  3. 模板面积
  4. 导出 Excel 报表

怎么运行：
    python calc.py
"""

from datetime import datetime
from openpyxl import Workbook

# 常量
STEEL_DENSITY = 7850        # 钢筋密度 kg/m3
REBAR_RATIO   = 0.01        # 配筋率 1%


def calc_concrete(length, width, height):
    """混凝土方量"""
    return length * width * height


def calc_rebar(concrete_volume, ratio=REBAR_RATIO):
    """钢筋估重"""
    return concrete_volume * ratio * STEEL_DENSITY


def calc_formwork(length, width, height):
    """模板面积（底面 + 四侧）"""
    bottom = length * width
    sides  = 2 * (length * height) + 2 * (width * height)
    return bottom + sides


def save_excel(records, filename=None):
    """
    把计算结果存为 Excel 文件

    参数:
        records: 所有构件的计算记录列表
        filename: 文件名（不传则自动生成日期名）
    """
    if filename is None:
        filename = f"算量报表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = "工程算量"

    # 表头
    headers = ["序号", "构件名称", "长(m)", "宽(m)", "高(m)",
               "混凝土(m3)", "钢筋(kg)", "模板(m2)"]
    ws.append(headers)

    # 数据行
    for i, r in enumerate(records, 1):
        ws.append([i, r["name"],
                   r["length"], r["width"], r["height"],
                   round(r["concrete"], 2),
                   round(r["rebar"], 1),
                   round(r["formwork"], 2)])

    # 汇总行
    total_concrete = sum(r["concrete"] for r in records)
    total_rebar    = sum(r["rebar"] for r in records)
    total_formwork = sum(r["formwork"] for r in records)
    ws.append(["", "合计", "", "", "",
               round(total_concrete, 2),
               round(total_rebar, 1),
               round(total_formwork, 2)])

    wb.save(filename)
    return filename


def main():
    print("=" * 45)
    print("  工程算量小助手")
    print("  输入构件 → 计算 → 导出 Excel")
    print("=" * 45)

    records = []

    while True:
        print("\n--- 新建构件 ---")
        name   = input("构件名称（如 KL1、B1、Z1，输入 q 结束）：")
        if name.lower() == "q":
            break

        length = float(input("长度（米）："))
        width  = float(input("宽度（米）："))
        height = float(input("高度（米）："))

        concrete = calc_concrete(length, width, height)
        rebar    = calc_rebar(concrete)
        formwork = calc_formwork(length, width, height)

        records.append({
            "name": name,
            "length": length,
            "width": width,
            "height": height,
            "concrete": concrete,
            "rebar": rebar,
            "formwork": formwork
        })

        print(f"  → 混凝土 {concrete:.2f} m3 | 钢筋 {rebar:.1f} kg | 模板 {formwork:.2f} m2")

    if not records:
        print("没有输入任何构件，退出。")
        return

    # 导出 Excel
    filename = save_excel(records)
    print("\n" + "=" * 45)
    print(f"  报表已保存：{filename}")
    print(f"  共 {len(records)} 个构件")
    print(f"  混凝土合计：{sum(r['concrete'] for r in records):.2f} m3")
    print(f"  钢筋合计：  {sum(r['rebar'] for r in records):.1f} kg")
    print(f"  模板合计：  {sum(r['formwork'] for r in records):.2f} m2")
    print("=" * 45)


if __name__ == "__main__":
    main()
