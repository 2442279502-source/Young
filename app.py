# -*- coding: utf-8 -*-
"""
工程算量小助手 v2.0（Web 版）
=============================
支持模式：
  - 快速估算：体积×配筋率×密度 → 大概钢筋量
  - 精确配筋：按直径+间距精确算每根钢筋（板/梁/柱）

怎么运行:
    python app.py
    浏览器打开 http://127.0.0.1:5001
"""

from datetime import datetime
from flask import Flask, render_template, request, session, send_file, redirect, url_for
import os

from calc import calc_concrete, calc_rebar, calc_rebar_area, calc_formwork, calc_costs, save_excel
from calc_pro import calc_slab, calc_beam, calc_column
from gb_standards import cover_min, COMMON_DIAMETERS

app = Flask(__name__)
app.secret_key = "quantity-calc-pro-2026"


# ============================================================
# 辅助函数
# ============================================================

def _safe_float(val, default=None):
    """安全转 float，空值返回 default"""
    if val is None:
        return default
    s = str(val).strip()
    return float(s) if s else default


def _apply_prices(calcs, prices):
    """给所有没费用的记录补算费用"""
    if not prices:
        return
    cp, rp, fp = prices["concrete_price"], prices["rebar_price"], prices["formwork_price"]
    for r in calcs:
        if "total_cost" not in r:
            r.update(calc_costs(r["concrete"], r["rebar"], r["formwork"], cp, rp, fp))


def _ctx(calcs):
    """计算模板上下文"""
    has_costs = any("total_cost" in r for r in calcs)
    ctx = {
        "calcs": calcs,
        "has_costs": has_costs,
        "total_rebar": round(sum(r["rebar"] for r in calcs), 1),
        "total_concrete": round(sum(r["concrete"] for r in calcs), 3),
        "total_formwork": round(sum(r["formwork"] for r in calcs), 2),
        "total_area": round(sum(r.get("rebar_area", 0) for r in calcs), 0),
    }
    if has_costs:
        ctx["total_concrete_cost"] = round(sum(r.get("concrete_cost", 0) for r in calcs), 2)
        ctx["total_rebar_cost"] = round(sum(r.get("rebar_cost", 0) for r in calcs), 2)
        ctx["total_formwork_cost"] = round(sum(r.get("formwork_cost", 0) for r in calcs), 2)
        ctx["total_all_cost"] = round(sum(r.get("total_cost", 0) for r in calcs), 2)
    return ctx


# ============================================================
# 路由
# ============================================================

@app.route("/")
def index():
    calcs = session.get("calcs", [])
    prices = session.get("prices")
    ctx = _ctx(calcs)
    ctx["prices"] = prices
    ctx["cover_defaults"] = {
        'slab': cover_min('slab'),
        'beam': cover_min('beam'),
        'column': cover_min('column'),
    }
    ctx["diameters"] = COMMON_DIAMETERS
    return render_template("index.html", **ctx)


@app.route("/add", methods=["POST"])
def add():
    """统一提交入口：根据 mode 字段决定用快速估算还是精确配筋"""
    mode = request.form.get("mode", "quick")
    name = request.form.get("name", "").strip()

    calcs = session.get("calcs", [])

    if mode == "precise":
        calc = _handle_precise(name, request.form)
    else:
        calc = _handle_quick(name, request.form)

    # 单价处理
    cp = _safe_float(request.form.get("concrete_price"))
    rp = _safe_float(request.form.get("rebar_price"))
    fp = _safe_float(request.form.get("formwork_price"))

    if any(x is not None for x in (cp, rp, fp)):
        session["prices"] = {"concrete_price": cp, "rebar_price": rp, "formwork_price": fp}

    # 如果已设单价，给所有记录（含旧记录）补算费用
    prices = session.get("prices")
    if prices:
        _apply_prices(calcs, prices)

    # 新记录也加上费用
    if prices:
        calc.update(calc_costs(
            calc["concrete"], calc["rebar"], calc["formwork"],
            prices["concrete_price"], prices["rebar_price"], prices["formwork_price"]
        ))

    calcs.append(calc)
    session["calcs"] = calcs

    ctx = _ctx(calcs)
    ctx["prices"] = session.get("prices")
    ctx["cover_defaults"] = {
        'slab': cover_min('slab'),
        'beam': cover_min('beam'),
        'column': cover_min('column'),
    }
    ctx["diameters"] = COMMON_DIAMETERS
    return render_template("index.html", **ctx)


