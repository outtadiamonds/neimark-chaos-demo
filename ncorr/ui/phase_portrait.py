"""Фазовая плоскость (x, v): раскручивающаяся спираль со скачками вниз при ударах.

Показывает, откуда берутся числа y_n: это скорости в точках, где траектория
пересекает ось x = 0. Движущаяся точка соответствует курсору на графике процесса.
"""
import math

import pygame

from .. import theme
from ..i18n import t
from ..physics import neimark as nm
from .plot import dashed_polyline
from .widgets import Widget, draw_text

SAMPLES = 28  # точек на полупериод
TRAIL = 5     # сколько прошлых полупериодов оставлять на экране


class PhasePortrait(Widget):
    def __init__(self, font_size=13):
        super().__init__()
        self.font_size = font_size
        self.params = None
        self.ys = []
        self.unit = []
        self.xmax = self.vmax = 1.0

    def layout(self, rect):
        self.rect = pygame.Rect(rect)

    def set_data(self, params, ys):
        self.params = params
        self.ys = ys
        d = params.delta
        # форма полупериода при единичной начальной скорости: x = e^{du} sin u, v = f(u)
        self.unit = []
        for j in range(SAMPLES + 1):
            u = math.pi * j / SAMPLES
            self.unit.append((math.exp(d * u) * math.sin(u), nm.shape(u, d)))
        top = max(abs(params.lower), nm.A)
        self.xmax = 1.08 * top * max(x for x, _ in self.unit)
        self.vmax = 1.08 * params.gamma * nm.A

    def _pt(self, x, v):
        r = self.rect
        return (r.centerx + x / self.xmax * r.width / 2, r.centery - v / self.vmax * r.height / 2)

    def draw(self, surf, pos, start):
        """pos — положение курсора в полупериодах (дробное), start — с какого номера рисовать."""
        if not self.visible or self.params is None:
            return
        r = self.rect
        fs = self.font_size
        pygame.draw.line(surf, theme.AXIS, (r.x, r.centery), (r.right, r.centery))
        pygame.draw.line(surf, theme.AXIS, (r.centerx, r.y), (r.centerx, r.bottom))
        draw_text(surf, t("g_x"), (r.right - 2, r.centery + 2), fs, theme.MUTED, anchor="topright")
        draw_text(surf, t("g_v"), (r.centerx + 4, r.y), fs, theme.MUTED)
        ax, ay = self._pt(0, nm.A)
        dashed_polyline(surf, theme.NEGATIVE, [(ax - r.width * 0.12, ay), (ax + r.width * 0.12, ay)],
                        dash=4, gap=3, width=1)
        draw_text(surf, t("g_a"), (ax + r.width * 0.13, ay), fs, theme.NEGATIVE, anchor="midleft")

        n_now = min(int(pos), len(self.ys) - 2)
        frac = pos - n_now
        first = max(start, n_now - TRAIL)
        surf.set_clip(r)
        for n in range(first, n_now + 1):
            y = self.ys[n]
            age = n_now - n
            shade = min(200, 40 + 32 * age)
            color = (shade, shade, shade)
            count = SAMPLES if n < n_now else max(1, int(frac * SAMPLES))
            pts = [self._pt(y * ux, y * uv) for ux, uv in self.unit[:count + 1]]
            if n == n_now:
                u = frac * math.pi
                d = self.params.delta
                pts.append(self._pt(y * math.exp(d * u) * math.sin(u), y * nm.shape(u, d)))
            if len(pts) > 1:
                pygame.draw.aalines(surf, color, False, pts)
            if n < n_now:
                z = -self.params.s * y
                if z >= nm.A:  # удар: вертикальный скачок вниз на оси x = 0
                    pygame.draw.line(surf, theme.NEGATIVE, self._pt(0, z), self._pt(0, self.ys[n + 1]), 2)
        for n in range(first, n_now + 1):
            pygame.draw.circle(surf, theme.SHIFTED, self._pt(0, self.ys[n]), 3)
        pygame.draw.circle(surf, theme.CURSOR, pts[-1], 5)
        surf.set_clip(None)
