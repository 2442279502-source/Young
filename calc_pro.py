# -*- coding: utf-8 -*-
"""
专业配筋计算模块 — 工程算量小助手
==================================
板 (Slab)、梁 (Beam)、柱 (Column) 三种构件的精确钢筋计算。

所有公式基于：
  - GB 50010-2010 (2015年版) 《混凝土结构设计规范》
  - GB 50011-2010 (2016年版) 《建筑抗震设计规范》
  - GB 55008-2021  《混凝土结构通用规范》

用法:
    from calc_pro import calc_slab, calc_beam, calc_column
    result = calc_slab({...})
"""

import math
from gb_standards import (
    unit_weight, hook_add_180, hook_add_135_stirrup, cover_min,
    calc_anchor_length, calc_lap_length)


# ============================================================
# 内部辅助函数
# ============================================================

def _calc_bars(span_dist_mm, span_bar_mm, cover, d, s, rebar_type, is_stirrup=False):
    """计算一组钢筋的根数、每根长度、总重、面积

    参数:
        span_dist_mm: 分布跨度的长度 (mm) — 钢筋沿这个方向排列
        span_bar_mm:  每根钢筋跨度的长度 (mm) — 钢筋本身的长度方向
        cover:        保护层厚度 (mm)
        d:            钢筋直径 (mm)
        s:            钢筋间距 (mm)
        rebar_type:   'HPB300' | 'HRB400'
        is_stirrup:   是否是箍筋（箍筋用 135° 弯钩）

    返回:
        {count, len_mm, unit_w, total_kg, area_mm2}
    """
    # 根数
    count = int((span_dist_mm - 2 * cover) / s) + 1
    if count < 1:
        count = 1

    # 每根长度（含弯钩）
    if is_stirrup:
        hook = 0  # 箍筋弯钩由调用方单独计算
    elif rebar_type == 'HPB300':
        hook = 2 * hook_add_180(d)  # 两端 180° 弯钩
    else:
        hook = 0

    bar_len = span_bar_mm - 2 * cover + hook

    uw = unit_weight(d)
    total_kg = count * (bar_len / 1000.0) * uw
    area_mm2 = count * math.pi * (d / 2.0) ** 2

    return {
        'count':      count,
        'len_mm':     round(bar_len, 0),
        'unit_w':     uw,
        'total_kg':   round(total_kg, 1),
        'area_mm2':   round(area_mm2, 0),
        'diameter':   d,
        'spacing':    s,
    }


def _stirrup_unfold_len(b, h, cover, d_s, legs):
    """箍筋展开长度 (mm)

    参数:
        b, h:   截面宽、高 (mm)
        cover:  保护层 (mm)
        d_s:    箍筋直径 (mm)
        legs:   肢数 (2 或 4)

    返回:
        每根箍筋展开长度 (mm)
    """
    # 外框周长
    outer = 2 * (b - 2 * cover) + 2 * (h - 2 * cover)

    # 两个 135° 弯钩增加值
    hooks = 2 * hook_add_135_stirrup(d_s)

    if legs == 2:
        return round(outer + hooks, 0)
    elif legs == 4:
        # 4 肢箍：外框 + 2 根内肢竖筋
        interior_w = (b - 2 * cover - d_s) / 3.0  # 每格宽度
        interior_v = 2 * (h - 2 * cover)           # 2 根内肢竖筋
        return round(outer + interior_v + hooks, 0)
    else:
        # 默认 2 肢
        return round(outer + hooks, 0)


# ============================================================
# 1. 板 (Slab) 配筋计算
# ============================================================

