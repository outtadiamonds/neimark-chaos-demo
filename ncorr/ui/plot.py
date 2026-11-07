"""Минимальные оси для графиков: пересчёт координат, нулевая линия, подписи делений."""
import math

import pygame
import pygame.gfxdraw

from .. import resources as res
from .. import theme
from .widgets import draw_text, remember_text


def stroke_width(surf, role="curve"):
    """Единая шкала толщин для доски: сетка < оси < данные."""
    scale = max(1.0, min(1.5, surf.get_height() / 1200))
    return max(1, round({"grid": 1, "axis": 1.5, "curve": 2}[role] * scale))


def graph_line(surf, color, start, end, width=1):
    role = "grid" if color == theme.GRID else "axis" if color == theme.AXIS else "curve"
    width = stroke_width(surf, role)
    _smooth_segment(surf, color, start, end, width)


def graph_lines(surf, color, closed, points, width=1):
    role = "axis" if color == theme.AXIS else "curve"
    _supersampled_curve(surf, points, [color] * (len(points)-1), stroke_width(surf, role), closed)


def _supersampled_curve(surf, points, colors, width, closed=False):
    """Рисование кривой в утроенном разрешении с последующим сглаженным уменьшением."""
    if len(points) < 2:
        return
    pad = width + 2
    left = math.floor(min(p[0] for p in points)) - pad
    top = math.floor(min(p[1] for p in points)) - pad
    right = math.ceil(max(p[0] for p in points)) + pad
    bottom = math.ceil(max(p[1] for p in points)) + pad
    box = pygame.Rect(left, top, right-left+1, bottom-top+1).clip(surf.get_clip())
    if box.width <= 0 or box.height <= 0:
        return
    scale = 3
    layer = pygame.Surface((box.width*scale, box.height*scale), pygame.SRCALPHA)
    pts = [(round((x-box.x)*scale), round((y-box.y)*scale)) for x,y in points]
    thick = width*scale
    for i, (a,b) in enumerate(zip(pts,pts[1:])):
        color = colors[i]
        pygame.draw.line(layer,color,a,b,thick)
        pygame.draw.circle(layer,color,a,max(1,thick//2))
    pygame.draw.circle(layer,colors[-1],pts[-1],max(1,thick//2))
    if closed:
        pygame.draw.line(layer,colors[-1],pts[-1],pts[0],thick)
    surf.blit(pygame.transform.smoothscale(layer,box.size),box.topleft)


def _smooth_segment(surf, color, a, b, width):
    """Полоса с субпиксельным сглаживанием вместо ступенек pygame.draw.line."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    if length < 1e-8:
        return
    if width <= 1:
        pygame.draw.aaline(surf, color, a, b)
        return
    nx, ny = -dy / length * (width - 1) / 2, dx / length * (width - 1) / 2
    vertices = [(a[0]+nx,a[1]+ny), (b[0]+nx,b[1]+ny),
                (b[0]-nx,b[1]-ny), (a[0]-nx,a[1]-ny)]
    pygame.draw.polygon(surf, color, vertices)
    pygame.draw.aalines(surf, color, True, vertices)


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
        graph_line(surf, theme.AXIS, r.topleft, r.bottomleft)
        # горизонтальные деления
        ys = nice_step(self.y1 - self.y0, yticks)
        y = math.ceil(self.y0 / ys) * ys
        while y <= self.y1 + 1e-9:
            py = round(self.py(y))
            graph_line(surf, theme.GRID, (r.x + 1, py), (r.right, py))
            label = yfmt(y) if yfmt else theme.num(y, 1 if ys < 1 else 0)
            draw_text(surf, label, (r.x - 5, py), font_size, theme.MUTED, anchor="midright")
            y += ys
        if zero and self.y0 < 0 < self.y1:
            graph_line(surf, theme.AXIS, (r.x, round(self.py(0))), (r.right, round(self.py(0))))
        # вертикальные деления; подпись оси справа, метки под ней не рисуются
        label_rect = None
        if xlabel:
            label_rect = draw_text(surf, xlabel, (r.right, r.bottom + 5), font_size, theme.MUTED, anchor="topright")
        xs = nice_step(self.x1 - self.x0, xticks)
        x = math.ceil(self.x0 / xs) * xs
        while x <= self.x1 + 1e-9:
            px = round(self.px(x))
            graph_line(surf, theme.AXIS, (px, r.bottom), (px, r.bottom + 4))
            label = xfmt(x) if xfmt else (f"{x:g}" if abs(x) >= 1e-9 else "0")
            img = res.font(font_size).render(label, True, theme.MUTED)
            rect = img.get_rect(midtop=(px, r.bottom + 5))
            if label_rect is None or not rect.inflate(8, 0).colliderect(label_rect):
                surf.blit(img, rect)
            x += xs
        graph_line(surf, theme.AXIS, r.bottomleft, r.bottomright)


def dashed_polyline(surf, color, points, dash=7, gap=5, width=2):
    """Штриховая ломаная: штрихи идут непрерывно по длине всей линии."""
    scale = max(1.0, surf.get_height() / 900)
    dash, gap = max(1, round(dash * scale)), max(1, round(gap * scale))
    period = dash + gap
    pos = 0.0
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        if seg == 0:
            continue
        t = 0.0
        while t < seg - 1e-8:
            phase = round((pos + t) % period, 7)
            if phase >= period - 1e-7:
                phase = 0.0
            if phase < dash:
                run = min(dash - phase, seg - t)
                a = t / seg
                b = (t + run) / seg
                graph_line(surf, color, (x0 + (x1 - x0) * a, y0 + (y1 - y0) * a),
                                 (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b), width)
                t += run
            else:
                t += period - phase
        pos += seg


def curve_line(surf, color, closed, points):
    """Контрастная кривая для проектора; ширина растёт с высотой окна."""
    if len(points) > 1:
        graph_lines(surf, color, closed, points, stroke_width(surf))


def trail_color(base, age, horizon):
    """Контрастный свежий след; последние 35% времени жизни плавно стираются."""
    fraction = max(0.0, min(1.0, age / max(horizon, 1e-6)))
    fade = 0.55 * min(1.0, fraction / 0.65)
    if fraction > 0.65:
        fade += 0.45 * ((fraction - 0.65) / 0.35)
    return tuple(round(c + (255-c)*fade) for c in base)


def fading_trail(surf, points, ages, base, horizon):
    colors = [trail_color(base, age, horizon) for age in ages[:len(points)-1]]
    _supersampled_curve(surf, points, colors, stroke_width(surf))


def point_marker(surf, color, center, radius, width=0):
    """Увеличенный сглаженный маркер данных, отдельно от толщины кривой."""
    scale = max(1.0, min(1.4, surf.get_height() / 1200))
    r = max(1, round((radius + 2 if radius >= 5 else radius) * scale))
    x, y = round(center[0]), round(center[1])
    pygame.draw.circle(surf, color, (x,y), r, min(r, max(3, width)) if width else 0)
    pygame.gfxdraw.aacircle(surf, x, y, r, color)