def _handle_quick(name, form):
    """快速估算模式（保留原有逻辑）"""
    length = _safe_float(form.get("length"), 0)
    width  = _safe_float(form.get("width"), 0)
    height = _safe_float(form.get("height"), 0)
    ratio  = _safe_float(form.get("rebar_ratio"), 1.0) / 100.0

    concrete   = calc_concrete(length, width, height)
    rebar_area = calc_rebar_area(width, height, ratio)
    rebar      = calc_rebar(concrete, ratio)
    formwork   = calc_formwork(length, width, height)

    return {
        "name": name,
        "mode": "quick",
        "type": None,
        "length": length,
        "width": width,
        "height": height,
        "rebar_ratio": ratio,
        "concrete":   round(concrete, 3),
        "rebar_area": round(rebar_area, 0),
        "rebar":      round(rebar, 1),
        "formwork":   round(formwork, 2),
        "timestamp":  datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def _handle_precise(name, form):
    """精确配筋模式"""
    comp_type = form.get("comp_type", "slab")

    if comp_type == "slab":
        inputs = {
            'L': _safe_float(form.get("L")),
            'W': _safe_float(form.get("W")),
            't_slab': _safe_float(form.get("t_slab"), 120),
            'cover': _safe_float(form.get("cover"), cover_min('slab')),
            'd_btm_short': _safe_float(form.get("d_btm_short")),
            's_btm_short': _safe_float(form.get("s_btm_short")),
            'd_btm_long': _safe_float(form.get("d_btm_long")),
            's_btm_long': _safe_float(form.get("s_btm_long")),
            'd_top_short': _safe_float(form.get("d_top_short")) or 0,
            's_top_short': _safe_float(form.get("s_top_short")) or 0,
            'd_top_long': _safe_float(form.get("d_top_long")) or 0,
            's_top_long': _safe_float(form.get("s_top_long")) or 0,
            'rebar_type': form.get("rebar_type", "HRB400"),
        }
        result = calc_slab(inputs)
        dimensions = {
            '长(m)': inputs['L'], '宽(m)': inputs['W'],
            '板厚(mm)': inputs['t_slab'],
            '保护层(mm)': inputs['cover'],
        }

    elif comp_type == "beam":
        inputs = {
            'L': _safe_float(form.get("L")),
            'b': _safe_float(form.get("b"), 250),
            'h': _safe_float(form.get("h"), 500),
            'cover': _safe_float(form.get("cover"), cover_min('beam')),
            'n_top': _safe_float(form.get("n_top")),
            'd_top': _safe_float(form.get("d_top")),
            'n_btm': _safe_float(form.get("n_btm")),
            'd_btm': _safe_float(form.get("d_btm")),
            'd_stirrup': _safe_float(form.get("d_stirrup")),
            's_stirrup': _safe_float(form.get("s_stirrup")),
            'legs': _safe_float(form.get("legs"), 2),
            'n_waist': _safe_float(form.get("n_waist")) or 0,
            'd_waist': _safe_float(form.get("d_waist"), 12),
            'has_dense': form.get("has_dense") == 'on',
            'L_dense': _safe_float(form.get("L_dense"), 1.5 * _safe_float(form.get("h"), 500)),
            's_dense': _safe_float(form.get("s_dense"), 100),
            'anchor_len': _safe_float(form.get("anchor_len")) or None,
            'rebar_type': form.get("rebar_type", "HRB400"),
        }
        result = calc_beam(inputs)
        dimensions = {
            '长(m)': inputs['L'], '截面宽(mm)': inputs['b'],
            '截面高(mm)': inputs['h'], '保护层(mm)': inputs['cover'],
        }

    elif comp_type == "column":
        inputs = {
            'b': _safe_float(form.get("b")),
            'h_sec': _safe_float(form.get("h_sec")),
            'H': _safe_float(form.get("H")),
            'cover': _safe_float(form.get("cover"), cover_min('column')),
            'n_long': _safe_float(form.get("n_long")),
            'd_long': _safe_float(form.get("d_long")),
            'd_stirrup': _safe_float(form.get("d_stirrup")),
            's_stirrup': _safe_float(form.get("s_stirrup")),
            'legs': form.get("legs", "2x2"),
            'lap_len': _safe_float(form.get("lap_len")) or None,
            'rebar_type': form.get("rebar_type", "HRB400"),
        }
        result = calc_column(inputs)
        dimensions = {
            '截面宽(mm)': inputs['b'], '截面高(mm)': inputs['h_sec'],
            '柱高(m)': inputs['H'], '保护层(mm)': inputs['cover'],
        }

    else:
        raise ValueError(f"Unknown component type: {comp_type}")

    return {
        "name": name,
        "mode": "precise",
        "type": comp_type,
        "dimensions": dimensions,
        "concrete":   result["concrete"],
        "formwork":   result["formwork"],
        "rebar":      result["rebar"],
        "rebar_area": result["rebar_area"],
        "rebar_per_m3": result.get("rebar_per_m3", 0),
        "detail":     result["detail"],
        "timestamp":  datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


@app.route("/export")
def export():
    calcs = session.get("calcs", [])
    if not calcs:
        return "no data to export", 400

    filename = f"rebar_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join("static", filename)
    save_excel(calcs, filepath)
    return send_file(filepath, as_attachment=True, download_name=filename)


@app.route("/clear")
def clear():
    session["calcs"] = []
    session.pop("prices", None)
    return render_template("index.html",
                           calcs=[], has_costs=False,
                           total_rebar=0, total_concrete=0,
                           total_formwork=0, total_area=0,
                           prices=None,
                           cover_defaults={
                               'slab': cover_min('slab'),
                               'beam': cover_min('beam'),
                               'column': cover_min('column'),
                           },
                           diameters=COMMON_DIAMETERS)


if __name__ == "__main__":
    print("=" * 50)
    print(" 工程算量小助手 v2.0")
    print(" http://127.0.0.1:5001")
    print("=" * 50)
    app.run(debug=True, port=5001)
