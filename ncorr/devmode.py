"""Режим разработчика (F12): конструктор оформления.

Работает при запуске из исходников и в версии разработчика (NeimarkCorrelation-dev, см. packaging.py);
в обычной версии для показа его нет.

Щелчок по элементу выбирает его, перетаскивание двигает, перетаскивание правого нижнего угла
меняет размер, стрелки двигают точно. Двигаются кнопки, ползунки, заголовки разделов и графики.
На панели инструментов: текст элемента, размер шрифта, все тексты, цвета, общий шрифт, отмена,
сохранение и сборка. Оформление записывается в assets/design.json (см. design.py), важные числа —
в assets/config.json (окно «Числа», см. config.py); всё сразу видно на экране.
Пока режим включён, кнопки демонстрации не нажимаются — сначала выйдите из режима (F12).

При выходе из режима (F12 или закрытие окна) правки сохраняются и собирается обычная версия:
- в версии разработчика — копированием самой себя рядом, за несколько секунд (packaging.export_show);
- из исходников — так же из dist/<платформа>/NeimarkCorrelation-dev, если она не старее кода,
  иначе полной сборкой tools/build.py.
"""
import copy
import json
import os
import subprocess
import sys
import threading
import time

import pygame

from . import config, design, i18n, packaging, resources as res, theme
from .ui.plot import label_box
from .ui import widgets
from .ui.widgets import Button, Slider, draw_text, fit_text

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRID = 0.05     # шаг сдвига мышью, в единицах u
HANDLE = 10     # размер уголка для изменения размера, px
ACCENT = (255, 120, 0)
OUTLINE = (40, 130, 255)
GRAPH_OUTLINE = (0, 170, 90)
TOOLBAR_BG = (35, 35, 40)
TOOLBAR_FG = (235, 235, 235)


FROZEN = getattr(sys, "frozen", False)


def allowed():
    """Из исходников — всегда; в собранной программе — только в версии разработчика (есть метка)."""
    return not FROZEN or os.path.exists(res.path(packaging.MARKER))


def _design_json():
    """Всё, из чего собирается обычная версия: оформление и числа."""
    return json.dumps({"design": design.data, "config": config.values}, sort_keys=True)


def _newest_source():
    """Время последнего изменения кода и ресурсов (кроме design.json) — не устарела ли сборка."""
    newest = 0.0
    for top in ("ncorr", "assets"):
        for base, _, files in os.walk(os.path.join(ROOT, top)):
            for name in files:
                if name not in (design.FILE, config.FILE) and not name.endswith(".pyc"):
                    newest = max(newest, os.path.getmtime(os.path.join(base, name)))
    for name in ("main.py", os.path.join("build", "neimark.spec")):
        newest = max(newest, os.path.getmtime(os.path.join(ROOT, name)))
    return newest