def calc_slab(inputs):
    """楼板/底板配筋计算

    必需参数:
        L, W:          板长、板宽 (m)
        t_slab:        板厚 (mm)
        d_btm_short:   底筋短跨直径 (mm)
        s_btm_short:   底筋短跨间距 (mm)
        d_btm_long:    底筋长跨直径 (mm)
        s_btm_long:    底筋长跨间距 (mm)

    可选参数:
        cover:         保护层厚度 (mm), 默认 15
        d_top_short:   面筋短跨直径 (mm), 0 或 None 表示无面筋
        s_top_short:   面筋短跨间距 (mm)
        d_top_long:    面筋长跨直径 (mm)
        s_top_long:    面筋长跨间距 (mm)
        rebar_type:    'HPB300' | 'HRB400', 默认 'HRB400'
    """
    L = float(inputs.get('L', 0))
    W = float(inputs.get('W', 0))
    t_slab = float(inputs.get('t_slab', 100))
    cover = float(inputs.get('cover', cover_min('slab')))

    rebar_type = inputs.get('rebar_type', 'HRB400')

    # 确定短跨/长跨方向
    L_mm = L * 1000
    W_mm = W * 1000
    short_span = min(L_mm, W_mm)
    long_span = max(L_mm, W_mm)

    detail = {}

    # --- 底筋短跨 ---
    d_bs = int(inputs.get('d_btm_short', 0))
    s_bs = int(inputs.get('s_btm_short', 0))
    if d_bs > 0 and s_bs > 0:
        detail['bottom_short'] = _calc_bars(
            long_span, short_span, cover, d_bs, s_bs, rebar_type)
        detail['bottom_short']['label'] = '底筋短跨'

    # --- 底筋长跨 ---
    d_bl = int(inputs.get('d_btm_long', 0))
    s_bl = int(inputs.get('s_btm_long', 0))
    if d_bl > 0 and s_bl > 0:
        detail['bottom_long'] = _calc_bars(
            short_span, long_span, cover, d_bl, s_bl, rebar_type)
        detail['bottom_long']['label'] = '底筋长跨'

    # --- 面筋短跨 (可选) ---
    d_ts = int(inputs.get('d_top_short', 0) or 0)
    s_ts = int(inputs.get('s_top_short', 0) or 0)
    if d_ts > 0 and s_ts > 0:
        detail['top_short'] = _calc_bars(
            long_span, short_span, cover, d_ts, s_ts, rebar_type)
        detail['top_short']['label'] = '面筋短跨'

    # --- 面筋长跨 (可选) ---
    d_tl = int(inputs.get('d_top_long', 0) or 0)
    s_tl = int(inputs.get('s_top_long', 0) or 0)
    if d_tl > 0 and s_tl > 0:
        detail['top_long'] = _calc_bars(
            short_span, long_span, cover, d_tl, s_tl, rebar_type)
        detail['top_long']['label'] = '面筋长跨'

    # --- 汇总 ---
    total_kg = sum(v['total_kg'] for v in detail.values())
    total_area = sum(v['area_mm2'] for v in detail.values())
    concrete_m3 = round(L * W * t_slab / 1000.0, 3)
    # 模板：底面 + 四侧（侧面高度 = 板厚）
    formwork_m2 = round(L * W + 2 * L * t_slab / 1000.0 + 2 * W * t_slab / 1000.0, 2)

    return {
        'concrete':      concrete_m3,
        'formwork':      formwork_m2,
        'rebar':         round(total_kg, 1),
        'rebar_area':    round(total_area, 0),
        'rebar_per_m3':  round(total_kg / concrete_m3, 1) if concrete_m3 > 0 else 0,
        'detail':        detail,
    }


# ============================================================
# 2. 梁 (Beam) 配筋计算
# ============================================================

