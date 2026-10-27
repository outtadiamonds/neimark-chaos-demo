"""Простые виджеты: кнопка, переключатель, ползунок. Надписи задаются функциями, чтобы
при смене языка всё перерисовывалось без пересоздания виджетов."""
import math

import pygame

from .. import i18n
from .. import resources as res
from .. import theme


# Режим разработчика включает запись: какие надписи где нарисованы в этом кадре (для правки двойным щелчком)
DRAWN = None


def remember_text(rect, text):
    if DRAWN is not None and text:
        DRAWN.append((rect, text, i18n.traced_key(text)))


def draw_text(surf, text, pos, size, color=None, anchor="topleft", bold=False, serif=False, italic=False):
    color = theme.FG if color is None else color  # цвет по умолчанию берётся при рисовании: его можно поменять
    img = res.font(size, bold=bold, serif=serif, italic=italic).render(text, True, color)
    rect = img.get_rect(**{anchor: pos})
    surf.blit(img, rect)
    remember_text(rect, text)
    return rect


def fit_text(text, size, max_width, **kw):
    """Наибольший размер шрифта <= size, при котором текст влезает в max_width."""
    while size > 9 and res.font(size, **kw).size(text)[0] > max_width:
        size -= 1
    return size


class Widget:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.visible = True

    def handle(self, event):
        return False

    def draw(self, surf):
        pass


class Button(Widget):
    def __init__(self, label, on_click, font_size=16):
        super().__init__()
        self.label = label  # функция без аргументов, возвращающая текст
        self.on_click = on_click
        self.font_size = font_size
        self.enabled = True
        self.selected = False
        self._pressed = False

    def handle(self, event):
        if not (self.visible and self.enabled):
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self._pressed = True
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self._pressed:
            self._pressed = False
            if self.rect.collidepoint(event.pos):
                self.on_click()
            return True
        return False

    def draw(self, surf):
        if not self.visible:
            return
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        if self.selected:
            bg, fg = theme.SELECTED, theme.SELECTED_TEXT
        else:
            bg = theme.BUTTON_PRESSED if self._pressed else theme.BUTTON_HOVER if hover and self.enabled else theme.BUTTON
            fg = theme.FG if self.enabled else theme.DISABLED_TEXT
        radius = max(3, self.rect.height // 6)
        pygame.draw.rect(surf, bg, self.rect, border_radius=radius)
        text = self.label()
        size = fit_text(text, self.font_size, self.rect.width - 8)
        draw_text(surf, text, self.rect.center, size, fg, anchor="center")


class Segmented(Widget):
    """Ряд взаимоисключающих кнопок."""

    def __init__(self, options, value, on_change, font_size=16):
        super().__init__()
        self.options = options  # [(value, label_fn)]
        self.value = value
        self.on_change = on_change
        self.font_size = font_size
        self.buttons = [Button(label, self._chooser(v), font_size) for v, label in options]

    def _chooser(self, v):
        def choose():
            if v != self.value:
                self.value = v
                self.on_change(v)
        return choose

    def layout(self, rect, gap=4):
        self.rect = pygame.Rect(rect)
        n = len(self.buttons)
        w = (self.rect.width - gap * (n - 1)) / n
        for i, b in enumerate(self.buttons):
            b.rect = pygame.Rect(round(self.rect.x + i * (w + gap)), self.rect.y, round(w), self.rect.height)
            b.font_size = self.font_size

    def handle(self, event):
        return any(b.handle(event) for b in self.buttons)

    def draw(self, surf):
        for (v, _), b in zip(self.options, self.buttons):
            b.selected = v == self.value
            b.draw(surf)


class Slider(Widget):
    """Ползунок. on_change(value, final): final=True, когда кнопку мыши отпустили."""

    def __init__(self, label, vmin, vmax, value, on_change, fmt=lambda v: f"{v:.3g}", log=False, font_size=15):
        super().__init__()
        self.label = label
        self.vmin, self.vmax = vmin, vmax
        self.value = value
        self.on_change = on_change
        self.fmt = fmt
        self.log = log
        self.font_size = font_size
        self.dragging = False
        self.track = pygame.Rect(0, 0, 0, 0)

    def set_range(self, vmin, vmax):
        self.vmin, self.vmax = vmin, vmax
        self.value = min(max(self.value, vmin), vmax)

    def _to_frac(self, v):
        if self.vmax <= self.vmin:
            return 0.0
        if self.log:
            return (math.log(v) - math.log(self.vmin)) / (math.log(self.vmax) - math.log(self.vmin))
        return (v - self.vmin) / (self.vmax - self.vmin)

    def _from_frac(self, f):
        f = min(max(f, 0.0), 1.0)
        if self.log:
            return math.exp(math.log(self.vmin) + f * (math.log(self.vmax) - math.log(self.vmin)))
        return self.vmin + f * (self.vmax - self.vmin)

    def layout(self, rect):
        self.rect = pygame.Rect(rect)
        label_h = int(self.font_size * 1.35)
        self.track = pygame.Rect(self.rect.x + 8, self.rect.y + label_h + (self.rect.height - label_h) // 2 - 2,
                                 self.rect.width - 16, 4)

    def _set_from_mouse(self, x, final):
        self.value = self._from_frac((x - self.track.x) / max(1, self.track.width))
        self.on_change(self.value, final)

    def handle(self, event):
        if not self.visible:
            return False
        hit = self.track.inflate(16, 22)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and hit.collidepoint(event.pos):
            self.dragging = True
            self._set_from_mouse(event.pos[0], False)
            return True
        if event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from_mouse(event.pos[0], False)
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            self._set_from_mouse(event.pos[0], True)
            return True
        return False

    def draw(self, surf):
        if not self.visible:
            return
        draw_text(surf, self.label(), (self.rect.x, self.rect.y), self.font_size, theme.FG)
        draw_text(surf, self.fmt(self.value), (self.rect.right, self.rect.y), self.font_size, theme.FG,
                  anchor="topright", bold=True)
        pygame.draw.rect(surf, theme.BORDER, self.track, border_radius=2)
        x = self.track.x + self._to_frac(self.value) * self.track.width
        filled = pygame.Rect(self.track.x, self.track.y, x - self.track.x, self.track.height)
        pygame.draw.rect(surf, theme.SELECTED, filled, border_radius=2)
        r = max(6, self.font_size // 2)
        pygame.draw.circle(surf, theme.BG, (round(x), self.track.centery), r)
        pygame.draw.circle(surf, theme.SELECTED, (round(x), self.track.centery), r, 2)
