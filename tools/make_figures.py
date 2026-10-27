"""Рисунки для теории (theory/fig_*.png): фазовая плоскость, отображение за полпериода,
плоскость параметров. Подписи только символьные, поэтому рисунки общие для обоих языков.

python tools/make_figures.py, затем python tools/build_theory.py
"""
import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame  # noqa: E402

from ncorr import resources as res, theme  # noqa: E402
from ncorr.physics import neimark as nm  # noqa: E402
from ncorr.ui.param_plane import ParamPlane  # noqa: E402
from ncorr.ui.plot import dashed_polyline  # noqa: E402
from ncorr.ui.widgets import draw_text  # noqa: E402

P = nm.PRESETS["H"]
FS = 30


def canvas(w, h):
    s = pygame.Surface((w, h))
    s.fill(theme.BG)
    return s


def save(surf, name):
    path = os.path.join(ROOT, "theory", name)
    pygame.image.save(surf, path)
    print(path)


def fig_phase():
    """Раскручивающаяся спираль с двумя ударами; точки на оси x = 0 — значения y_n."""
    w, h = 1000, 900
    s = canvas(w, h)
    cx, cy, sx, sy = 520, 520, 190, 190
    pt = lambda x, v: (cx + x * sx, cy - v * sy)  # noqa: E731
    pygame.draw.line(s, theme.AXIS, (40, cy), (w - 40, cy), 2)
    pygame.draw.line(s, theme.AXIS, (cx, 30), (cx, h - 30), 2)
    draw_text(s, "x", (w - 45, cy + 8), FS, theme.MUTED, anchor="topright", italic=True)
    draw_text(s, "v", (cx + 12, 30), FS, theme.MUTED, italic=True)
    ax, ay = pt(0, nm.A)
    dashed_polyline(s, theme.NEGATIVE, [(ax - 150, ay), (ax + 150, ay)], dash=10, gap=7, width=2)
    draw_text(s, "a", (ax + 160, ay), FS, theme.NEGATIVE, anchor="midleft", italic=True)

    d = P.delta
    y = -0.7  # старт подобран так, чтобы первый удар разворачивал скорость, а второй нет
    ys = [y]
    kicks = 0
    for n in range(4):
        pts = []
        for j in range(61):
            u = math.pi * j / 60
            pts.append(pt(y * math.exp(d * u) * math.sin(u), y * nm.shape(u, d)))
        pygame.draw.lines(s, theme.PROCESS, False, pts, 3)
        z = -P.s * y
        if z >= nm.A:
            off = -9 if kicks == 0 else 9  # два удара рисуем по разные стороны оси, чтобы не слились
            (x1, y1), (x2, y2) = pt(0, z), pt(0, z - P.h)
            pygame.draw.line(s, theme.NEGATIVE, (x1 + off, y1), (x2 + off, y2), 6)
            pygame.draw.polygon(s, theme.NEGATIVE, [(x2 + off, y2 + 4), (x2 + off - 11, y2 - 16), (x2 + off + 11, y2 - 16)])
            draw_text(s, "h", (x1 + off + (16 if off > 0 else -16), (y1 + y2) / 2), FS, theme.NEGATIVE,
                      anchor="midleft" if off > 0 else "midright", italic=True)
            z -= P.h
            kicks += 1
        y = z
        ys.append(y)
    sub = "₁₂₃₄₅"
    sides = ["midright", "midleft", "midright", "midright", "midleft"]
    for n, y in enumerate(ys):
        px, py = pt(0, y)
        pygame.draw.circle(s, theme.SHIFTED, (px, py), 9)
        dx = -26 if sides[n] == "midright" else 26
        draw_text(s, "y" + sub[n], (px + dx, py), FS - 2, theme.SHIFTED, anchor=sides[n], bold=True)
    save(s, "fig_phase.png")


def fig_map():
    """График y_{n+1} = T(y_n) в точке H."""
    w, h = 1000, 900
    s = canvas(w, h)
    x0, x1, y0, y1 = -2.0, 1.4, -2.0, 1.4
    px = lambda x: 90 + (x - x0) / (x1 - x0) * (w - 140)   # noqa: E731
    py = lambda y: h - 80 - (y - y0) / (y1 - y0) * (h - 130)  # noqa: E731
    lo, br = P.lower, P.branch
    pygame.draw.rect(s, theme.REGION, (px(lo), py(nm.A), px(nm.A) - px(lo), py(lo) - py(nm.A)))
    pygame.draw.line(s, theme.AXIS, (px(x0), py(0)), (px(x1), py(0)), 2)
    pygame.draw.line(s, theme.AXIS, (px(0), py(y0)), (px(0), py(y1)), 2)
    dashed_polyline(s, theme.MUTED, [(px(br), py(y0)), (px(br), py(y1))], dash=8, gap=6, width=2)
    dashed_polyline(s, theme.NEGATIVE, [(px(x0), py(nm.A)), (px(x1), py(nm.A))], dash=8, gap=6, width=2)
    pygame.draw.line(s, theme.SHIFTED, (px(br), py(nm.A)), (px(nm.A), py(-P.s)), 5)
    pygame.draw.line(s, theme.SHIFTED, (px(lo), py(P.gamma - P.h)), (px(br), py(nm.A - P.h)), 5)
    pygame.draw.circle(s, theme.SHIFTED, (px(br), py(nm.A - P.h)), 9)
    pygame.draw.circle(s, theme.BG, (px(br), py(nm.A)), 9)
    pygame.draw.circle(s, theme.SHIFTED, (px(br), py(nm.A)), 9, 3)
    draw_text(s, "yₙ", (px(x1), py(0) + 8), FS, theme.MUTED, anchor="topright", italic=True)
    draw_text(s, "yₙ₊₁", (px(0) + 12, py(y1)), FS, theme.MUTED, italic=True)
    draw_text(s, "a", (px(x0) + 8, py(nm.A) - 6), FS, theme.NEGATIVE, anchor="bottomleft", italic=True)
    draw_text(s, "y*", (px(br) + 10, py(y0) - 6), FS, theme.MUTED, anchor="bottomleft", italic=True)
    draw_text(s, "−√γ·a", (px(lo), py(lo) + 8), FS - 4, theme.MUTED, anchor="midtop")
    draw_text(s, "a", (px(nm.A), py(lo) + 8), FS - 4, theme.MUTED, anchor="midtop", italic=True)
    draw_text(s, "−√γ·y", (px(0.45), py(-P.s * 0.45) - 10), FS - 4, theme.SHIFTED, anchor="bottomleft")
    draw_text(s, "−√γ·y − h", (px(-1.35), py(P.s * 1.35 - P.h) - 12), FS - 4, theme.SHIFTED, anchor="bottomleft")
    save(s, "fig_map.png")


def fig_plane():
    """Плоскость параметров со всеми линиями рис. 4 статьи."""
    s = canvas(760, 700)
    plane = ParamPlane(lambda *a: None, font_size=24, full=True)
    plane.layout((20, 20, 720, 660))
    plane.gamma, plane.h = P.gamma, P.h
    plane.draw(s)
    save(s, "fig_plane.png")


if __name__ == "__main__":
    pygame.display.init()
    pygame.display.set_mode((16, 16))
    pygame.font.init()
    res.clear_cache()
    fig_phase()
    fig_map()
    fig_plane()