def calc_beam(inputs):
    """框架梁/次梁配筋计算

    必需参数:
        L:           梁长 (m)
        b:           截面宽 (mm)
        h:           截面高 (mm)
        n_top:       上部纵筋根数
        d_top:       上部纵筋直径 (mm)
        n_btm:       下部纵筋根数
        d_btm:       下部纵筋直径 (mm)
        d_stirrup:   箍筋直径 (mm)
        s_stirrup:   箍筋间距 (mm)

    可选参数:
        cover:       保护层厚度 (mm), 默认 20
        n_waist:     腰筋每侧根数, 默认 0
        d_waist:     腰筋直径 (mm), 默认 12
        legs:        箍筋肢数, 默认 2
        has_dense:   是否设加密区, 默认 False
        L_dense:     加密区长度 (mm), 默认 1.5*h
        s_dense:     加密区间距 (mm), 默认 100
        anchor_len:  锚固长度 (mm), 默认自动按 C30+HRB400 计算
        rebar_type:  'HPB300' | 'HRB400', 默认 'HRB400'
        concrete:    混凝土等级, 默认 'C30'
    """
    L = float(inputs.get('L', 0))
    b = float(inputs.get('b', 250))
    h = float(inputs.get('h', 500))
    cover = float(inputs.get('cover', cover_min('beam')))
    rebar_type = inputs.get('rebar_type', 'HRB400')
    concrete_grade = inputs.get('concrete', 'C30')

    # 锚固长度
    anchor_ov = inputs.get('anchor_len', None)
    if anchor_ov is not None and float(anchor_ov) > 0:
        anchor_len = float(anchor_ov)
    else:
        # 取上部下部最大直径算锚固
        d_max = max(
            int(inputs.get('d_top', 0)),
            int(inputs.get('d_btm', 0)),
        )
        anchor_len = calc_anchor_length(d_max, concrete_grade, rebar_type) if d_max > 0 else 700

    L_mm = L * 1000
    detail = {}

    # --- 上部纵筋 ---
    n_top = int(inputs.get('n_top', 0))
    d_top = int(inputs.get('d_top', 0))
    if n_top > 0 and d_top > 0:
        bar_len = L_mm - 2 * cover + 2 * anchor_len
        uw = unit_weight(d_top)
        total_kg = n_top * (bar_len / 1000.0) * uw
        detail['top_bars'] = {
            'count':    n_top,
            'len_mm':   round(bar_len, 0),
            'unit_w':   uw,
            'total_kg': round(total_kg, 1),
            'area_mm2': round(n_top * math.pi * (d_top / 2) ** 2, 0),
            'diameter': d_top,
            'label':    '上部纵筋',
        }

    # --- 下部纵筋 ---
    n_btm = int(inputs.get('n_btm', 0))
    d_btm = int(inputs.get('d_btm', 0))
    if n_btm > 0 and d_btm > 0:
        bar_len = L_mm - 2 * cover + 2 * anchor_len
        uw = unit_weight(d_btm)
        total_kg = n_btm * (bar_len / 1000.0) * uw
        detail['bottom_bars'] = {
            'count':    n_btm,
            'len_mm':   round(bar_len, 0),
            'unit_w':   uw,
            'total_kg': round(total_kg, 1),
            'area_mm2': round(n_btm * math.pi * (d_btm / 2) ** 2, 0),
            'diameter': d_btm,
            'label':    '下部纵筋',
        }

    # --- 腰筋 (截面高 > 450mm 时常用) ---
    n_waist = int(inputs.get('n_waist', 0) or 0)
    d_waist = int(inputs.get('d_waist', 12))
    if n_waist > 0 and d_waist > 0:
        # 腰筋锚固长度取 15d (构造筋)
        waist_anchor = 15 * d_waist
        bar_len = L_mm - 2 * cover + 2 * waist_anchor
        n_total = n_waist * 2  # 两侧
        uw = unit_weight(d_waist)
        total_kg = n_total * (bar_len / 1000.0) * uw
        detail['waist_bars'] = {
            'count':    n_total,
            'len_mm':   round(bar_len, 0),
            'unit_w':   uw,
            'total_kg': round(total_kg, 1),
            'area_mm2': round(n_total * math.pi * (d_waist / 2) ** 2, 0),
            'diameter': d_waist,
            'label':    '腰筋（两侧）',
        }

    # --- 箍筋 ---
    d_s = int(inputs.get('d_stirrup', 0))
    s_s = int(inputs.get('s_stirrup', 0))
    legs = int(inputs.get('legs', 2))
    has_dense = inputs.get('has_dense', False) in (True, 'true', 'on', '1')
    L_dense = float(inputs.get('L_dense', 1.5 * h))
    s_dense = int(inputs.get('s_dense', 100))

    if d_s > 0 and s_s > 0:
        unfold = _stirrup_unfold_len(b, h, cover, d_s, legs)

        if has_dense and L_dense > 0 and s_dense > 0:
            # 两端各一个加密区
            n_dense_per = int(L_dense / s_dense) + 1
            n_dense = n_dense_per * 2
            L_normal = L_mm - 2 * cover - 2 * L_dense * 2  # wait, L_dense is per end
            # Actually: L_normal = L*1000 - 2*cover - 2*L_dense
            # Let me recalculate
            L_clear = L_mm - 2 * cover
            L_dense_total = 2 * L_dense  # both ends
            L_normal = max(0, L_clear - L_dense_total)
            n_normal = int(L_normal / s_s) + 1 if L_normal > 0 else 0
            n_total = n_dense + n_normal
        else:
            n_total = int((L_mm - 2 * cover) / s_s) + 1

        uw = unit_weight(d_s)
        total_kg = n_total * (unfold / 1000.0) * uw

        stirrup_info = {
            'count':    n_total,
            'len_mm':   round(unfold, 0),
            'unit_w':   uw,
            'total_kg': round(total_kg, 1),
            'area_mm2': round(n_total * math.pi * (d_s / 2) ** 2, 0),
            'diameter': d_s,
            'label':    f'箍筋({legs}肢)',
        }
        if has_dense:
            stirrup_info['dense_zone'] = f'加密区各{L_dense:.0f}mm @{s_dense}mm, 非加密区@{s_s}mm'
        detail['stirrups'] = stirrup_info

    # --- 汇总 ---
    total_kg = sum(v['total_kg'] for v in detail.values())
    total_area = sum(v['area_mm2'] for v in detail.values())
    concrete_m3 = round(L * b / 1000.0 * h / 1000.0, 3)
    # 模板：底面 + 两侧面（梁顶不支模）
    formwork_m2 = round(L * b / 1000.0 + 2 * L * h / 1000.0, 2)

    return {
        'concrete':      concrete_m3,
        'formwork':      formwork_m2,
        'rebar':         round(total_kg, 1),
        'rebar_area':    round(total_area, 0),
        'rebar_per_m3':  round(total_kg / concrete_m3, 1) if concrete_m3 > 0 else 0,
        'detail':        detail,
    }


