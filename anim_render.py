"""
anim_render.py — 전장 애니메이션 프레임 렌더러
ProcessPoolExecutor 서브프로세스용. PyQt6 미사용, matplotlib Agg 백엔드만 사용.
launcher.py에서 직접 임포트하여 FrameRenderWorker가 제출한다.
"""

import io
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as _plt
from matplotlib.figure import Figure
import numpy as np


def _render_anim_frame(args):
    """
    전장 프레임을 PNG bytes로 렌더링.
    args = (idx, t, enemy_ships, friendly_ships, missiles, events,
            display_range, show_labels, show_alt_lines)
    returns (idx, png_bytes: bytes)
    """
    (idx, t, enemy_ships, friendly_ships, missiles, events,
     R, show_labels, show_alt_lines) = args

    _ISO_COS   = math.cos(math.radians(30))
    _ISO_SIN   = math.sin(math.radians(30))
    _ALT_SCALE = 0.50
    _MAX_ALT   = 300.0   # DF-26 등 탄도미사일 최대 고도 반영 (기존 200km → 300km)
    _ENT_CFG   = {
        'friendly': ('^', 140, '#2ecc71',  8),
        'aircraft': ('*', 170, '#ff6b6b',  7),
        'ship':     ('s',  90, '#ff8c8c',  7),
        'sub':      ('D',  75, '#e74c3c',  7),
        'em_bm':   ('^',  55, '#ff2222',  9),
        'em_cm':   ('o',  30, '#ff8888',  9),
        'sam':      ('^',  30, '#55ff99', 10),
        'fstk':     ('o',  30, '#55aaff', 10),
        'esam':     ('v',  22, '#e67e22',  9),
    }

    def iso(xk, yk, ak=0.0):
        ak_c = min(ak, _MAX_ALT)
        return (xk - yk) * _ISO_COS, (xk + yk) * _ISO_SIN + ak_c * _ALT_SCALE

    fig = Figure(figsize=(10, 7), facecolor='#0d1117')
    ax  = fig.add_axes([0.01, 0.01, 0.98, 0.98], facecolor='#0d1117')
    ax.set_aspect('equal')
    ax.axis('off')

    km = lambda v: v / 1000.0

    # ── 뷰 범위 (격자보다 먼저 계산) ─────────────────────────────────────
    cx     = R * _ISO_COS
    cy_gnd = R * _ISO_SIN
    x_span = cx * 1.10
    y_bot  = -cy_gnd * 1.05   # 남쪽 적 하단 잘림 수정 (0.40 → 1.05)
    y_top  = cy_gnd + _MAX_ALT * _ALT_SCALE * 0.60
    ax.set_xlim(-x_span, x_span)
    ax.set_ylim(y_bot, y_top)

    # ── 격자 ─────────────────────────────────────────────────────────────
    step  = max(50, int(R / 5) // 10 * 10)
    r_int = int(R) + step
    for v in range(-r_int, r_int + step, step):
        x1, y1 = iso(-R, v); x2, y2 = iso(R, v)
        ax.plot([x1, x2], [y1, y2], color='#0c2640', lw=0.55, zorder=1)
        x1, y1 = iso(v, -R); x2, y2 = iso(v, R)
        ax.plot([x1, x2], [y1, y2], color='#0c2640', lw=0.55, zorder=1)
    for ring_r in [r for r in [100, 200, 300, 400, 500, 700] if r < R * 1.05]:
        theta = np.linspace(0, 2 * np.pi, 80)
        rxs   = ring_r * np.cos(theta); rys = ring_r * np.sin(theta)
        ax.plot([(x - y) * _ISO_COS for x, y in zip(rxs, rys)],
                [(x + y) * _ISO_SIN for x, y in zip(rxs, rys)],
                color='#152e48', lw=0.85, ls='--', zorder=1)
        lx, ly = iso(ring_r * 0.72, ring_r * -0.72)
        ax.text(lx, ly, f'{ring_r}km', color='#2a4e72', fontsize=7,
                va='center', zorder=2)

    # ── 적 위협 ──────────────────────────────────────────────────────────
    for item in enemy_ships:
        euid, epname, ex, ey, ealive, ehp = item[:6]
        ealt = item[6] if len(item) > 6 else 0.0
        xk, yk, ak = km(ex), km(ey), km(ealt)
        gx, gy = iso(xk, yk, 0); px, py = iso(xk, yk, ak)
        if ak > 0.5 and show_alt_lines:
            ax.plot([gx, px], [gy, py], color='#ff6b6b', lw=0.9, alpha=0.40, zorder=5)
            ax.scatter([gx], [gy], s=10, c='#ff4444', marker='o',
                       alpha=0.22, zorder=5, edgecolors='none')
        key = 'sub' if ak < -0.02 else ('aircraft' if ak > 0.5 else 'ship')
        mk, sz, col, zo = _ENT_CFG[key]
        ax.scatter([px], [py], s=sz, c=col, marker=mk,
                   edgecolors='#ff0000' if not ealive else 'none',
                   linewidths=2.0 if not ealive else 0, zorder=zo)
        if show_labels and ealive:
            ax.text(px + R * 0.02, py + R * 0.015, str(epname)[:10],
                    color='#ffaaaa', fontsize=7, ha='left', va='bottom', zorder=12)

    # ── 아군 함정 ────────────────────────────────────────────────────────
    for item in friendly_ships:
        sname, sx_, sy_, salive, shp = item[:5]
        px, py = iso(km(sx_), km(sy_), 0)
        mk, sz, col, zo = _ENT_CFG['friendly']
        ax.scatter([px], [py], s=sz, c=col, marker=mk,
                   edgecolors='#ff0000' if not salive else 'none',
                   linewidths=2.5 if not salive else 0, zorder=zo)
        if show_labels:
            ax.text(px + R * 0.02, py + R * 0.015, str(sname)[:9],
                    color='#aaffcc', fontsize=7, ha='left', va='bottom', zorder=12)

    # ── 미사일 ───────────────────────────────────────────────────────────
    for item in missiles:
        muid, mx_, my_, mtype, mname = item[:5]
        malt = item[5] if len(item) > 5 else 0.0
        xk, yk, ak = km(mx_), km(my_), km(malt)
        gx, gy = iso(xk, yk, 0); px, py = iso(xk, yk, ak)
        if mtype == 'enemy_strike':
            key = 'em_bm' if malt > 5000 else 'em_cm'
        elif mtype == 'friendly_sam':    key = 'sam'
        elif mtype == 'friendly_strike': key = 'fstk'
        elif mtype == 'enemy_sam':       key = 'esam'
        else: continue
        mk, sz, col, zo = _ENT_CFG[key]
        if ak > 0.5 and show_alt_lines:
            ax.plot([gx, px], [gy, py], color=col, lw=0.7, alpha=0.38, zorder=6)
        ax.scatter([px], [py], s=sz, c=col, marker=mk, edgecolors='none', zorder=zo)
        if show_labels and mname:
            lbl_col = ('#aaffaa' if mtype == 'friendly_sam' else
                       '#aaaaff' if mtype == 'friendly_strike' else '#ffaaaa')
            ax.text(px + R * 0.015, py + R * 0.01, str(mname)[:8],
                    color=lbl_col, fontsize=6, ha='left', va='bottom', zorder=12)

    # ── 타이틀 ───────────────────────────────────────────────────────────
    ax.text(0, y_top * 0.975, f"전장 상황   t = {t:.0f}s",
            color='#dde8ff', fontsize=11, fontweight='bold',
            ha='center', va='top', zorder=15)

    # ── 범례 ─────────────────────────────────────────────────────────────
    legend_items = [
        ('Friendly Ship', '#2ecc71'), ('Enemy Aircraft', '#ff6b6b'),
        ('Enemy Ship',    '#ff8c8c'), ('Enemy Sub',      '#e74c3c'),
        ('Friendly SAM',  '#55ff99'), ('Enemy Missile',  '#ff2222'),
        ('Enemy BM',      '#ff4444'),
    ]
    lx_leg = cx * 0.90
    ly_leg = y_top * 0.95
    row_h  = (y_top - y_bot) * 0.055
    for i, (lbl, col) in enumerate(legend_items):
        ax.text(lx_leg, ly_leg - i * row_h, lbl,
                color=col, fontsize=7, ha='center', va='top', zorder=15)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120, facecolor='#0d1117')
    buf.seek(0)
    data = buf.read()
    fig.clf()
    del fig
    return idx, data


def _warmup_task(_):
    """글로벌 풀 워커 예열용 더미 태스크 (subprocess 안전, PyQt6 미사용)."""
    try:
        import engine_v7  # noqa — import로 워커 내 캐시 선점
    except Exception:
        pass
    return True

