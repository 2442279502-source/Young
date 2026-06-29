# -*- coding: utf-8 -*-
"""
GB 标准常数模块 — 工程算量小助手
================================
所有常数和公式均引用自中国国家标准（最新有效版本）：
  - GB 50010-2010 (2015年版) 《混凝土结构设计规范》
  - GB 50011-2010 (2016年版) 《建筑抗震设计规范》
  - GB 55008-2021  《混凝土结构通用规范》（全文强制，2022.4.1 实施）
  - GB/T 1499.2-2018 《钢筋混凝土用钢 第2部分：热轧带肋钢筋》
  - 钢材密度 7850 kg/m³ 为上述标准统一取值

每个函数都标注了出处，方便核对。
"""

import math

# ============================================================
# 1. 钢筋理论重量
#    GB 1499.2: w = 0.00617 × d² (kg/m)
#    推导: w = π × d²/4 × 7850 / 1,000,000 = 0.006165 × d² ≈ 0.00617 × d²
# ============================================================

def unit_weight(diameter_mm):
    """钢筋每米理论重量 (kg/m)

    公式: w = 0.00617 × d²
    出处: GB 1499.2

    示例:
        unit_weight(10) → 0.617  (φ10 每米重 0.617 kg)
        unit_weight(20) → 2.468  (φ20 每米重 2.47 kg)
    """
    return round(diameter_mm ** 2 * 0.00617, 3)


# 常用直径速查表 (kg/m) —— 用于快速校验
UNIT_WEIGHT_TABLE = {
    6:  0.222,  8:  0.395,  10: 0.617,  12: 0.888,
    14: 1.210,  16: 1.580,  18: 2.000,  20: 2.470,
    22: 2.980,  25: 3.850,  28: 4.830,  32: 6.310,
    36: 7.990,  40: 9.870,
}

# ============================================================
# 2. 弯钩增加长度
# ============================================================

def hook_add_180(diameter_mm):
    """HPB300 180° 弯钩增加长度 (mm)

    公式: 6.25 × d
    出处: GB 50010-2010 第 9.3.1 条
    组成: 3d (平直段) + 3.25d (半圆弧, D=2.5d) = 6.25d

    仅用于 HPB300 光圆钢筋。
    HRB400 带肋钢筋不设 180° 弯钩。
    """
    return 6.25 * diameter_mm


def hook_add_135_stirrup(diameter_mm):
    """箍筋 135° 弯钩增加长度（单端，抗震）(mm)

    公式: 11.9 × d
    出处: GB 50010-2010 第 11.3.8 条
    组成: 10d (平直段) + 1.9d (135°弧段超出, D=4d)

    用于抗震结构箍筋两端 135° 弯钩。
    非抗震: 平直段 5d, 即 5d + 1.9d = 6.9d
    """
    return 11.9 * diameter_mm


def hook_add_for_rebar(diameter_mm, rebar_type, stirrup_seismic=True):
    """通用弯钩增加值

    参数:
        diameter_mm: 钢筋直径 (mm)
        rebar_type:  'HPB300' | 'HRB400' | 'HRB500'
        stirrup_seismic: 是否是抗震箍筋（仅对 HRB400 箍筋有效）

    返回:
        弯钩增加值 (mm)，无弯钩返回 0
    """
    if rebar_type == 'HPB300':
        # HPB300 光圆钢筋，必须做 180° 弯钩
        return hook_add_180(diameter_mm)
    elif rebar_type in ('HRB400', 'HRB500'):
        # HRB400/HRB500 带肋钢筋，纵筋不需弯钩
        # 但箍筋需要 135° 弯钩（抗震）或 90°/135°（非抗震）
        # 此处由调用方区分
        return 0.0
    return 0.0


# ============================================================
# 3. 保护层最小厚度
#    GB 50010-2010 表 8.2.1（一类环境）
# ============================================================

def cover_min(elem_type):
    """混凝土保护层最小厚度 (mm)

    出处: GB 50010-2010 表 8.2.1

    参数:
        elem_type: 'slab' | 'beam' | 'column' | 'wall' | 'foundation'

    一类环境（室内干燥环境）:
        板、墙:    15mm
        梁、柱:    20mm
        基础:      40mm (有垫层)
    """
    table = {
        'slab':       15,   # 板
        'wall':       15,   # 墙
        'beam':       20,   # 梁
        'column':     20,   # 柱
        'foundation': 40,   # 基础（有垫层）
    }
    return table.get(elem_type, 20)


# ============================================================
# 4. 锚固长度
#    GB 50010-2010 第 8.3.1 条
#    基本锚固长度 lab = α × (fy / ft) × d
# ============================================================

# 混凝土轴心抗拉强度设计值 ft (N/mm²)
CONCRETE_FT = {
    'C20': 1.10, 'C25': 1.27, 'C30': 1.43,
    'C35': 1.57, 'C40': 1.71, 'C45': 1.80, 'C50': 1.89,
}

# 钢筋抗拉强度设计值 fy (N/mm²)
REBAR_FY = {
    'HPB300': 270,
    'HRB400': 360,
    'HRB500': 435,
}

# 钢筋外形系数 α
# HPB300 光圆钢筋: 0.16
# HRB400/HRB500 带肋钢筋: 0.14
REBAR_ALPHA = {
    'HPB300': 0.16,
    'HRB400': 0.14,
    'HRB500': 0.14,
}