# ============================================================
# 3. 柱 (Column) 配筋计算
# ============================================================

def calc_column(inputs):
    """框架柱/构造柱配筋计算

    必需参数:
        b, h_sec:    截面宽、高 (mm)
        H:           柱高 (m)
        n_long:      全部纵筋根数
        d_long:      纵筋直径 (mm)
        d_stirrup:   箍筋直径 (mm)
        s_stirrup:   箍筋间距 (mm)

    可选参数:
        cover:       保护层厚度 (mm), 默认 20
        legs:        箍筋肢数 ('2x2' | '3x3' | '4x4'), 默认 '2x2'
        lap_len:     搭接长度 (mm), 默认自动按 50% 搭接率计算
        rebar_type:  'HPB300' | 'HRB400', 默认 'HRB400'
        concrete:    混凝土等级, 默认 'C30'
    """
    b = float(inputs.get('b', 400))
    h_sec = float(inputs.get('h_sec', 400))
    H = float(inputs.get('H', 0))
    cover = float(inputs.get('cover', cover_min('column')))
    rebar_type = inputs.get('rebar_type', 'HRB400')
    concrete_grade = inputs.get('concrete', 'C30')

    detail = {}

    # --- 纵筋 ---
    n_long = int(inputs.get('n_long', 0))
    d_long = int(inputs.get('d_long', 0))
    if n_long > 0 and d_long > 0:
        # 搭接长度
        lap_ov = inputs.get('lap_len', None)
        if lap_ov is not None and float(lap_ov) > 0:
            lap_len = float(lap_ov)
        else:
            anchor = calc_anchor_length(d_long, concrete_grade, rebar_type)
            lap_len = calc_lap_length(anchor, 0.5)  # 50% 搭接率

        bar_len = H * 1000 + lap_len
        uw = unit_weight(d_long)
        total_kg = n_long * (bar_len / 1000.0) * uw
        detail['long_bars'] = {
            'count':    n_long,
            'len_mm':   round(bar_len, 0),
            'unit_w':   uw,
            'total_kg': round(total_kg, 1),
            'area_mm2': round(n_long * math.pi * (d_long / 2) ** 2, 0),
            'diameter': d_long,
            'label':    '纵筋',
        }

    # --- 箍筋 ---
    d_s = int(inputs.get('d_stirrup', 0))
    s_s = int(inputs.get('s_stirrup', 0))
    legs_str = inputs.get('legs', '2x2')

    if d_s > 0 and s_s > 0:
        # 解析肢数
        if '4' in str(legs_str):
            legs_num = 4
        elif '3' in str(legs_str):
            legs_num = 3
        else:
            legs_num = 2

        # 柱箍筋展开长
        # 外框 + 内肢
        outer = 2 * (b - 2 * cover) + 2 * (h_sec - 2 * cover)
        hooks = 2 * hook_add_135_stirrup(d_s)

        if legs_num == 2:
            # 2×2：一个外框
            unfold = outer + hooks
        elif legs_num == 3:
            # 3×3：外框 + 2 根内肢 (b向1根, h向1根)
            inner_b = h_sec - 2 * cover  # 内肢平行于 h 方向
            inner_h = b - 2 * cover      # 内肢平行于 b 方向
            unfold = outer + inner_b + inner_h + hooks
        else:
            # 4×4：外框 + 4 根内肢 (b向2根, h向2根)
            inner_b = 2 * (h_sec - 2 * cover)
            inner_h = 2 * (b - 2 * cover)
            unfold = outer + inner_b + inner_h + hooks

        n_total = int((H * 1000 - 2 * cover) / s_s) + 1

        uw = unit_weight(d_s)
        total_kg = n_total * (unfold / 1000.0) * uw

        detail['stirrups'] = {
            'count':    n_total,
            'len_mm':   round(unfold, 0),
            'unit_w':   uw,
            'total_kg': round(total_kg, 1),
            'area_mm2': round(n_total * math.pi * (d_s / 2) ** 2, 0),
            'diameter': d_s,
            'label':    f'箍筋({legs_str})',
        }

    # --- 汇总 ---
    total_kg = sum(v['total_kg'] for v in detail.values())
    total_area = sum(v['area_mm2'] for v in detail.values())
    concrete_m3 = round(b / 1000.0 * h_sec / 1000.0 * H, 3)
    # 模板：四侧
    formwork_m2 = round(2 * (b + h_sec) / 1000.0 * H, 2)

    return {
        'concrete':      concrete_m3,
        'formwork':      formwork_m2,
        'rebar':         round(total_kg, 1),
        'rebar_area':    round(total_area, 0),
        'rebar_per_m3':  round(total_kg / concrete_m3, 1) if concrete_m3 > 0 else 0,
        'detail':        detail,
    }


