"""Минимальные оси для графиков: пересчёт координат, нулевая линия, подписи делений."""
import math

import pygame

from .. import resources as res
from .. import theme
from .widgets import draw_text, remember_text


def label_box(surf, rect, pad=3):
    """Полупрозрачная белая подложка под надпись поверх графика."""
    box = pygame.Surface((rect.width + 2 * pad, rect.height + 2 * pad), pygame.SRCALPHA)
    box.fill(theme.BG + (215,))
    surf.blit(box, (rect.x - pad, rect.y - pad))


def boxed_text(surf, text, font, color, **anchor):
    """Надпись на полупрозрачной белой подложке поверх графика; anchor — например bottomleft=(x, y)."""
    img = font.render(text, True, color)
    rect = img.get_rect(**anchor)
    label_box(surf, rect)
    surf.blit(img, rect)
    remember_text(rect, text)
    return rect


def nice_step(span, target):
    raw = span / max(1, target)
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            return m * mag
    return 10 * mag


class Axes:
    def __init__(self, rect, xlim, ylim):
        self.rect = pygame.Rect(rect)
        self.x0, self.x1 = xlim
        self.y0, self.y1 = ylim

    def px(self, x):
        return self.rect.x + (x - self.x0) / (self.x1 - self.x0) * self.rect.width

    def py(self, y):
        return self.rect.bottom - (y - self.y0) / (self.y1 - self.y0) * self.rect.height

    def point(self, x, y):
        return self.px(x), self.py(y)

    def data_x(self, px):
        return self.x0 + (px - self.rect.x) / self.rect.width * (self.x1 - self.x0)

    def clip_y(self, y):
        return min(max(y, self.y0), self.y1)

    def frame(self, surf, font_size, xticks=6, yticks=4, xlabel=None, xfmt=None, yfmt=None, zero=True):
        r = self.rect
        pygame.draw.line(surf, theme.AXIS, r.topleft, r.bottomleft)
        # горизонтальные деления
        ys = nice_step(self.y1 - self.y0, yticks)
        y = math.ceil(self.y0 / ys) * ys
        while y <= self.y1 + 1e-9:
            py = round(self.py(y))
            pygame.draw.line(surf, theme.GRID, (r.x + 1, py), (r.right, py))
            label = yfmt(y) if yfmt else theme.num(y, 1 if ys < 1 else 0)
            draw_text(surf, label, (r.x - 5, py), font_size, theme.MUTED, anchor="midright")
            y += ys
        if zero and self.y0 < 0 < self.y1:
            pygame.draw.line(surf, theme.AXIS, (r.x, round(self.py(0))), (r.right, round(self.py(0))))
        # вертикальные деления; подпись оси справа, метки под ней не рисуются
        label_rect = None
        if xlabel:
            label_rect = draw_text(surf, xlabel, (r.right, r.bottom + 5), font_size, theme.MUTED, anchor="topright")
        xs = nice_step(self.x1 - self.x0, xticks)
        x = math.ceil(self.x0 / xs) * xs
        while x <= self.x1 + 1e-9:
            px = round(self.px(x))
            pygame.draw.line(surf, theme.AXIS, (px, r.bottom), (px, r.bottom + 4))
            label = xfmt(x) if xfmt else (f"{x:g}" if abs(x) >= 1e-9 else "0")
            img = res.font(font_size).render(label, True, theme.MUTED)
            rect = img.get_rect(midtop=(px, r.bottom + 5))
            if label_rect is None or not rect.inflate(8, 0).colliderect(label_rect):
                surf.blit(img, rect)
            x += xs
        pygame.draw.line(surf, theme.AXIS, r.bottomleft, r.bottomright)


def dashed_polyline(surf, color, points, dash=7, gap=5, width=2):
    """Штриховая ломаная: штрихи идут непрерывно по длине всей линии."""
    period = dash + gap
    pos = 0.0
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        if seg == 0:
            continue
        t = 0.0
        while t < seg:
            phase = (pos + t) % period
            if phase < dash:
                run = min(dash - phase, seg - t)
                a = t / seg
                b = (t + run) / seg
                pygame.draw.line(surf, color, (x0 + (x1 - x0) * a, y0 + (y1 - y0) * a),
                                 (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b), width)
                t += run
            else:
                t += period - phase
        pos += seg
