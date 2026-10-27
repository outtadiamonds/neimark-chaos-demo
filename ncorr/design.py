"""Оформление, изменённое в режиме разработчика (F12), — файл assets/design.json.

Файл хранит только отличия от того, что задано в коде:
    widgets  — сдвиг и изменение размера элементов в единицах u (theme.unit), множитель шрифта;
    colors   — цвета из theme.py;
    texts    — надписи из i18n.py, отдельно для "ru" и "en";
    font     — общий множитель размера шрифта и шрифт с засечками.
Файл читается при каждом запуске — и из исходников, и в собранной программе (он лежит в assets
и попадает в сборку вместе с ними). Удалите его — и вернётся оформление из кода.
"""
import copy
import json
import os

from . import i18n, resources as res, theme
from .ui.widgets import Widget

FILE = "design.json"

# Цвета, которые можно менять, и что ими нарисовано
COLORS = {
    "BG": "фон окна",
    "FG": "основной текст",
    "MUTED": "второстепенный текст, подписи осей",
    "PANEL": "фон панели справа",
    "BORDER": "рамка панели",
    "GRID": "сетка графиков",
    "AXIS": "оси, пружина",
    "BUTTON": "кнопка",
    "BUTTON_HOVER": "кнопка под мышью",
    "BUTTON_PRESSED": "нажатая кнопка",
    "SELECTED": "выбранная кнопка, ползунок",
    "SELECTED_TEXT": "текст выбранной кнопки",
    "DISABLED_TEXT": "текст недоступной кнопки",
    "PROCESS": "траектория, процесс yₙ",
    "SHIFTED": "синий: груз, точки yₙ, ветви, сдвинутая копия",
    "POSITIVE": "вклад > 0",
    "NEGATIVE": "удар, вклад < 0, предупреждения",
    "BAR": "столбики эксперимента",
    "BAR_CURRENT": "строящийся столбик",
    "THEORY": "теория (пунктир)",
    "CURSOR": "текущее состояние, точка y*",
    "REGION": "аттрактор, область хаоса",
    "REGION_NORMAL": "нормальный режим на плоскости параметров",
    "TWIN": "близкая траектория",
    "TWIN_LIGHT": "след близкой траектории",
}
DEFAULT_COLORS = {name: getattr(theme, name) for name in COLORS}

data = {}


def empty():
    return {"widgets": {}, "colors": {}, "texts": {"ru": {}, "en": {}}, "font": {"scale": 1.0, "serif": False}}


def file_path():
    return res.path(FILE)


def load():
    """Прочитать assets/design.json (если есть) и применить цвета, тексты и шрифт."""
    global data
    data = empty()
    try:
        with open(file_path(), encoding="utf-8") as f:
            saved = json.load(f)
        for key in data:
            if isinstance(saved.get(key), dict):
                data[key].update(saved[key])
        for lang in ("ru", "en"):
            data["texts"].setdefault(lang, {})
    except (OSError, ValueError):
        pass
    apply_global()


