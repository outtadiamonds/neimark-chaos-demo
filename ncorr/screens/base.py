import pygame

from .. import resources as res
from .. import theme
from ..i18n import t
from ..ui.widgets import draw_text, fit_text


class Screen:
    def __init__(self, app):
        self.app = app
        self.widgets = []
        self.label_scale = {}  # множители шрифта заголовков разделов из design.json

    def layout(self, w, h):
        pass

    def enter(self):
        pass

    def handle(self, event):
        for wdg in self.widgets:
            if wdg.handle(event):
                return True
        return False

    def update(self, dt):
        pass

    def draw(self, surf):
        for wdg in self.widgets:
            wdg.draw(surf)


def draw_header(surf, w, h, lines):
    """Шапка как в других демонстрациях: эмблема МГУ слева, логотип ВМК справа, текст по центру.
    lines: [(text, size, bold, serif)]. Возвращает y под шапкой."""
    logo = int(min(w * 0.09, h * 0.15))
    top = int(h * 0.05)
    for name, x in (("msu_logo.png", int(w * 0.05)), ("cmc_logo.png", w - int(w * 0.05) - logo)):
        img = res.image("img", name)
        if img:
            k = logo / max(img.get_size())
            size = (round(img.get_width() * k), round(img.get_height() * k))
            surf.blit(pygame.transform.smoothscale(img, size), (x + (logo - size[0]) // 2, top + (logo - size[1]) // 2))
    y = top
    max_w = w - 2 * (int(w * 0.05) + logo) - 40
    for text, size, bold, serif in lines:
        size = fit_text(text, size, max_w, bold=bold, serif=serif)
        rect = draw_text(surf, text, (w // 2, y), size, theme.FG, anchor="midtop", bold=bold, serif=serif)
        y = rect.bottom + int(size * 0.45)
    return max(y, top + logo)


def standard_header(surf, w, h, with_title=True):
    u = theme.unit(h)
    lines = [(t("msu"), int(u * 1.45), False, True), (t("faculty"), int(u * 1.45), False, True)]
    if with_title:
        lines += [(t("course"), int(u * 1.15), False, True),
                  (t("title1"), int(u * 2.3), True, True),
                  (t("title2"), int(u * 2.3), True, True)]
    return draw_header(surf, w, h, lines)