def calc_anchor_length(diameter_mm, concrete='C30', rebar_type='HRB400'):
    """计算基本锚固长度 lab (mm)

    公式: lab = α × (fy / ft) × d
    出处: GB 50010-2010 第 8.3.1 条

    参数:
        diameter_mm: 钢筋直径 (mm)
        concrete:    混凝土强度等级 ('C20' ~ 'C50')
        rebar_type:  钢筋类型 ('HPB300' | 'HRB400' | 'HRB500')

    返回:
        基本锚固长度 (mm)，向上取整到 5mm

    示例:
        calc_anchor_length(20, 'C30', 'HRB400') → 705  (≈ 35d)
    """
    alpha = REBAR_ALPHA.get(rebar_type, 0.14)
    fy = REBAR_FY.get(rebar_type, 360)
    ft = CONCRETE_FT.get(concrete, 1.43)

    lab = alpha * (fy / ft) * diameter_mm
    # 向上取整到 5mm
    return math.ceil(lab / 5) * 5


# 锚固长度速查因子表 { (concrete, rebar_type): lab/d }
# 用于快速查表，避免重复计算
ANCHOR_FACTOR_TABLE = {
    ('C20', 'HPB300'): 39,  ('C20', 'HRB400'): 46,  ('C20', 'HRB500'): 55,
    ('C25', 'HPB300'): 34,  ('C25', 'HRB400'): 40,  ('C25', 'HRB500'): 48,
    ('C30', 'HPB300'): 30,  ('C30', 'HRB400'): 35,  ('C30', 'HRB500'): 43,
    ('C35', 'HPB300'): 28,  ('C35', 'HRB400'): 32,  ('C35', 'HRB500'): 39,
    ('C40', 'HPB300'): 25,  ('C40', 'HRB400'): 30,  ('C40', 'HRB500'): 36,
}


def get_anchor_factor(concrete='C30', rebar_type='HRB400'):
    """获取锚固长度倍数 (lab/d)

    返回 lab = factor × d 中的 factor
    """
    return ANCHOR_FACTOR_TABLE.get((concrete, rebar_type), 35)


# ============================================================
# 5. 搭接长度
#    GB 50010-2010 第 8.4.3 条
#    ll = ζl × lab
# ============================================================

def calc_lap_length(anchor_length_mm, lap_pct=0.5):
    """计算纵向受拉钢筋搭接长度 ll (mm)

    公式: ll = ζl × lab
    出处: GB 50010-2010 第 8.4.3 条

    参数:
        anchor_length_mm: 基本锚固长度 (mm)
        lap_pct:          搭接接头面积百分率
                          0.25 → ζl = 1.2
                          0.50 → ζl = 1.4
                          1.00 → ζl = 1.6

    返回:
        搭接长度 (mm)
    """
    zeta_map = {0.25: 1.2, 0.5: 1.4, 1.0: 1.6}
    zeta = zeta_map.get(lap_pct, 1.4)
    return round(anchor_length_mm * zeta)


# ============================================================
# 6. 常用直径列表（给下拉菜单用）
# ============================================================

COMMON_DIAMETERS = [6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 32]
COMMON_SPACINGS = [100, 120, 150, 180, 200, 250, 300]
COMMON_STIRRUP_LEGS = [2, 4]  # 箍筋肢数（梁）；柱用 2×2, 3×3, 4×4


# ============================================================
# 7. 自检（直接运行本文件时执行）
# ============================================================

if __name__ == '__main__':
    print("=" * 50)
    print("GB 标准常数自检")
    print("=" * 50)

    # 单位重量校验
    print("\n[1] rebar unit weight (kg/m):")
    for d in [6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 32]:
        calc = unit_weight(d)
        std = UNIT_WEIGHT_TABLE.get(d, 'N/A')
        ok = 'OK' if abs(calc - std) < 0.01 else 'MISMATCH!'
        print(f"   d={d}: {calc} kg/m  (std {std}) {ok}")

    # 弯钩增加值
    print("\n[2] hook addition length:")
    print(f"   HPB300 d=8  180deg hook: {hook_add_180(8):.1f} mm  (expected 50.0 mm)")
    print(f"   HPB300 d=10 180deg hook: {hook_add_180(10):.1f} mm  (expected 62.5 mm)")
    print(f"   stirrup d=8  135deg hook: {hook_add_135_stirrup(8):.1f} mm  (expected 95.2 mm)")
    print(f"   stirrup d=10 135deg hook: {hook_add_135_stirrup(10):.1f} mm  (expected 119.0 mm)")

    # 保护层
    print("\n[3] min cover thickness (class I environment):")
    for t in ['slab', 'beam', 'column', 'wall', 'foundation']:
        print(f"   {t}: {cover_min(t)} mm")

    # 锚固长度
    print("\n[4] anchor length (C30, HRB400):")
    for d in [12, 14, 16, 18, 20, 22, 25]:
        lab = calc_anchor_length(d, 'C30', 'HRB400')
        print(f"   d={d}: lab = {lab} mm  (approx {lab//d}d)")

    # 搭接长度
    print("\n[5] lap length (lab=700mm, 50% lapped):")
    ll = calc_lap_length(700, 0.5)
    print(f"   ll = {ll} mm  (expected 980 mm)")

    print("\n" + "=" * 50)
    print("自检完成")
