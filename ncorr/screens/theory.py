"""Экран «Теория»: страницы, свёрстанные заранее (assets/theory/<язык>/page-*.png), с прокруткой."""
import os

import pygame

from .. import resources as res
from .. import theme
from ..i18n import lang, t
from ..ui.widgets import Button, draw_text
from .base import Screen


class TheoryScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.back = Button(lambda: t("back"), lambda: app.show("menu"))
        self.widgets = [self.back]
        self.scroll = 0.0
        self._cache_key = None
        self._pages = []
        self._drag = None

    def enter(self):
        self.scroll = 0.0

    def layout(self, w, h):
        self.back.rect = pygame.Rect(w - int(w * 0.18), h - int(h * 0.1), int(w * 0.14), int(h * 0.06))
        self.back.font_size = int(theme.unit(h) * 1.4)
        self._cache_key = None

    def _pages_for(self, w, h):
        key = (lang(), w, h)
        if key != self._cache_key:
            folder = res.path("theory", lang())
            names = sorted(f for f in os.listdir(folder) if f.endswith(".png")) if os.path.isdir(folder) else []
            width = int(min(w * 0.62, h * 1.05))
            self._pages = []
            for name in names:
                img = res.image("theory", lang(), name)
                scale = width / img.get_width()
                self._pages.append(pygame.transform.smoothscale(img, (width, int(img.get_height() * scale))))
            self._cache_key = key
        return self._pages

    def _content_height(self, h):
        return sum(p.get_height() for p in self._pages) + 12 * len(self._pages)

    def _clamp(self, h):
        self.scroll = min(max(self.scroll, 0.0), max(0.0, self._content_height(h) - h + 20))

    def handle(self, event):
        if super().handle(event):
            return True
        h = self.app.screen.get_height()
        if event.type == pygame.MOUSEWHEEL:
            self.scroll -= event.y * h * 0.08
        elif event.type == pygame.KEYDOWN:
            step = {pygame.K_DOWN: 0.08, pygame.K_UP: -0.08, pygame.K_PAGEDOWN: 0.9, pygame.K_PAGEUP: -0.9,
                    pygame.K_SPACE: 0.9}.get(event.key)
            if step is None:
                return False
            self.scroll += step * h
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._drag = (event.pos[1], self.scroll)
        elif event.type == pygame.MOUSEMOTION and self._drag:
            self.scroll = self._drag[1] - (event.pos[1] - self._drag[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._drag = None
        else:
            return False
        self._clamp(h)
        return True

    def draw(self, surf):
        w, h = surf.get_size()
        pages = self._pages_for(w, h)
        if not pages:
            draw_text(surf, t("theory_missing"), (w // 2, h // 2), theme.unit(h) * 2, theme.MUTED, anchor="center")
        self._clamp(h)
        y = 10 - self.scroll
        for page in pages:
            if y + page.get_height() > 0 and y < h:
                x = (w - page.get_width()) // 2
                surf.blit(page, (x, y))
                pygame.draw.rect(surf, theme.BORDER, (x - 1, y - 1, page.get_width() + 2, page.get_height() + 2), 1)
            y += page.get_height() + 12
        total = self._content_height(h)
        if total > h:
            bar_h = max(30, h * h / total)
            bar_y = (h - bar_h) * self.scroll / (total - h + 20)
            pygame.draw.rect(surf, theme.BORDER, (w - 10, bar_y, 6, bar_h), border_radius=3)
        super().draw(surf)