class DevMode:
    def __init__(self, app):
        self.app = app
        self.active = False
        self.selected = None     # id выбранного элемента
        self.text_key = None     # ключ надписи выбранного элемента
        self.drag = None         # (что тащим, мышь в начале, значения в начале)
        self.modal = None        # None, "text", "texts", "colors", "numbers"
        self.undo = []
        self.dirty = False
        self.status = ""
        self.status_time = 0.0
        self.toolbar_pos = None  # левый верхний угол панели; None — по умолчанию
        self.collapsed = False   # панель свёрнута в одну строку (Tab)
        self.texts = []          # надписи последнего кадра: (прямоугольник, текст)
        self.last_click = (0.0, (0, 0))
        self.build = None        # процесс полной сборки (из исходников)
        self.build_design = None
        self.job = None          # поток быстрой сборки обычной версии
        self.exported = _design_json()  # оформление, из которого собрана последняя обычная версия
        self.auto_export = True  # собирать обычную версию при выходе из режима (тесты выключают)
        self.reset_all_time = 0.0
        # правка текста или числа: edit_key — ключ надписи или (раздел, ключ) числа
        self.edit_key = None
        self.edit_lang = None
        self.buffer = ""
        self.defaults_time = 0.0
        # список всех текстов
        self.filter = ""
        self.scroll = 0
        self._rows = []  # (прямоугольник строки, ключ) — для щелчков по списку
        # цвета
        self.color = None
        self.sliders = [Slider(lambda c=c: c, 0, 255, 0, self._on_rgb, fmt=lambda v: str(int(v)), font_size=14)
                        for c in ("R", "G", "B")]
        self.b_color_reset = Button(lambda: "Вернуть исходный", self._color_reset, 14)
        # числа
        self.cfg_buttons = [
            Button(lambda: "Открыть config.json", self._open_config_file, 14),
            Button(lambda: "Перечитать файл", self._reload_config, 14),
            Button(lambda: "Всё по умолчанию", self._config_defaults, 14),
        ]
        self.buttons = [
            Button(lambda: "Текст элемента", self._edit_selected_text, 14),
            Button(lambda: "Шрифт −", lambda: self._scale_font(1 / 1.1), 14),
            Button(lambda: "Шрифт +", lambda: self._scale_font(1.1), 14),
            Button(lambda: "Сбросить элемент", self._reset_selected, 14),
            Button(lambda: "Все тексты", lambda: self._open("texts"), 14),
            Button(lambda: "Цвета", lambda: self._open("colors"), 14),
            Button(lambda: "Числа (config)", lambda: self._open("numbers"), 14),
            Button(lambda: "Шрифт: с засечками" if design.data["font"]["serif"] else "Шрифт: без засечек",
                   self._toggle_serif, 14),
            Button(lambda: "Весь текст −", lambda: self._global_font(1 / 1.05), 14),
            Button(lambda: "Весь текст +", lambda: self._global_font(1.05), 14),
            Button(lambda: "Отменить", self._undo, 14),
            Button(lambda: "Сохранить", self._save, 14),
            Button(lambda: "Собрать обычную версию", self.export, 14),
            Button(lambda: "Сбросить всё", self._reset_all, 14),
            Button(lambda: "Выйти (F12)", self.toggle, 14),
        ]

    # ---------- общее ----------

    def toggle(self):
        self.active = not self.active
        self.modal = None
        self.drag = None
        if self.active:
            pygame.key.start_text_input()
            self._say("режим разработчика включён")
        else:
            self.finish()

    def finish(self):
        """Выход из режима (F12 или закрытие окна): сохранить и, если оформление менялось, собрать обычную версию."""
        if self.dirty:
            self._save()
        if not self.auto_export:
            return
        if _design_json() != self.exported:
            self.export()
        else:
            self._say("режим разработчика выключен; оформление не менялось, обычная версия не пересобирается")

    def busy(self):
        return bool(self.job and self.job["thread"].is_alive()) or bool(self.build and self.build.poll() is None)

    def export(self):
        """Собрать обычную версию с текущим оформлением."""
        if self.busy():
            self._say("сборка уже идёт")
            return
        self._save()
        if FROZEN:
            self._start_export(os.path.dirname(sys.executable), None, None)
            return
        plat = packaging.platform_name()
        dev_dir = os.path.join(ROOT, "dist", plat, packaging.DEV_NAME)
        exe = os.path.join(dev_dir, packaging.exe_name(plat))
        if os.path.isfile(exe) and os.path.getmtime(exe) >= _newest_source():
            self._start_export(dev_dir, os.path.join(ROOT, "dist", plat), os.path.join(ROOT, "dist"))
        else:  # код менялся после последней сборки (или её нет) — нужна полная сборка
            self._build()

    def _start_export(self, app_dir, out_dir, zip_dir):
        with open(design.file_path(), "rb") as f:
            files = {design.FILE: f.read(), config.FILE: config.dumps().encode("utf-8")}
        job = {"result": None, "error": None, "design": _design_json()}

        def work():
            try:
                job["result"] = packaging.export_show(app_dir, files, out_dir, zip_dir)
            except Exception as e:  # показать пользователю любую ошибку
                job["error"] = e

        # не фоновый поток: если окно закрыли, программа дождётся конца сборки
        job["thread"] = threading.Thread(target=work, daemon=False)
        job["thread"].start()
        self.job = job
        self._say("собирается обычная версия")

    def _say(self, text):
        self.status, self.status_time = text, time.time()

    def _u(self):
        return theme.unit(self.app.screen.get_height())

    def _items(self):
        return design.items(self.app, self.app.active)

    def _item(self, id):
        return next((it for it in self._items() if it.id == id), None)

    def _push(self):
        self.undo.append((design.snapshot(), copy.deepcopy(config.values)))
        del self.undo[:-100]

    def _changed(self, relayout=True):
        self.dirty = True
        if relayout:
            self.app._layout()

    def _ov(self, id):
        return design.data["widgets"].setdefault(id, {})

    # ---------- действия панели ----------

    def _edit_selected_text(self):
        if not self.text_key:
            self._say("у этого элемента нет постоянной надписи — найдите её в «Все тексты»")
            return
        self._edit_text(self.text_key)

    def _edit_text(self, key):
        self.edit_key, self.edit_lang = key, i18n.lang()
        self.buffer = i18n.raw(key)
        self.modal = "text"

    def _scale_font(self, k):
        if not self.selected:
            self._say("сначала выберите элемент")
            return
        if ".graph." in self.selected:
            self._say("у графика шрифт меняется кнопками «Весь текст − / +»")
            return
        self._push()
        ov = self._ov(self.selected)
        ov["fs"] = round(ov.get("fs", 1.0) * k, 3)
        self._changed()

    def _reset_selected(self):
        if self.selected and self.selected in design.data["widgets"]:
            self._push()
            del design.data["widgets"][self.selected]
            self._changed()

    def _toggle_serif(self):
        self._push()
        design.data["font"]["serif"] = not design.data["font"]["serif"]
        design.apply_global()
        self._changed()

    def _global_font(self, k):
        self._push()
        f = design.data["font"]
        f["scale"] = round(min(1.6, max(0.6, f.get("scale", 1.0) * k)), 3)
        design.apply_global()
        self._changed()

    def _undo(self):
        if not self.undo:
            self._say("отменять нечего")
            return
        snap, numbers = self.undo.pop()
        design.restore(snap)
        if numbers != config.values:
            config.values = numbers
            config.save()
            self.app.rebuild()
        self._changed()

    def _save(self):
        design.save()
        config.save()
        self.dirty = False
        self._say("сохранено: design.json и config.json")

    # ---------- числа (config.json) ----------

    def _edit_number(self, section, key):
        self.edit_key, self.edit_lang = (section, key), None
        self.buffer = config.fmt(config.values[section][key])
        self.modal = "text"

    def _apply_number(self):
        section, key = self.edit_key
        old = copy.deepcopy(config.values)
        try:
            config.set_value(section, key, self.buffer)
        except (ValueError, TypeError):
            self._say(f"«{self.buffer}» — не число; ничего не изменено")
            return False
        self.undo.append((design.snapshot(), old))
        config.save()
        self.app.rebuild()
        self.dirty = True
        self._say(f"{section}.{key} = {config.fmt(config.values[section][key])} — экраны перестроены")
        return True

    def _open_config_file(self):
        config.save()
        path = config.file_path()
        try:
            if sys.platform == "win32":
                os.startfile(path)
            else:
                subprocess.Popen(["xdg-open", path])
            self._say("config.json открыт в редакторе; после правки нажмите «Перечитать файл»")
        except OSError as e:
            self._say(f"не удалось открыть {path}: {e}")

    def _reload_config(self):
        self._push()
        config.load()
        self.app.rebuild()
        self.dirty = True
        self._say("числа перечитаны из config.json")

    def _config_defaults(self):
        if time.time() - self.defaults_time > 3:
            self.defaults_time = time.time()
            self._say("нажмите «Всё по умолчанию» ещё раз, чтобы вернуть все числа к значениям из кода")
            return
        self._push()
        config.use_defaults()
        config.save()
        self.app.rebuild()
        self.dirty = True
        self._say("все числа — по умолчанию")

    def _build(self):
        if self.build and self.build.poll() is None:
            self._say("сборка уже идёт")
            return
        self._save()
        log = open(os.path.join(ROOT, "build", "dev-build.log"), "w", encoding="utf-8")
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        self.build = subprocess.Popen([sys.executable, os.path.join(ROOT, "tools", "build.py"), "--no-tests"],
                                      cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
        self.build_design = _design_json()
        self._say("код менялся, поэтому полная сборка (около минуты), журнал: build/dev-build.log")

    def _reset_all(self):
        if time.time() - self.reset_all_time > 3:
            self.reset_all_time = time.time()
            self._say("нажмите «Сбросить всё» ещё раз, чтобы вернуть оформление из кода")
            return
        self._push()
        design.data = design.empty()
        design.apply_global()
        self._changed()
        self._say("оформление сброшено (не сохранено)")

    def _open(self, modal):
        self.modal = modal
        self.filter, self.scroll = "", 0
        if modal == "colors" and not self.color:
            self._pick_color(next(iter(design.COLORS)))

    def _pick_color(self, name):
        self.color = name
        for s, c in zip(self.sliders, getattr(theme, name)):
            s.value = c

    def _on_rgb(self, value, final):
        if self.color:
            if not self.drag:
                self._push()
                self.drag = ("rgb", None, None)
            if final:
                self.drag = None
            design.set_color(self.color, [s.value for s in self.sliders])
            self.dirty = True

    def _color_reset(self):
        if self.color:
            self._push()
            design.set_color(self.color, design.DEFAULT_COLORS[self.color])
            self._pick_color(self.color)
            self.dirty = True

    # ---------- события ----------

    def handle(self, event):
        """Режим разработчика забирает себе мышь и клавиатуру, пока включён."""
        if self.modal == "text":
            return self._handle_text(event)
        if self.modal in ("texts", "colors", "numbers"):
            return self._handle_list(event)
        if not self.collapsed:
            for b in self.buttons:
                if b.handle(event):
                    return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            self.collapsed = not self.collapsed
            return True
        if event.type == pygame.KEYDOWN:
            return self._handle_key(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._toolbar_rect().collidepoint(event.pos):
                self.drag = ("toolbar", event.pos, self._toolbar_rect().topleft)
                return True
            self._press(event.pos)
            return True
        if event.type == pygame.MOUSEMOTION and self.drag:
            self._move(event.pos)
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.drag:
            kind, _, start = self.drag
            if kind in ("move", "resize") and design.data["widgets"].get(self.selected) == start:
                self.undo.pop()  # щёлкнули, но не сдвинули — отменять нечего
            self.drag = None
            return True
        return event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL, pygame.TEXTINPUT)

    def _text_at(self, pos):
        """Ключ надписи под мышью (по тексту последнего кадра) или None."""
        hits = [h for h in self.texts if h[0].inflate(4, 4).collidepoint(pos)]
        for r, s, key in sorted(hits, key=lambda h: h[0].width * h[0].height):
            key = key or i18n.find_key(s)
            if key:
                return key
        return None

    def _press(self, pos):
        now = time.time()
        t0, p0 = self.last_click
        self.last_click = (now, pos)
        if now - t0 < 0.4 and abs(pos[0] - p0[0]) < 6 and abs(pos[1] - p0[1]) < 6:
            key = self._text_at(pos)  # двойной щелчок по любой надписи — правка этой надписи
            if key:
                self._edit_text(key)
            else:
                self._say("эта надпись — число или собрана программой; её не изменить")
            return
        u = self._u()
        hit = [it for it in self._items() if it.rect(u).collidepoint(pos)]
        if not hit:
            self.selected = self.text_key = None
            return
        it = min(hit, key=lambda i: i.rect(u).width * i.rect(u).height)  # самый маленький — самый «внутренний»
        self.selected = it.id
        self.text_key = self._text_at(pos) or it.text_key(pos)
        if it.kind == "graph":  # у графика «текст элемента» — его заголовок
            title = it._get(it.title) if it.title else None
            self.text_key = self._text_at((title[0] + 3, title[1] + 3)) if title else self._text_at(pos)
        r = it.rect(u)
        corner = pygame.Rect(r.right - HANDLE, r.bottom - HANDLE, HANDLE, HANDLE)
        self._push()
        start = dict(design.data["widgets"].get(it.id, {}))
        self.drag = ("resize" if corner.collidepoint(pos) and it.resizable else "move", pos, start)
        design.data["widgets"][it.id] = dict(start)

    def _move(self, pos):
        kind, p0, start = self.drag
        if kind == "toolbar":
            self.toolbar_pos = (start[0] + pos[0] - p0[0], start[1] + pos[1] - p0[1])
            return
        if kind not in ("move", "resize"):
            return
        u = self._u()
        dx, dy = (pos[0] - p0[0]) / u, (pos[1] - p0[1]) / u
        ov = dict(start)
        a, b = ("dx", "dy") if kind == "move" else ("dw", "dh")
        ov[a] = round((start.get(a, 0.0) + dx) / GRID) * GRID
        ov[b] = round((start.get(b, 0.0) + dy) / GRID) * GRID
        design.data["widgets"][self.selected] = ov
        self._changed()

    def _handle_key(self, event):
        ctrl = event.mod & pygame.KMOD_CTRL
        if ctrl and event.key == pygame.K_s:
            self._save()
        elif ctrl and event.key == pygame.K_z:
            self._undo()
        elif event.key == pygame.K_ESCAPE:
            self.selected = self.text_key = None
        elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
            self._reset_selected()
        elif event.key == pygame.K_RETURN:
            self._edit_selected_text()
        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN) and self.selected:
            step = 1.0 if event.mod & pygame.KMOD_SHIFT else 0.1
            dx = {pygame.K_LEFT: -step, pygame.K_RIGHT: step}.get(event.key, 0.0)
            dy = {pygame.K_UP: -step, pygame.K_DOWN: step}.get(event.key, 0.0)
            self._push()
            ov = self._ov(self.selected)
            key_x, key_y = ("dw", "dh") if event.mod & pygame.KMOD_ALT else ("dx", "dy")
            ov[key_x] = round(ov.get(key_x, 0.0) + dx, 3)
            ov[key_y] = round(ov.get(key_y, 0.0) + dy, 3)
            self._changed()
        return True

    def _handle_text(self, event):
        if event.type == pygame.TEXTINPUT:
            self.buffer += event.text
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.buffer = self.buffer[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.modal = "numbers" if isinstance(self.edit_key, tuple) else None
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if isinstance(self.edit_key, tuple):  # число из config.json
                    if self._apply_number():
                        self.modal = "numbers"
                    return True
                self._push()
                design.set_text(self.edit_key, self.edit_lang, self.buffer)
                self.modal = None
                self._changed()
            elif event.key == pygame.K_v and event.mod & pygame.KMOD_CTRL:
                pasted = _clipboard()
                if pasted:
                    self.buffer += pasted
        return True

    def _handle_list(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.modal = None
            return True
        if self.modal == "colors":
            for w in self.sliders + [self.b_color_reset]:
                if w.handle(event):
                    return True
        if self.modal == "numbers":
            for b in self.cfg_buttons:
                if b.handle(event):
                    return True
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, self.scroll - event.y * 3)
        elif self.modal == "texts" and event.type == pygame.TEXTINPUT:
            self.filter += event.text
            self.scroll = 0
        elif self.modal == "texts" and event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
            self.filter = self.filter[:-1]
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self._modal_rect().collidepoint(event.pos):
                self.modal = None
                return True
            for rect, value in self._rows:
                if rect.collidepoint(event.pos):
                    if self.modal == "texts":
                        self._edit_text(value)
                    elif self.modal == "numbers":
                        self._edit_number(*value)
                    else:
                        self._pick_color(value)
        return True

    # ---------- рисование ----------

    def update(self):
        if self.build and self.build.poll() is not None:
            code = self.build.returncode
            if code == 0:
                self.exported = self.build_design
            self._say("готово: обычная версия в dist/windows/NeimarkCorrelation и архив в dist" if code == 0 else
                      f"сборка не удалась (код {code}), см. build/dev-build.log")
            self.build = None
        if self.job and not self.job["thread"].is_alive():
            job, self.job = self.job, None
            if job["error"]:
                self._say(f"обычная версия не собрана: {job['error']} (если она запущена, закройте её)")
            else:
                folder, archive = job["result"]
                self.exported = job["design"]
                self._say(f"готово: обычная версия {folder}, архив {os.path.basename(archive)}")

    def draw_status(self, surf):
        """Строка состояния сборки, когда режим уже выключен."""
        self.update()
        if not (self.busy() or self.status and time.time() - self.status_time < 8):
            return
        text = ("идёт сборка обычной версии...  " if self.busy() else "") + self.status
        img = res.font(self._px(14), bold=True).render(text, True, ACCENT)
        w, h = surf.get_size()
        rect = img.get_rect(bottomleft=(12, h - 8))
        box = pygame.Surface((rect.width + 16, rect.height + 8), pygame.SRCALPHA)
        box.fill(TOOLBAR_BG + (230,))
        surf.blit(box, (rect.x - 8, rect.y - 4))
        surf.blit(img, rect)

    def draw(self, surf):
        self.update()
        u = self._u()
        for it in self._items():
            r = it.rect(u)
            if it.id == self.selected:
                pygame.draw.rect(surf, ACCENT, r.inflate(4, 4), 2)
                if it.resizable:
                    pygame.draw.rect(surf, ACCENT, (r.right - HANDLE + 2, r.bottom - HANDLE + 2, HANDLE, HANDLE))
            else:
                pygame.draw.rect(surf, GRAPH_OUTLINE if it.kind == "graph" else OUTLINE, r.inflate(2, 2), 1)
        self._draw_toolbar(surf)
        if self.modal == "text":
            self._draw_text_modal(surf)
        elif self.modal == "texts":
            self._draw_texts(surf)
        elif self.modal == "colors":
            self._draw_colors(surf)
        elif self.modal == "numbers":
            self._draw_numbers(surf)

    # ---------- размеры: всё от размера окна ----------

    def _k(self):
        """Масштаб интерфейса конструктора: при высоте окна ~680 px — 1, на больших экранах больше."""
        return max(1.0, self._u() / 13) * 1.1

    def _px(self, v):
        return int(v * self._k())

    def _toolbar_rect(self):
        w, h = self.app.screen.get_size()
        p = self._px
        width, height = min(w - 20, p(800)), p(32) if self.collapsed else p(236)
        if self.toolbar_pos is None:
            self.toolbar_pos = (12, h - height - 12)  # слева внизу: не закрывает панель управления справа
        x = min(max(self.toolbar_pos[0], 0), w - width)
        y = min(max(self.toolbar_pos[1], 0), h - height)
        return pygame.Rect(x, y, width, height)

    def _draw_toolbar(self, surf):
        p = self._px
        r = self._toolbar_rect()
        box = pygame.Surface(r.size, pygame.SRCALPHA)
        box.fill(TOOLBAR_BG + (238,))
        surf.blit(box, r)
        pygame.draw.rect(surf, ACCENT, r, 1)
        draw_text(surf, "РЕЖИМ РАЗРАБОТЧИКА" + ("  •  есть несохранённые изменения" if self.dirty else ""),
                  (r.x + p(10), r.y + p(6)), p(15), ACCENT, bold=True)
        draw_text(surf, "Tab — " + ("развернуть" if self.collapsed else "свернуть") + " панель; её можно перетащить",
                  (r.right - p(10), r.y + p(8)), p(12), (150, 150, 150), anchor="topright")
        if self.collapsed:
            return
        u = self._u()
        sel = self._item(self.selected) if self.selected else None
        if sel:
            ov = design.data["widgets"].get(sel.id, {})
            info = (f"{sel.id}   сдвиг {ov.get('dx', 0):+.2f}, {ov.get('dy', 0):+.2f}   размер {ov.get('dw', 0):+.2f}, "
                    f"{ov.get('dh', 0):+.2f}   шрифт ×{ov.get('fs', 1):.2f}   (в единицах u = {u}px)")
            if self.text_key:
                info += f"   текст: {self.text_key}"
        else:
            info = "щёлкните элемент (синие — кнопки и заголовки, зелёные — графики); тащите — двигать; уголок — размер"
        draw_text(surf, info, (r.x + p(10), r.y + p(30)), fit_text(info, p(14), r.width - p(20)), TOOLBAR_FG)
        per_row, bh, gap = 5, p(34), p(6)
        bw = (r.width - p(20) - gap * (per_row - 1)) // per_row
        for i, b in enumerate(self.buttons):
            row, col = divmod(i, per_row)
            b.rect = pygame.Rect(r.x + p(10) + col * (bw + gap), r.y + p(56) + row * (bh + gap), bw, bh)
            b.font_size = p(15)
            b.draw(surf)
        hint = ("двойной щелчок по надписи — изменить её   стрелки — сдвиг (Shift — крупно, Alt — размер)   "
                "Enter — текст элемента   Delete — сброс   Ctrl+S   Ctrl+Z")
        draw_text(surf, hint, (r.x + p(10), r.bottom - p(44)), fit_text(hint, p(13), r.width - p(20)), (160, 160, 160))
        if self.status and time.time() - self.status_time < 8 or (self.build and self.build.poll() is None):
            draw_text(surf, self.status, (r.x + p(10), r.bottom - p(22)), fit_text(self.status, p(14), r.width - p(20)),
                      ACCENT)

    def _modal_rect(self):
        w, h = self.app.screen.get_size()
        width = min(w - 40, self._px(980))
        return pygame.Rect((w - width) // 2, 20, width, h - 40)

    def _panel(self, surf, rect, title):
        dim = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 90))
        surf.blit(dim, (0, 0))
        pygame.draw.rect(surf, theme.BG, rect, border_radius=8)
        pygame.draw.rect(surf, ACCENT, rect, 2, border_radius=8)
        p = self._px
        draw_text(surf, title, (rect.x + p(14), rect.y + p(10)), fit_text(title, p(18), rect.width - p(28), bold=True),
                  (0, 0, 0), bold=True)

    def _draw_text_modal(self, surf):
        w, h = surf.get_size()
        p = self._px
        width = min(w - 40, p(980))
        rect = pygame.Rect((w - width) // 2, h // 2 - p(110), width, p(220))
        number = isinstance(self.edit_key, tuple)
        if number:
            section, key = self.edit_key
            what = config.entry(section, key)[3]
            self._panel(surf, rect, f"Число {section}.{key}")
            base = f"{what}   (по умолчанию: {config.fmt(config.DEFAULTS[section][key])})"
        else:
            self._panel(surf, rect, f"Надпись «{self.edit_key}», язык: {self.edit_lang}")
            base = "в коде: " + i18n.base(self.edit_key, self.edit_lang)
        draw_text(surf, base, (rect.x + p(14), rect.y + p(46)), fit_text(base, p(14), rect.width - p(28)),
                  (110, 110, 110))
        field = pygame.Rect(rect.x + p(14), rect.y + p(80), rect.width - p(28), p(48))
        pygame.draw.rect(surf, (245, 245, 245), field)
        pygame.draw.rect(surf, ACCENT, field, 1)
        cursor = "|" if int(time.time() * 2) % 2 else " "
        text = self.buffer + cursor
        draw_text(surf, text, (field.x + p(6), field.centery), fit_text(text, p(20), field.width - p(12)), (0, 0, 0),
                  anchor="midleft")
        if number:
            lo, hi = config.entry(*self.edit_key)[4]
            tips = (f"Enter — применить (экраны перестроятся), Esc — назад. Допустимо от {config.fmt(lo)} до "
                    f"{config.fmt(hi)}; список — через запятую.", "")
        else:
            tips = ("Enter — применить, Esc — отмена, Ctrl+V — вставить. Поля в {скобках} не меняйте: туда "
                    "подставляются числа.",
                    "Другой язык — выйдите (Esc), переключите язык кнопкой English/Русский и откройте надпись снова.")
        y = rect.bottom - p(62)
        for tip in tips:
            draw_text(surf, tip, (rect.x + p(14), y), fit_text(tip, p(13), rect.width - p(28)), (110, 110, 110))
            y += p(24)

    def _scroll_rows(self, rect, y, count, row_h):
        visible = max(1, (rect.bottom - y - 10) // row_h)
        self.scroll = min(self.scroll, max(0, count - visible))
        return visible

    def _draw_texts(self, surf):
        p = self._px
        rect = self._modal_rect()
        self._panel(surf, rect, f"Все тексты ({i18n.lang()}) — щёлкните строку, чтобы изменить; колесо — прокрутка; Esc — закрыть")
        q = self.filter.lower()
        draw_text(surf, "поиск: " + self.filter + "|", (rect.x + p(14), rect.y + p(42)), p(16), ACCENT)
        keys = [k for k in i18n.STRINGS if q in k.lower() or q in i18n.raw(k).lower()]
        self._rows = []
        y = rect.y + p(72)
        row_h = p(28)
        visible = self._scroll_rows(rect, y, len(keys), row_h)
        key_w = p(200)
        for k in keys[self.scroll:self.scroll + visible]:
            r = pygame.Rect(rect.x + p(10), y, rect.width - p(20), row_h)
            if r.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(surf, (255, 235, 210), r)
            changed = k in design.data["texts"].get(i18n.lang(), {})
            draw_text(surf, k, (r.x + p(4), r.centery), fit_text(k, p(13), key_w - p(8)),
                      ACCENT if changed else (120, 120, 120), anchor="midleft")
            text = i18n.raw(k)
            draw_text(surf, text, (r.x + key_w, r.centery), fit_text(text, p(15), r.width - key_w - p(6)), (0, 0, 0),
                      anchor="midleft")
            self._rows.append((r, k))
            y += row_h

    def _draw_colors(self, surf):
        p = self._px
        rect = self._modal_rect()
        self._panel(surf, rect, "Цвета — выберите слева (колесо мыши — прокрутка), настройте ползунками справа; Esc — закрыть")
        self._rows = []
        y = rect.y + p(50)
        list_w = int(rect.width * 0.55)
        row_h = p(32)
        names = list(design.COLORS)
        visible = self._scroll_rows(rect, y, len(names), row_h)
        for name in names[self.scroll:self.scroll + visible]:
            what = design.COLORS[name]
            r = pygame.Rect(rect.x + p(10), y, list_w - p(20), row_h - p(2))
            if name == self.color:
                pygame.draw.rect(surf, (255, 235, 210), r)
            swatch = pygame.Rect(r.x + p(4), r.y + p(4), p(44), r.height - p(8))
            pygame.draw.rect(surf, getattr(theme, name), swatch)
            pygame.draw.rect(surf, (120, 120, 120), swatch, 1)
            changed = name in design.data["colors"]
            draw_text(surf, what, (swatch.right + p(10), r.centery), fit_text(what, p(16), r.right - swatch.right - p(14)),
                      ACCENT if changed else (0, 0, 0), anchor="midleft")
            self._rows.append((r, name))
            y += row_h
        if self.color:
            x = rect.x + list_w + p(10)
            width = rect.right - x - p(16)
            title = design.COLORS[self.color]
            draw_text(surf, title, (x, rect.y + p(50)), fit_text(title, p(18), width, bold=True), (0, 0, 0), bold=True)
            draw_text(surf, f"theme.{self.color}", (x, rect.y + p(80)), p(14), (120, 120, 120))
            sw = pygame.Rect(x, rect.y + p(108), width, p(90))
            pygame.draw.rect(surf, getattr(theme, self.color), sw)
            pygame.draw.rect(surf, (120, 120, 120), sw, 1)
            yy = sw.bottom + p(20)
            for s in self.sliders:
                s.font_size = p(16)
                s.layout((x, yy, width, p(56)))
                s.draw(surf)
                yy += p(64)
            self.b_color_reset.font_size = p(16)
            self.b_color_reset.rect = pygame.Rect(x, yy + p(8), width, p(40))
            self.b_color_reset.draw(surf)

    def _draw_numbers(self, surf):
        p = self._px
        rect = self._modal_rect()
        self._panel(surf, rect, "Числа (config.json) — щёлкните строку, чтобы изменить; колесо — прокрутка; Esc — закрыть")
        bw = (rect.width - p(28) - p(12)) // 3
        for i, b in enumerate(self.cfg_buttons):
            b.font_size = p(15)
            b.rect = pygame.Rect(rect.x + p(14) + i * (bw + p(6)), rect.y + p(44), bw, p(36))
            b.draw(surf)
        rows = []
        last = None
        for section, key, default, what, _ in config.SCHEMA:
            if section != last:
                rows.append(("head", section))
                last = section
            rows.append(("row", (section, key)))
        self._rows = []
        y = rect.y + p(92)
        row_h = p(28)
        visible = self._scroll_rows(rect, y, len(rows), row_h)
        value_w = p(170)
        for kind, value in rows[self.scroll:self.scroll + visible]:
            r = pygame.Rect(rect.x + p(10), y, rect.width - p(20), row_h)
            if kind == "head":
                draw_text(surf, config.SECTIONS[value], (r.x + p(4), r.centery), p(16), ACCENT, anchor="midleft",
                          bold=True)
            else:
                section, key = value
                if r.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(surf, (255, 235, 210), r)
                current = config.values[section][key]
                changed = current != config.DEFAULTS[section][key]
                what = config.entry(section, key)[3]
                draw_text(surf, what, (r.x + p(14), r.centery), fit_text(what, p(15), r.width - value_w - p(24)),
                          (0, 0, 0), anchor="midleft")
                text = config.fmt(current)
                draw_text(surf, text, (r.right - p(6), r.centery), fit_text(text, p(16), value_w, bold=True),
                          ACCENT if changed else (0, 0, 0), anchor="midright", bold=True)
                self._rows.append((r, value))
            y += row_h


def _clipboard():
    try:
        return pygame.scrap.get_text() if hasattr(pygame.scrap, "get_text") else ""
    except Exception:
        return ""
