"""Экран «Авторы». Данные берутся из assets/authors.json, фото — из assets/authors/."""
import pygame

from .. import resources as res
from .. import theme
from ..i18n import pick, t
from ..ui.widgets import Button, draw_text, fit_text
from .base import Screen, standard_header


class AuthorsScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        try:
            self.data = res.load_json("authors.json")
        except (OSError, ValueError):
            self.data = {}
        self.back = Button(lambda: t("back"), lambda: app.show("menu"))
        self.widgets = [self.back]

    def layout(self, w, h):
        self.back.rect = pygame.Rect(w - int(w * 0.18), h - int(h * 0.1), int(w * 0.14), int(h * 0.06))
        self.back.font_size = int(theme.unit(h) * 1.4)

    def draw(self, surf):
        w, h = surf.get_size()
        u = theme.unit(h)
        y = standard_header(surf, w, h, with_title=False) + int(h * 0.03)
        draw_text(surf, t("title1") + " " + t("title2"), (w // 2, y), int(u * 1.6), anchor="midtop", bold=True,
                  serif=True)
        y += int(u * 3.2)
        for key in ("lecturer", "supervisor"):
            name = pick(self.data.get(key, {})) or "—"
            draw_text(surf, f"{t(key)}: {name}", (w // 2, y), int(u * 1.4), anchor="midtop", serif=True)
            y += int(u * 2.1)

        people = self.data.get("authors") or [{}, {}]
        y += int(u * 1.2)
        draw_text(surf, t("authors_title"), (w // 2, y), int(u * 1.5), anchor="midtop", bold=True, serif=True)
        y += int(u * 2.6)
        n = len(people)
        name_size = int(u * 1.3)
        photo_h = int(min(h * 0.3, h - y - h * 0.16 - name_size * 2.6))
        photo_w = int(photo_h * 0.78)
        # у каждого автора своя колонка, чтобы подписи не наезжали друг на друга
        col = int(min(max(photo_w + w * 0.05, w * 0.3), w * 0.9 / n))
        x0 = (w - n * col) // 2
        for i, person in enumerate(people):
            cx = x0 + i * col + col // 2
            box = pygame.Rect(cx - photo_w // 2, y, photo_w, photo_h)
            img = res.image("authors", person["photo"]) if person.get("photo") else None
            if img:
                # заполнить рамку без искажения: масштабировать и обрезать лишнее по центру
                k = max(box.width / img.get_width(), box.height / img.get_height())
                scaled = pygame.transform.smoothscale(img, (round(img.get_width() * k), round(img.get_height() * k)))
                crop = pygame.Rect(0, 0, box.width, box.height)
                crop.center = scaled.get_rect().center
                surf.blit(scaled, box, crop)
            else:
                pygame.draw.rect(surf, theme.PANEL, box)
                pygame.draw.rect(surf, theme.BORDER, box, 1)
            name = pick(person.get("name", {})) or f"({t('to_be_added')})"
            color = theme.FG if pick(person.get("name", {})) else theme.MUTED
            max_w = col - 16
            lines = [name]
            if res.font(name_size, serif=True).size(name)[0] > max_w and " " in name:
                lines = name.split(" ", 1)  # «Фамилия» / «Имя Отчество»
            ty = box.bottom + 8
            for line in lines:
                r = draw_text(surf, line, (cx, ty), fit_text(line, name_size, max_w, serif=True), color,
                              anchor="midtop", serif=True)
                ty = r.bottom + 2
        super().draw(surf)
