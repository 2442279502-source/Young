# -*- coding: utf-8 -*-
"""
工程算量小助手 — Day 4（Web 版）
==============================
浏览器里输入构件尺寸 → 自动算量 → 导出 Excel

技术栈: Flask + openpyxl
怎么运行:
    python app.py
    浏览器打开 http://127.0.0.1:5000
"""

from datetime import datetime
from flask import Flask, render_template, request, session, send_file
from openpyxl import Workbook
import os

# 导入我们自己写的计算函数
from calc import calc_concrete, calc_rebar, calc_formwork

app = Flask(__name__)
app.secret_key = "quantity-calc-secret-2026"  # session 加密用


@app.route("/")
def index():
    """首页 — 显示表单 + 已添加的构件列表"""
    records = session.get("records", [])
    return render_template("index.html", records=records)


@app.route("/add", methods=["POST"])
def add():
    """添加一个构件"""
    name   = request.form.get("name", "")
    length = float(request.form.get("length", 0))
    width  = float(request.form.get("width", 0))
    height = float(request.form.get("height", 0))

    # 计算
    concrete = calc_concrete(length, width, height)
    rebar    = calc_rebar(concrete)
    formwork = calc_formwork(length, width, height)

    # 存入 session
    records = session.get("records", [])
    records.append({
        "name": name,
        "length": length,
        "width": width,
        "height": height,
        "concrete": round(concrete, 2),
        "rebar": round(rebar, 1),
        "formwork": round(formwork, 2)
    })
    session["records"] = records

    return render_template("index.html", records=records)


@app.route("/export")
def export():
    """导出 Excel 并下载"""
    records = session.get("records", [])
    if not records:
        return "没有数据可导出", 400

    filename = f"算量报表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join("static", filename)

    wb = Workbook()
    ws = wb.active
    ws.title = "工程算量"

    headers = ["序号", "构件名称", "长(m)", "宽(m)", "高(m)",
               "混凝土(m3)", "钢筋(kg)", "模板(m2)"]
    ws.append(headers)

    for i, r in enumerate(records, 1):
        ws.append([i, r["name"], r["length"], r["width"], r["height"],
                   r["concrete"], r["rebar"], r["formwork"]])

    # 汇总行
    ws.append(["", "合计", "", "", "",
               round(sum(r["concrete"] for r in records), 2),
               round(sum(r["rebar"] for r in records), 1),
               round(sum(r["formwork"] for r in records), 2)])

    wb.save(filepath)
    return send_file(filepath, as_attachment=True, download_name=filename)


@app.route("/clear")
def clear():
    """清空构件列表"""
    session["records"] = []
    return render_template("index.html", records=[])


if __name__ == "__main__":
    print("=" * 45)
    print("  工程算量小助手（Web 版）")
    print("  浏览器打开: http://127.0.0.1:5001")
    print("=" * 45)
    app.run(debug=True, port=5001)
