"""Пути к ресурсам и кэш шрифтов/картинок (работает и из исходников, и из сборки PyInstaller)."""
import json
import os
import sys

import pygame


def base_dir():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def path(*parts):
    return os.path.join(base_dir(), "assets", *parts)


_fonts = {}
_images = {}
FONT = {"scale": 1.0, "serif": False}  # общий размер и шрифт; меняются в режиме разработчика (design.py)


def clear_cache():
    """Шрифты и картинки привязаны к экземпляру pygame; после pygame.quit их нужно создать заново."""
    _fonts.clear()
    _images.clear()


def clear_fonts():
    _fonts.clear()


def font(size, bold=False, serif=False, italic=False):
    size = max(8, int(size * FONT["scale"]))
    serif = serif or FONT["serif"]
    key = (size, bold, serif, italic)
    if key not in _fonts:
        family = "DejaVuSerif" if serif else "DejaVuSans"
        if bold:
            name = family + "-Bold.ttf"
        elif italic:
            name = family + ("-Italic.ttf" if serif else "-Oblique.ttf")
        else:
            name = family + ".ttf"
        _fonts[key] = pygame.font.Font(path("fonts", name), size)
    return _fonts[key]


def image(*parts):
    """Картинка или None, если файла нет."""
    key = parts
    if key not in _images:
        p = path(*parts)
        _images[key] = pygame.image.load(p).convert_alpha() if os.path.isfile(p) else None
    return _images[key]


def load_json(*parts):
    with open(path(*parts), encoding="utf-8") as f:
        return json.load(f)
