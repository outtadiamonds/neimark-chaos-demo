"""Плоскость параметров (h/a, γ) с областью хаоса (рис. 4 статьи 1993 г.).

В программе отмечены только марковские точки H и E; с full=True рисуются ещё линии и точки A–G (рис. 3 теории).
"""
import math

import pygame

from .. import config, theme
from ..i18n import t
from ..physics import neimark as nm
from .plot import Axes, dashed_polyline
from .widgets import Widget, draw_text

GAMMA_MIN = GAMMA_MAX = 0.0  # пределы γ из assets/config.json (раздел "demo"), см. refresh()


def refresh():
    global GAMMA_MIN, GAMMA_MAX
    GAMMA_MIN, GAMMA_MAX = config.demo.gamma_min, config.demo.gamma_max


refresh()


def clamp(gamma, h):
    gamma = min(max(gamma, GAMMA_MIN), GAMMA_MAX)
    lo, hi = nm.Params(gamma, 0).h_range()
    return gamma, min(max(h, lo), hi)


class ParamPlane(Widget):
    def __init__(self, on_change, font_size=13, full=False):
        super().__init__()
        self.full = full  # True — с линиями GD, HC, DE и точками A–G, как на рис. 3 теории
        self.on_change = on_change  # (gamma, h, final)
        self.font_size = font_size
        self.gamma, self.h = nm.PRESETS["H"].gamma, nm.PRESETS["H"].h
        self.axes = None
        self.dragging = False

    def layout(self, rect):
        self.rect = pygame.Rect(rect)
        pad_l, pad_b = int(self.font_size * 2.2), int(self.font_size * 1.8)
        inner = pygame.Rect(self.rect.x + pad_l, self.rect.y + 4, self.rect.width - pad_l - 6,
                            self.rect.height - pad_b - 4)
        self.axes = Axes(inner, (0.0, 3.25), (1.0, 4.25))

    def _pick(self, pos, final):
        g = self.axes.y0 + (self.axes.rect.bottom - pos[1]) / self.axes.rect.height * (self.axes.y1 - self.axes.y0)
        h = self.axes.data_x(pos[0])
        self.gamma, self.h = clamp(g, h)
        self.on_change(self.gamma, self.h, final)

    def handle(self, event):
        if not self.visible or self.axes is None:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.axes.rect.collidepoint(event.pos):
            self.dragging = True
            self._pick(event.pos, False)
            return True
        if event.type == pygame.MOUSEMOTION and self.dragging:
            self._pick(event.pos, False)
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            self._pick(event.pos, True)
            return True
        return False

    def draw(self, surf):
        if not self.visible or self.axes is None:
            return
        ax = self.axes
        fs = self.font_size
        gs = [1.0 + 3.0 * i / 60 for i in range(61)]
        region = [ax.point(g - 1.0, g) for g in gs] + [ax.point(1.0 + math.sqrt(g), g) for g in reversed(gs)]
        pygame.draw.polygon(surf, theme.REGION, region)
        # нормальный режим h < a — бежевая часть области слева от h/a = 1
        pygame.draw.polygon(surf, theme.REGION_NORMAL, [ax.point(0, 1), ax.point(1, 2), ax.point(1, 1)])
        pygame.draw.lines(surf, theme.AXIS, True, region, 1)
        ax.frame(surf, fs - 1, xticks=3, yticks=3, zero=False, yfmt=lambda v: f"{v:g}", xfmt=lambda v: f"{v:g}")
        draw_text(surf, t("g_gamma"), (ax.rect.x + 5, ax.rect.y - 2), fs + 2, theme.FG, bold=True)
        draw_text(surf, t("g_ha"), (ax.rect.right, ax.rect.bottom - 3), fs, theme.FG, anchor="bottomright", bold=True)

        if self.full:  # рисунок теории; в программе отмечены только марковские точки H и E
            self._draw_lines_and_points(surf, ax, fs)
        offsets = {"H": ("bottomright", (-5, -1)), "E": ("midleft", (7, 0))}
        for name, p in nm.PRESETS.items():
            pt = ax.point(p.h, p.gamma)
            pygame.draw.circle(surf, theme.FG, pt, 4)
            anchor, (dx, dy) = offsets[name]
            draw_text(surf, name, (pt[0] + dx, pt[1] + dy), fs, theme.FG, anchor=anchor, bold=True)
        pt = ax.point(self.h, self.gamma)
        pygame.draw.circle(surf, theme.SHIFTED, pt, 7, 2)
        pygame.draw.circle(surf, theme.SHIFTED, pt, 2)

    def _draw_lines_and_points(self, surf, ax, fs):
        """Линии и точки рис. 4 статьи: GD (h/a = 1), HC (h/a = 1 + 1/√γ), DE (h/a = γ), A, B, C, D, G."""
        golden2 = nm.GOLDEN ** 2
        lines = (
            [ax.point(1, 1), ax.point(1, 2)],
            [ax.point(1 + 1 / math.sqrt(1 + (golden2 - 1) * i / 20), 1 + (golden2 - 1) * i / 20) for i in range(21)],
            [ax.point(1, 1), ax.point(golden2, golden2)],
        )
        for pts in lines:
            dashed_polyline(surf, theme.MUTED, pts, dash=4, gap=3, width=1)
        marks = (("A", (0, 1), "bottomleft", (3, -2)), ("B", (3, 4), "bottomright", (-4, 0)),
                 ("C", (2, 1), "bottomleft", (4, -1)), ("D", (1, 1), "bottomleft", (3, -1)),
                 ("G", (1, 2), "bottomright", (-4, 0)))
        for name, (x, y), anchor, (dx, dy) in marks:
            px, py = ax.point(x, y)
            pygame.draw.circle(surf, theme.MUTED, (px, py), 2)
            draw_text(surf, name, (px + dx, py + dy), fs, theme.MUTED, anchor=anchor)