def save():
    clean = copy.deepcopy(data)
    clean["widgets"] = {k: v for k, v in clean["widgets"].items() if any(v.get(f, d) != d for f, d in
                                                                         (("dx", 0), ("dy", 0), ("dw", 0), ("dh", 0),
                                                                          ("fs", 1)))}
    with open(file_path(), "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=1)


def snapshot():
    return copy.deepcopy(data)


def restore(snap):
    global data
    data = copy.deepcopy(snap)
    apply_global()


def apply_global():
    """Цвета, тексты и шрифт действуют сразу на всю программу."""
    for name, default in DEFAULT_COLORS.items():
        setattr(theme, name, tuple(data["colors"].get(name, default)))
    i18n.OVERRIDES = data["texts"]
    font = data["font"]
    res.FONT["scale"] = float(font.get("scale", 1.0))
    res.FONT["serif"] = bool(font.get("serif", False))
    res.clear_fonts()


def set_color(name, rgb):
    rgb = [int(c) for c in rgb]
    if tuple(rgb) == tuple(DEFAULT_COLORS[name]):
        data["colors"].pop(name, None)
    else:
        data["colors"][name] = rgb
    apply_global()


def set_text(key, lang, text):
    base = i18n.base(key, lang)
    if text == base:
        data["texts"][lang].pop(key, None)
    else:
        data["texts"][lang][key] = text


# ---------- элементы экранов ----------

class Item:
    """Элемент, который можно двигать: виджет экрана или заголовок раздела на панели."""

    kind = "widget"

    def __init__(self, id, obj=None, screen=None, index=None):
        self.id = id
        self.obj = obj
        self.screen = screen
        self.index = index
        if obj is None:
            self.kind = "label"

    @property
    def is_label(self):
        return self.kind == "label"

    @property
    def resizable(self):
        return self.kind != "label"

    def text_key(self, mouse=None):
        """Ключ надписи в i18n.py (для кнопок — найденный по тексту)."""
        if self.is_label:
            return self.screen.labels[self.index][0]
        obj = self.obj
        buttons = getattr(obj, "buttons", None)
        if buttons and mouse:  # ряд переключателей: надпись той кнопки, на которую щёлкнули
            for b in buttons:
                if b.rect.collidepoint(mouse):
                    obj = b
        label = getattr(obj, "label", None)
        return i18n.find_key(label()) if callable(label) else None

    def rect(self, u):
        if self.is_label:
            key, pos = self.screen.labels[self.index][:2]
            size = int(u * 1.05 * self.screen.label_scale.get(key, 1.0))
            w, h = res.font(size, bold=True).size(i18n.t(key))
            return _rect(pos, (w, h))
        return self.obj.rect

    def apply(self, ov, u):
        dx, dy, dw, dh = (ov.get(k, 0.0) * u for k in ("dx", "dy", "dw", "dh"))
        fs = ov.get("fs", 1.0)
        if self.is_label:
            entry = list(self.screen.labels[self.index])
            x, y = entry[1]
            entry[1] = (round(x + dx), round(y + dy))
            self.screen.labels[self.index] = tuple(entry)
            self.screen.label_scale[entry[0]] = fs
            return
        obj = self.obj
        if fs != 1.0 and hasattr(obj, "font_size"):
            obj.font_size = max(8, round(obj.font_size * fs))
        r = obj.rect.move(round(dx), round(dy))
        r.width, r.height = max(12, r.width + round(dw)), max(8, r.height + round(dh))
        if hasattr(obj, "layout"):
            obj.layout(r)  # ряд кнопок, ползунок, плоскость параметров раскладывают себя заново
        else:
            obj.rect = r


class GraphItem(Item):
    """График: прямоугольник осей (Axes или Rect) и, если есть, позиция его заголовка.

    Экран перечисляет свои графики в словаре GRAPHS: имя → (поле осей, поле заголовка);
    поле — имя атрибута или (имя списка, номер). Заголовок едет вместе с графиком.
    """

    kind = "graph"

    def __init__(self, id, screen, target, title):
        super().__init__(id, obj=True, screen=screen)
        self.kind = "graph"
        self.target, self.title = target, title

    def _get(self, ref):
        attr, i = (ref, None) if isinstance(ref, str) else ref
        value = getattr(self.screen, attr)
        return value[i] if i is not None else value

    def _set(self, ref, value):
        attr, i = (ref, None) if isinstance(ref, str) else ref
        if i is None:
            setattr(self.screen, attr, value)
        else:
            getattr(self.screen, attr)[i] = value

    def text_key(self, mouse=None):
        return None

    def rect(self, u):
        t = self._get(self.target)
        return t.rect if hasattr(t, "rect") else t

    def apply(self, ov, u):
        dx, dy, dw, dh = (round(ov.get(k, 0.0) * u) for k in ("dx", "dy", "dw", "dh"))
        r = self.rect(u).move(dx, dy)
        r.width, r.height = max(40, r.width + dw), max(30, r.height + dh)
        t = self._get(self.target)
        if hasattr(t, "rect"):
            t.rect = r
        else:
            self._set(self.target, r)
        if self.title is not None:
            x, y = self._get(self.title)
            self._set(self.title, (x + dx, y + dy))


def _rect(pos, size):
    import pygame
    return pygame.Rect(pos, size)


def items(app, name):
    """Все элементы экрана name, которые можно двигать: id вида «motion.b_run»."""
    screen = app.screens[name]
    out = []
    for attr, val in vars(screen).items():
        if attr == "widgets":
            continue
        if isinstance(val, Widget):
            out.append(Item(f"{name}.{attr}", val))
        elif isinstance(val, list) and val and all(isinstance(v, Widget) for v in val):
            out += [Item(f"{name}.{attr}[{i}]", v) for i, v in enumerate(val)]
    if name == app.active:
        if getattr(screen, "tabs_rect", None) is not None:
            out.append(Item(f"{name}.@tabs", app.tabs))
        out.append(Item(f"{name}.@lang", app.lang_button))
    for i, entry in enumerate(getattr(screen, "labels", [])):
        out.append(Item(f"{name}.label.{entry[0]}", screen=screen, index=i))
    for graph, (target, title) in getattr(screen, "GRAPHS", {}).items():
        try:
            out.append(GraphItem(f"{name}.graph.{graph}", screen, target, title))
        except AttributeError:  # экран ещё не разложен
            pass
    return [it for it in out if it.kind != "widget" or (it.obj.visible and it.obj.rect.width > 0)]


def apply_layout(app, u):
    """Вызывается в конце App._layout: сдвинуть элементы так, как записано в design.json."""
    for name, screen in app.screens.items():
        screen.label_scale = {}
        for it in items(app, name):
            ov = data["widgets"].get(it.id)
            if ov:
                it.apply(ov, u)
