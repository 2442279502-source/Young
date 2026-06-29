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
    """钢筋估重（kg）"""
    return concrete_volume * ratio * STEEL_DENSITY


def calc_rebar_area(width, height, ratio=REBAR_RATIO):
    """钢筋截面积（mm²）"""
    return width * height * ratio * 1_000_000


def calc_formwork(length, width, height):
    """模板面积（底面 + 四侧）"""
    bottom = length * width
    sides  = 2 * (length * height) + 2 * (width * height)
    return bottom + sides


def calc_costs(concrete, rebar, formwork,
               concrete_price=None, rebar_price=None, formwork_price=None):
    """计算费用。单价不填则不计算。返回 {concrete_cost, rebar_cost, formwork_cost, total_cost}"""
    costs = {}
    if concrete_price is not None:
        costs["concrete_cost"] = round(concrete * concrete_price, 2)
    if rebar_price is not None:
        costs["rebar_cost"] = round(rebar * rebar_price, 2)
    if formwork_price is not None:
        costs["formwork_cost"] = round(formwork * formwork_price, 2)
    if costs:
        costs["total_cost"] = round(sum(costs.values()), 2)
    return costs


def save_excel(records, filename=None):
    """
    把计算结果存为 Excel 文件

    参数:
        records: 所有构件的计算记录列表
        filename: 文件名（不传则自动生成日期名）

    自动识别 quick 和 precise 两种模式记录。
    precise 模式会额外生成「钢筋明细」Sheet。
    """
    if filename is None:
        filename = f"算量报表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = "工程算量汇总"

    has_costs = any("total_cost" in r for r in records)
    has_precise = any(r.get("mode") == "precise" for r in records)

    # ---- Sheet 1: 汇总表 ----
    headers = ["序号", "模式", "类型", "构件名称",
               "混凝土(m3)", "钢筋面积(mm²)", "钢筋(kg)", "模板(m2)", "含钢量(kg/m³)"]
    if has_costs:
        headers += ["混凝土费用(元)", "钢筋费用(元)", "模板费用(元)", "合计费用(元)"]
    ws.append(headers)

    for i, r in enumerate(records, 1):
        if r.get("mode") == "precise":
            type_label = {'slab': '板', 'beam': '梁', 'column': '柱'}.get(r.get('type'), '?')
            row = [i, "精确", type_label, r["name"],
                   round(r["concrete"], 3),
                   round(r.get("rebar_area", 0), 0),
                   round(r["rebar"], 1),
                   round(r["formwork"], 2),
                   round(r.get("rebar_per_m3", 0), 1)]
        else:
            row = [i, "快速", "", r["name"],
                   round(r["concrete"], 3),
                   round(r.get("rebar_area", 0), 0),
                   round(r["rebar"], 1),
                   round(r["formwork"], 2), ""]

        if has_costs:
            row += [r.get("concrete_cost", ""),
                    r.get("rebar_cost", ""),
                    r.get("formwork_cost", ""),
                    r.get("total_cost", "")]
        ws.append(row)

    # 汇总行
    name_idx = headers.index("构件名称")  # position of name column
    total_concrete   = round(sum(r["concrete"] for r in records), 3)
    total_rebar_area = round(sum(r.get("rebar_area", 0) for r in records), 0)
    total_rebar      = round(sum(r["rebar"] for r in records), 1)
    total_formwork   = round(sum(r["formwork"] for r in records), 2)
    summary = [""] * len(headers)
    summary[0] = ""
    summary[name_idx] = "合计"
    summary[name_idx + 1] = total_concrete
    summary[name_idx + 2] = total_rebar_area
    summary[name_idx + 3] = total_rebar
    summary[name_idx + 4] = total_formwork
    if has_costs:
        summary[name_idx + 5] = ""  # rebar_per_m3
        summary[name_idx + 6] = round(sum(r.get("concrete_cost", 0) for r in records), 2)
        summary[name_idx + 7] = round(sum(r.get("rebar_cost", 0) for r in records), 2)
        summary[name_idx + 8] = round(sum(r.get("formwork_cost", 0) for r in records), 2)
        summary[name_idx + 9] = round(sum(r.get("total_cost", 0) for r in records), 2)
    ws.append(summary)

    # ---- Sheet 2: 钢筋明细（仅精确模式） ----
    if has_precise:
        ws2 = wb.create_sheet("钢筋明细")
        ws2.append(["构件名称", "钢筋位置", "直径(mm)", "间距(mm)",
                    "根数", "每根长度(mm)", "每米重(kg/m)", "总重(kg)", "截面积(mm²)"])

        for r in records:
            if r.get("mode") != "precise" or "detail" not in r:
                continue
            for key, d in r["detail"].items():
                ws2.append([
                    r["name"],
                    d.get("label", key),
                    d.get("diameter", ""),
                    d.get("spacing", ""),
                    d["count"],
                    d["len_mm"],
                    d["unit_w"],
                    d["total_kg"],
                    d["area_mm2"],
                ])

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
