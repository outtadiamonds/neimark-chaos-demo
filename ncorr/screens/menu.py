import pygame

from .. import theme
from ..i18n import t
from ..ui.widgets import Button, draw_text
from .base import Screen, standard_header


class MenuScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.buttons = [
            Button(lambda: t("model"), lambda: app.show("motion")),
            Button(lambda: t("theory"), lambda: app.show("theory")),
            Button(lambda: t("authors"), lambda: app.show("authors")),
            Button(lambda: t("exit"), app.quit),
        ]
        self.widgets = list(self.buttons)

    def layout(self, w, h):
        u = theme.unit(h)
        bw, bh = int(w * 0.26), int(h * 0.065)
        gap = int(h * 0.022)
        y = int(h * 0.41)
        for b in self.buttons:
            b.rect = pygame.Rect((w - bw) // 2, y, bw, bh)
            b.font_size = int(u * 1.5)
            y += bh + gap

    def draw(self, surf):
        w, h = surf.get_size()
        standard_header(surf, w, h)
        super().draw(surf)
        draw_text(surf, t("fullscreen_hint"), (w // 2, h - int(h * 0.03)), theme.unit(h), theme.MUTED,
                  anchor="midbottom")