# ============================================================
# 统一调度：根据类型自动调用对应函数
# ============================================================

def calculate(inputs):
    """统一计算入口

    inputs 必须包含 'type' 字段:
        'slab'   → calc_slab
        'beam'   → calc_beam
        'column' → calc_column

    返回统一格式的 result dict
    """
    comp_type = inputs.get('type', 'slab')
    if comp_type == 'slab':
        return calc_slab(inputs)
    elif comp_type == 'beam':
        return calc_beam(inputs)
    elif comp_type == 'column':
        return calc_column(inputs)
    else:
        raise ValueError(f"Unknown component type: {comp_type}")


# ============================================================
# 自检
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Professional Rebar Calculation Self-Check")
    print("=" * 60)

    # ---- 板 ----
    print("\n[1] Slab: 4.2m x 3.6m x 120mm")
    print("    bottom: short phi10@150, long phi10@200")
    result = calc_slab({
        'L': 4.2, 'W': 3.6, 't_slab': 120,
        'd_btm_short': 10, 's_btm_short': 150,
        'd_btm_long': 10, 's_btm_long': 200,
        'rebar_type': 'HRB400',
    })
    print(f"    concrete:  {result['concrete']} m3  (expected: 1.814 m3)")
    print(f"    formwork:  {result['formwork']} m2")
    print(f"    total kg:  {result['rebar']} kg")
    print(f"    total mm2: {result['rebar_area']} mm2")
    print(f"    kg/m3:     {result['rebar_per_m3']}")
    for k, v in result['detail'].items():
        print(f"    {v['label']}: count={v['count']}, len={v['len_mm']}mm, "
              f"unit_w={v['unit_w']}, total_kg={v['total_kg']}kg, area={v['area_mm2']}mm2")

    # ---- 梁 ----
    print("\n[2] Beam: 3m, 250x500mm")
    print("    top: 2phi18, bottom: 3phi20, stirrup: phi8@200(2)")
    result = calc_beam({
        'L': 3.0, 'b': 250, 'h': 500,
        'n_top': 2, 'd_top': 18,
        'n_btm': 3, 'd_btm': 20,
        'd_stirrup': 8, 's_stirrup': 200, 'legs': 2,
        'rebar_type': 'HRB400',
    })
    print(f"    concrete:  {result['concrete']} m3  (expected: 0.375 m3)")
    print(f"    formwork:  {result['formwork']} m2")
    print(f"    total kg:  {result['rebar']} kg")
    for k, v in result['detail'].items():
        print(f"    {v['label']}: count={v['count']}, len={v['len_mm']}mm, "
              f"total_kg={v['total_kg']}kg")

    # ---- 柱 ----
    print("\n[3] Column: 400x400mm, H=3m")
    print("    long: 8phi20, stirrup: phi8@150(2x2)")
    result = calc_column({
        'b': 400, 'h_sec': 400, 'H': 3.0,
        'n_long': 8, 'd_long': 20,
        'd_stirrup': 8, 's_stirrup': 150, 'legs': '2x2',
        'rebar_type': 'HRB400',
    })
    print(f"    concrete:  {result['concrete']} m3  (expected: 0.48 m3)")
    print(f"    formwork:  {result['formwork']} m2")
    print(f"    total kg:  {result['rebar']} kg")
    for k, v in result['detail'].items():
        print(f"    {v['label']}: count={v['count']}, len={v['len_mm']}mm, "
              f"total_kg={v['total_kg']}kg")

    print("\n" + "=" * 60)
    print("Self-check complete")
