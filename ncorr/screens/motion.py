"""Вкладка «Движение осциллятора» демонстрации (часть А. С. Григорьева, перенесена из веб-версии).

Одномерный осциллятор с отрицательным трением: анимация груза на пружине, фазовая траектория
(x, v), скорость v(t) как проекция траектории и отображение за полпериода. Фазовая плоскость
и график v(t) имеют общую шкалу скорости, поэтому текущая точка соединяется с графиком v(t)
горизонтальной пунктирной линией — проекцией.

Рядом идёт вторая траектория, начатая со скоростью больше на ε: пока обе находятся по одну
сторону от точки ветвления y*, они совпадают, а разница растёт как ε·γ^(n/2); когда она
доходит до y*, траектории попадают на разные ветви (одна получает удар, другая нет) и дальше
движутся независимо. Так из динамической неопределённости появляется случайность.
Вторая вкладка — «Корреляционная функция» (demo.py); переключатель вкладок общий (App.tabs).
"""
import math

import pygame

from .. import config
from .. import resources as res
from .. import theme
from ..i18n import t
from ..physics import neimark as nm
from ..ui.plot import Axes, boxed_text, dashed_polyline, label_box
from ..ui.widgets import Button, Segmented, Slider, draw_text, fit_text, remember_text
from .base import Screen
from .demo import draw_legend

# Числа берутся из assets/config.json (раздел "motion", см. config.py); refresh() перечитывает их
PHASE_TRAIL = TIME_WINDOW = CURVE_SAMPLES = TRACK = 0
FLASH_DECAY = 0.0
SCENARIOS = {}  # сценарий → (параметры осциллятора, начальная скорость v0 в единицах a)
TWINS = {}      # "1", "2", … → ε, отклонение начальной скорости второй траектории


def refresh():
    global PHASE_TRAIL, TIME_WINDOW, CURVE_SAMPLES, FLASH_DECAY, TRACK, SCENARIOS, TWINS
    c = config.motion
    PHASE_TRAIL = c.phase_trail      # полупериодов в следе на фазовой плоскости
    TIME_WINDOW = c.time_window      # полупериодов на графике v(t)
    CURVE_SAMPLES = c.curve_samples  # точек кривой на полупериод
    FLASH_DECAY = c.flash_decay      # как быстро гаснет вспышка удара, в 1/с
    TRACK = c.track                  # сколько последних yₙ видно на графике двух траекторий
    SCENARIOS = {
        "H": (nm.PRESETS["H"], c.v0_markov),
        "E": (nm.PRESETS["E"], c.v0_markov),
        "normal": (nm.Params(c.normal_gamma, c.normal_h), c.normal_v0),  # нормальный режим h < a
        "free": (nm.Params(c.free_gamma, 0.0), c.free_v0),               # без ударов: уходит на бесконечность
    }
    TWINS = {str(i + 1): eps for i, eps in enumerate(c.twins)}


def eps_label(eps):
    """10⁻⁵ для степеней десяти, иначе число как есть."""
    k = math.log10(eps)
    return f"10{superscript(round(k))}" if abs(k - round(k)) < 1e-9 else f"{eps:g}"


refresh()


def curve(half, delta, upto=math.pi):
    """Точки (u, x, v) одного полупериода от u = 0 до upto."""
    n = max(1, int(CURVE_SAMPLES * upto / math.pi))
    out = []
    for j in range(n + 1):
        u = upto * j / n
        out.append((u, half.y * nm.position(u, delta), half.y * nm.shape(u, delta)))
    return out


def fmt_speed(v):
    return f"× {v:.2g}" if v < 10 else "× " + f"{int(round(v, -1 if v < 1000 else -2)):,}".replace(",", " ")


class MotionScreen(Screen):
    # графики, которые можно двигать в режиме разработчика: имя → (оси, заголовок)
    GRAPHS = {
        "oscillator": ("osc_rect", "osc_title"),
        "phase": ("phase_ax", "phase_title"),
        "time": ("time_ax", "time_title"),
        "map": ("map_ax", "map_title"),
        "twins": ("seq_ax", "twin_title"),
        "dy": ("dy_ax", None),
    }

    def __init__(self, app):
        super().__init__(app)
        self.scenario = "H"
        p, v0 = SCENARIOS["H"]
        self.params, self.v0 = p, v0
        self.speed = config.motion.speed
        self.running = False
        default = config.motion.twin_default
        self.twin_key = str(default) if str(default) in TWINS else "off"
        self.show_projection = True
        self.show_sections = True
        self.flash = 0.0
        self._synced = (p.gamma, p.h)  # параметры, последний раз переданные на вкладку корреляции

        self.sc_row1 = Segmented([("H", lambda: t("preset_H")), ("E", lambda: t("preset_E"))],
                                 "H", self._set_scenario)
        self.sc_row2 = Segmented([("normal", lambda: t("sc_normal")), ("free", lambda: t("sc_free"))],
                                 None, self._set_scenario)
        c = config.motion
        self.s_gamma = Slider(lambda: t("gamma"), c.gamma_min, c.gamma_max, p.gamma, self._on_gamma,
                              fmt=lambda v: f"{v:.3f}")
        self.s_h = Slider(lambda: t("h"), c.h_min, c.h_max, p.h, self._on_h, fmt=lambda v: f"{v:.3f}")
        self.s_v0 = Slider(lambda: t("v0"), c.v0_min, c.v0_max, v0, self._on_v0, fmt=lambda v: theme.num(v, 2))
        options = [("off", lambda: t("twin_off"))] + [(key, lambda e=eps: eps_label(e)) for key, eps in TWINS.items()]
        self.twin_sel = Segmented(options, self.twin_key, self._set_twin)
        self.s_speed = Slider(lambda: t("speed"), c.speed_min, c.speed_max, self.speed, self._on_speed, log=True,
                              fmt=fmt_speed)
        self.b_run = Button(lambda: t("pause") if self.running else t("run"), self._toggle_run)
        self.b_step = Button(lambda: t("step_pi"), self._step)
        self.b_reset = Button(lambda: t("reset"), self._reset)
        self.b_proj = Button(lambda: t("projection"), self._toggle_projection)
        self.b_sect = Button(lambda: t("sections"), self._toggle_sections)
        self.b_back = Button(lambda: t("back"), lambda: app.show("menu"))
        self.widgets = [app.tabs, self.sc_row1, self.sc_row2, self.s_gamma, self.s_h, self.s_v0, self.twin_sel,
                        self.s_speed, self.b_run, self.b_step, self.b_reset, self.b_proj, self.b_sect, self.b_back]
        self._reset()

    # ---------- состояние ----------

    def _reset(self):
        """Начать опыт заново: движение с t = 0 и вторая траектория."""
        self.motion = nm.Motion(self.params, self.v0)
        self.ext = max(1.5, nm.A * 1.4, abs(self.v0) * 1.5)
        self.flash = 0.0
        self._restart_twin()

    def _restart_twin(self):
        """Вторая траектория: копия текущего состояния, скорость больше на ε."""
        eps = TWINS.get(self.twin_key)
        self.twin = nm.Motion.near(self.motion, eps) if eps else None
        self.twin_start = self.motion.crossings
        self.split_n = None   # номер yₙ, начиная с которого траектории разошлись
        self.track = []       # (n, yₙ, yₙ второй траектории или None)
        self._record(self.motion.crossings)

    def enter(self):
        self.running = not self.motion.escaped

    def _set_scenario(self, name):
        self.scenario = name
        self.sc_row1.value = name if name in ("H", "E") else None
        self.sc_row2.value = name if name in ("normal", "free") else None
        p, v0 = SCENARIOS[name]
        self.params, self.v0 = p, v0
        self.s_gamma.value, self.s_h.value, self.s_v0.value = p.gamma, p.h, v0
        self._reset()
        self.running = True

    def _custom(self):
        self.scenario = None
        self.sc_row1.value = self.sc_row2.value = None

    def _on_gamma(self, v, final):
        self._custom()
        self.params = nm.Params(v, self.params.h)
        self._reset()

    def _on_h(self, v, final):
        self._custom()
        self.params = nm.Params(self.params.gamma, v)
        self._reset()

    def _on_v0(self, v, final):
        self._custom()
        self.v0 = v
        self._reset()

    def _on_speed(self, v, final):
        self.speed = v

    def _set_twin(self, key):
        self.twin_key = key
        self._restart_twin()

    def _toggle_projection(self):
        self.show_projection = not self.show_projection

    def _toggle_sections(self):
        self.show_sections = not self.show_sections

    def sync_correlation(self):
        """Перед переходом на вкладку корреляции передать ей γ и h, если они здесь менялись.

        Параметры прижимаются к области хаоса (вне её корреляционная функция не определена).
        Если здесь ничего не меняли, на вкладке корреляции остаются её собственные параметры.
        """
        key = (self.params.gamma, self.params.h)
        if key != self._synced:
            self._synced = key
            self.app.screens["demo"].use_params(*key)

    def _toggle_run(self):
        if self.motion.escaped:
            self._reset()
        self.running = not self.running

    def _step(self):
        self.running = False
        if not self.motion.escaped:
            self._advance(math.pi)

    # ---------- движение ----------

    def _advance(self, dt):
        # пока момент расхождения не найден, двигаемся кусками: история хранится не вся
        chunk = 500 * math.pi if self.twin and self.split_n is None else dt
        while dt > 0 and not self.motion.escaped:
            part = min(dt, chunk)
            dt -= part
            before = self.motion.crossings
            if self.motion.advance(part):
                self.flash = 1.0
            if self.twin:
                self.twin.advance(part)
            if self.motion.crossings != before:
                self._record(before + 1)
        if self.motion.escaped:
            self.running = False

    def _half(self, mo, n):
        """Полупериод номер n движения mo, если он ещё хранится."""
        i = len(mo.halves) - 1 - (mo.crossings - n)
        return mo.halves[i] if 0 <= i < len(mo.halves) else None

    def _record(self, first):
        """Запомнить yₙ обеих траекторий для n от first до текущего и найти момент расхождения.

        Траектории расходятся, когда в конце одного и того же полупериода одна получает удар,
        а другая нет: их скорости оказались по разные стороны от точки ветвления y*.
        """
        mo, tw = self.motion, self.twin
        last = mo.crossings
        if tw and self.split_n is None:
            for n in range(max(first - 1, self.twin_start, mo.halves[0].n), last):
                a, b = self._half(mo, n), self._half(tw, n)
                if a and b and b.after is not None and a.hit != b.hit:
                    self.split_n = n + 1
                    break
        for n in range(max(first, last - TRACK), last + 1):
            a = self._half(mo, n)
            b = self._half(tw, n) if tw else None
            if a:
                self.track.append((n, a.y, b.y if b else None))
        del self.track[:-TRACK - 1]

    def update(self, dt):
        if self.running:
            self._advance(dt * self.speed)
        self.flash = max(0.0, self.flash - dt * FLASH_DECAY)
        # масштаб только растёт во время опыта, чтобы графики не «прыгали»
        peak = max(1.0, nm.A)
        for mo in (self.motion, self.twin):
            if mo is None or mo.escaped:
                continue
            x, v = mo.state()
            peak = max(peak, abs(x), abs(v))
            for half in mo.halves[-PHASE_TRAIL:]:
                peak = max(peak, abs(half.y), abs(half.before or 0.0))
        self.ext = max(self.ext, math.ceil(min(peak, nm.Motion.LIMIT) * 1.15 * 4) / 4)

    def handle(self, event):
        if super().handle(event):
            return True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self._toggle_run()
                return True
            if event.key == pygame.K_RIGHT:
                self._step()
                return True
        return False

    # ---------- раскладка ----------

    def layout(self, w, h):
        u = theme.unit(h)
        self.u = u
        m = int(u * 1.1)
        pw = int(max(w * 0.25, 300))
        px = w - pw - m
        self.panel = pygame.Rect(px, m, pw, h - 2 * m)
        fs = int(u * 1.05)
        for wdg in (self.sc_row1, self.sc_row2, self.twin_sel, self.b_run, self.b_step, self.b_reset,
                    self.b_proj, self.b_sect, self.b_back):
            wdg.font_size = fs
        for s in (self.s_gamma, self.s_h, self.s_v0, self.s_speed):
            s.font_size = int(u * 0.95)

        x, width = px + 12, pw - 24
        row = int(u * 2.1)
        gap = int(u * 0.5)
        slider_h = int(u * 2.8)
        label_h = int(u * 1.5)
        self.labels = []
        y = m + 10
        self.tabs_rect = pygame.Rect(x, y, width, int(u * 2.3))  # переключатель вкладок ставит App
        y += self.tabs_rect.height + gap * 3

        def section(key):
            nonlocal y
            self.labels.append((key, (x, y)))
            y += label_h

        section("sec_scenario")
        self.sc_row1.layout((x, y, width, row))
        y += row + gap
        self.sc_row2.layout((x, y, width, row))
        y += row + gap * 2
        section("sec_params")
        for s in (self.s_gamma, self.s_h, self.s_v0):
            s.layout((x, y, width, slider_h))
            y += slider_h + gap
        y += gap
        section("sec_twin")
        self.twin_sel.layout((x, y, width, row))
        y += row + gap * 2
        self.formula_pos = (x, y)

        # снизу вверх: язык и «Назад», строки информации, кнопки, скорость
        bottom = self.panel.bottom - 10
        half = width // 2
        self.b_back.rect = pygame.Rect(x + half + 4, bottom - row, width - half - 4, row)
        self.lang_rect = pygame.Rect(x, bottom - row, half - 4, row)
        info_lines = 4
        line_h = int(u * 1.3)
        y2 = bottom - row - gap * 2 - line_h * info_lines
        self.info_pos = (x, y2)
        y2 -= gap * 2 + row
        self.b_proj.rect = pygame.Rect(x, y2, half - 3, row)
        self.b_sect.rect = pygame.Rect(x + half + 3, y2, width - half - 3, row)
        y2 -= gap + row
        bw = (width - 12) // 3
        self.b_run.rect = pygame.Rect(x, y2, bw, row)
        self.b_step.rect = pygame.Rect(x + bw + 6, y2, bw, row)
        self.b_reset.rect = pygame.Rect(x + 2 * (bw + 6), y2, width - 2 * (bw + 6), row)
        y2 -= gap + slider_h
        self.s_speed.layout((x, y2, width, slider_h))
        y2 -= label_h + gap
        self.labels.append(("sec_run", (x, y2)))
        self.formula_visible = y2 - self.formula_pos[1] > u * 3.5

        # слева три ряда: осциллятор; фазовая плоскость + v(t); отображение + две траектории
        lx = m + int(u * 3.2)
        lw = px - m - lx
        title_h, ticks_h, pgap = int(u * 1.5), int(u * 1.5), int(u * 0.6)
        free = h - 2 * m - 3 * title_h - 2 * ticks_h - 2 * pgap - int(u * 0.5)
        h0 = int(free * 0.18)
        h1 = int(free * 0.40)
        h2 = free - h0 - h1
        self.title_h = title_h
        y = m
        self.osc_title = (lx, y)
        self.osc_rect = pygame.Rect(lx - int(u * 2.5), y + title_h, lw + int(u * 2.5), h0)
        y += title_h + h0 + pgap
        side = min(h1, int(lw * 0.4))
        self.phase_title = (lx, y)
        self.phase_ax = Axes((lx, y + title_h, side, h1), (-1, 1), (-1, 1))
        tx = lx + side + int(u * 4.5)
        self.time_title = (tx, y)
        self.time_ax = Axes((tx, y + title_h, lx + lw - tx, h1), (0, 1), (-1, 1))
        y += title_h + h1 + ticks_h + pgap

        gx = int(u * 4.5)
        side2 = min(h2, int(lw * 0.4))
        self.map_title = (lx, y)
        self.map_ax = Axes((lx, y + title_h, side2, h2), (-1, 1), (-1, 1))
        x2 = lx + side2 + gx
        w2 = lx + lw - x2
        self.twin_title = (x2, y)
        top_h = int((h2 - ticks_h) * 0.6)
        self.seq_ax = Axes((x2, y + title_h, w2, top_h), (0, 1), (-1, 1))
        self.dy_ax = Axes((x2, y + title_h + top_h + ticks_h, w2, h2 - top_h - ticks_h), (0, 1), (-9, 1))

    # ---------- рисование ----------

    def draw(self, surf):
        u = self.u
        pygame.draw.rect(surf, theme.PANEL, self.panel, border_radius=8)
        pygame.draw.rect(surf, theme.BORDER, self.panel, 1, border_radius=8)
        for key, pos in self.labels:
            text = t(key)
            size = int(u * 1.05 * self.label_scale.get(key, 1.0))
            draw_text(surf, text, pos, fit_text(text, size, self.panel.right - 12 - pos[0], bold=True),
                      theme.FG, bold=True)
        self.b_proj.selected = self.show_projection
        self.b_sect.selected = self.show_sections
        super().draw(surf)
        if self.formula_visible:
            self._draw_formula(surf)
        self._draw_info(surf)
        self._draw_oscillator(surf)
        self._draw_phase(surf)
        self._draw_timeline(surf)
        self._draw_projection(surf)
        self._draw_map(surf)
        self._draw_twins(surf)
        if self.motion.escaped:
            self._draw_message(surf, t("escaped"), self.time_ax.rect)

    def _title(self, surf, key, pos, right, **kw):
        text = t(key, **kw)
        size = fit_text(text, int(self.u * 1.0), right - pos[0], bold=True)
        draw_text(surf, text, pos, size, bold=True)

    def _draw_message(self, surf, text, area):
        """Сообщение по центру области, с переносом строк по ширине области."""
        font = res.font(int(self.u * 1.1), bold=True)
        lines, line = [], ""
        for word in text.split():
            trial = (line + " " + word).strip()
            if line and font.size(trial)[0] > area.width - 30:
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
        imgs = [font.render(s, True, theme.NEGATIVE) for s in lines]
        remember_text(area, text)  # для правки двойным щелчком в режиме разработчика
        height = sum(i.get_height() for i in imgs)
        width = max(i.get_width() for i in imgs)
        box = pygame.Rect(0, 0, width, height)
        box.center = area.center
        label_box(surf, box, pad=10)
        y = box.y
        for img in imgs:
            surf.blit(img, img.get_rect(midtop=(box.centerx, y)))
            y += img.get_height()

    def _draw_formula(self, surf):
        x, y = self.formula_pos
        width = self.panel.right - 12 - x
        for line in (t("formula_title"), t("map_formula"), t("formula_note")):
            size = fit_text(line, int(self.u * 0.95), width)
            r = draw_text(surf, line, (x, y), size, theme.MUTED if line != t("formula_title") else theme.FG)
            y = r.bottom + 4

    def _draw_info(self, surf):
        u = self.u
        mo, p = self.motion, self.params
        x, v = mo.state()
        if not p.is_chaotic():
            region = t("region_out_weak") if p.h < p.gamma - 1 else t("region_out_strong")
        else:
            region = t("region_in_anomalous") if p.h > nm.A else t("region_in_normal")
        lines = [
            t("state_line", t=f"{mo.t:.2f}", x=theme.num(x), v=theme.num(v)),
            t("count_line", n=mo.crossings, hits=mo.hits),
            t("params_line", s=f"{p.s:.3f}", delta=f"{p.delta:.3f}"),
            region,
        ]
        px, py = self.info_pos
        width = self.panel.right - 12 - px
        for i, line in enumerate(lines):
            color = theme.NEGATIVE if i == 3 and not p.is_chaotic() else theme.FG
            draw_text(surf, line, (px, py), fit_text(line, int(u * 0.95), width), color)
            py += int(u * 1.3)

    # --- 1. осциллятор: стенка, пружина, груз, стрелка скорости ---

    def _draw_oscillator(self, surf):
        u = self.u
        r = self.osc_rect
        draw_text(surf, t("m_osc"), self.osc_title, int(u * 1.0), bold=True)
        items = [("rect", theme.CURSOR, t("lg_now_short")), ("rect", theme.NEGATIVE, t("lg_kick_short")),
                 ("rect", theme.SHIFTED, t("lg_section_short"))]
        if self.twin:
            items.append(("rect", theme.TWIN, t("lg_twin")))
        draw_legend(surf, items, r.right, self.osc_title[1], int(u * 0.85))
        x, v = self.motion.state()
        cx = r.centerx
        cy = r.y + int(r.height * 0.45)
        left, right = r.x + int(u * 2), r.right - int(u * 1)
        scale = (right - left) * 0.38 / self.ext
        size = int(min(u * 1.7, r.height * 0.4))
        rail = min(cy + int(u * 1.6), r.bottom - int(u * 1.2))
        pygame.draw.line(surf, theme.AXIS, (left, rail), (right, rail), 2)
        fs = int(u * 0.85)
        for i in (-2, -1, 0, 1, 2):
            tx = cx + i * self.ext / 2 * scale
            pygame.draw.line(surf, theme.AXIS, (tx, rail - 4), (tx, rail + 4))
            draw_text(surf, theme.num(i * self.ext / 2, 2) if i else "0", (tx, rail + 4), fs, theme.MUTED,
                      anchor="midtop")
        draw_text(surf, t("g_x"), (right, rail + 4), fs, theme.MUTED, anchor="topright")
        dashed_polyline(surf, theme.MUTED, [(cx, r.y + 2), (cx, rail)], dash=4, gap=4, width=1)
        # стенка со штриховкой
        wall = pygame.Rect(left, cy - size, 6, size * 2)
        pygame.draw.rect(surf, theme.PROCESS, wall)
        for i in range(6):
            y0 = wall.y + i * wall.height / 6
            pygame.draw.line(surf, theme.AXIS, (left - 7, y0 + 6), (left, y0))
        bx = cx + max(-self.ext, min(self.ext, x)) * scale
        # пружина: зигзаг от стенки до груза
        start, end = left + 6, bx - size / 2
        pts = [(start, cy), (start + 8, cy)]
        coils = 18
        span = end - start - 16
        for i in range(1, coils):
            pts.append((start + 8 + span * i / coils, cy + (size * 0.35 if i % 2 else -size * 0.35)))
        pts += [(end - 8, cy), (end, cy)]
        pygame.draw.lines(surf, theme.AXIS, False, pts, 2)
        # груз второй траектории — контуром (пока траектории совпадают, он скрыт под основным)
        if self.twin and not self.twin.escaped:
            tx = cx + max(-self.ext, min(self.ext, self.twin.state()[0])) * scale
            pygame.draw.rect(surf, theme.TWIN, (tx - size / 2 - 3, cy - size / 2 - 3, size + 6, size + 6), 2,
                             border_radius=7)
        # груз; при ударе вспыхивает красным
        hit = self.flash > 0.15
        color = theme.NEGATIVE if hit else theme.SHIFTED
        pygame.draw.rect(surf, color, (bx - size / 2, cy - size / 2, size, size), border_radius=6)
        # стрелка скорости над грузом
        ay = cy - size / 2 - int(u * 0.6)
        length = max(-1.0, min(1.0, v / self.ext)) * u * 5
        if abs(length) > 3:
            tip = bx + length
            sign = 1 if length > 0 else -1
            pygame.draw.line(surf, color, (bx, ay), (tip, ay), 3)
            pygame.draw.polygon(surf, color, [(tip, ay), (tip - sign * 9, ay - 5), (tip - sign * 9, ay + 5)])
            draw_text(surf, t("g_v"), (tip + sign * 6, ay), fs, color, anchor="midleft" if sign > 0 else "midright")
        if hit:
            radius = size * 0.7 + (1 - self.flash) * u * 2.5
            ring = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ring, theme.NEGATIVE + (int(255 * self.flash),), (radius + 2, radius + 2), radius, 2)
            surf.blit(ring, (cx - radius - 2, cy - radius - 2))
            draw_text(surf, t("kick_label"), (cx + size, r.y + 2), int(u * 0.95), theme.NEGATIVE, bold=True)

    # --- 2. фазовая плоскость ---

    def _draw_phase(self, surf):
        u = self.u
        ax = self.phase_ax
        e = self.ext
        ax.x0, ax.x1, ax.y0, ax.y1 = -e, e, -e, e
        self._title(surf, "m_phase", self.phase_title, self.time_title[0] - u)
        ax.frame(surf, int(u * 0.85), xticks=4, yticks=4, xlabel=t("g_x"))
        pygame.draw.line(surf, theme.AXIS, (ax.px(0), ax.rect.y), (ax.px(0), ax.rect.bottom))
        ay = ax.py(nm.A)
        dashed_polyline(surf, theme.NEGATIVE, [(ax.rect.x, ay), (ax.rect.right, ay)], dash=5, gap=4, width=1)
        draw_text(surf, t("g_a"), (ax.rect.right - 4, ay - 2), int(u * 0.85), theme.NEGATIVE, anchor="bottomright")
        surf.set_clip(ax.rect)
        d = self.params.delta
        tw = self.twin
        if tw and not tw.escaped:  # след второй траектории — короткий, цветом
            for i, half in enumerate(tw.halves[-3:]):
                upto = tw.s if half is tw.current else math.pi
                pts = [ax.point(x, v) for _, x, v in curve(half, d, upto)]
                if len(pts) > 1:
                    pygame.draw.aalines(surf, theme.TWIN_LIGHT, False, pts)
        mo = self.motion
        halves = mo.halves[-PHASE_TRAIL:]
        last = len(halves) - 1
        for i, half in enumerate(halves):
            upto = mo.s if i == last else math.pi
            shade = min(205, 20 + 8 * (last - i))
            pts = [ax.point(x, v) for _, x, v in curve(half, d, upto)]
            if len(pts) > 1:
                pygame.draw.aalines(surf, (shade, shade, shade), False, pts)
            if half.hit:
                pygame.draw.line(surf, theme.NEGATIVE, ax.point(0, half.before), ax.point(0, half.after), 2)
        if self.show_sections:
            for half in halves:
                pygame.draw.circle(surf, theme.SHIFTED, ax.point(0, half.y), 3)
        if tw and not tw.escaped:
            pygame.draw.circle(surf, theme.TWIN, ax.point(*tw.state()), 8, 2)
        pygame.draw.circle(surf, theme.CURSOR, ax.point(*mo.state()), 6)
        surf.set_clip(None)
        draw_text(surf, t("g_v"), (ax.rect.x + 5, ax.rect.y), int(u * 0.95), theme.FG, bold=True)

    # --- 3. скорость во времени ---

    def _time_window(self):
        span = TIME_WINDOW * math.pi
        start = max(0.0, self.motion.t - span * 0.92)
        return start, start + span

    def _draw_curve_in_time(self, surf, ax, mo, t0, color, marks):
        d = self.params.delta
        for half in mo.halves[-TIME_WINDOW - 2:]:
            if half.t0 + math.pi < t0:
                continue
            upto = mo.s if half is mo.current else math.pi
            pts = [ax.point((half.t0 + uu) / math.pi, v) for uu, _, v in curve(half, d, upto)]
            if len(pts) > 1:
                pygame.draw.aalines(surf, color, False, pts)
            if half.hit:
                tx = (half.t0 + math.pi) / math.pi
                pygame.draw.line(surf, theme.NEGATIVE if marks else color, ax.point(tx, half.before),
                                 ax.point(tx, half.after), 2 if marks else 1)
            if marks and self.show_sections:
                pygame.draw.circle(surf, theme.SHIFTED, ax.point(half.t0 / math.pi, half.y), 3)

    def _draw_timeline(self, surf):
        u = self.u
        ax = self.time_ax
        t0, t1 = self._time_window()
        ax.x0, ax.x1, ax.y0, ax.y1 = t0 / math.pi, t1 / math.pi, -self.ext, self.ext
        self._title(surf, "m_time", self.time_title, ax.rect.right)
        ax.frame(surf, int(u * 0.85), xticks=8, yticks=4, xlabel=t("g_t"))
        ay = ax.py(nm.A)
        dashed_polyline(surf, theme.NEGATIVE, [(ax.rect.x, ay), (ax.rect.right, ay)], dash=5, gap=4, width=1)
        draw_text(surf, t("g_a"), (ax.rect.right - 4, ay - 2), int(u * 0.85), theme.NEGATIVE, anchor="bottomright")
        surf.set_clip(ax.rect)
        if self.twin and not self.twin.escaped:
            self._draw_curve_in_time(surf, ax, self.twin, t0, theme.TWIN, False)
        mo = self.motion
        self._draw_curve_in_time(surf, ax, mo, t0, theme.PROCESS, True)
        pygame.draw.circle(surf, theme.CURSOR, ax.point(mo.t / math.pi, mo.state()[1]), 6)
        surf.set_clip(None)

    def _draw_projection(self, surf):
        """Горизонтальная линия от точки на фазовой плоскости к точке на графике v(t)."""
        if not self.show_projection:
            return
        x, v = self.motion.state()
        pa, ta = self.phase_ax, self.time_ax
        if not -self.ext <= v <= self.ext:
            return
        # к точке v(t) на втором графике (если графики сдвинуты по высоте, линия станет наклонной)
        dashed_polyline(surf, theme.CURSOR, [pa.point(x, v), ta.point(self.motion.t / math.pi, v)],
                        dash=5, gap=4, width=1)

    # --- 4. отображение за полпериода ---

    def _draw_map(self, surf):
        u = self.u
        ax = self.map_ax
        e = self.ext
        ax.x0, ax.x1, ax.y0, ax.y1 = -e, e, -e, e
        self._title(surf, "m_map", self.map_title, self.twin_title[0] - u)
        ax.frame(surf, int(u * 0.85), xticks=4, yticks=4, xlabel=t("g_yn"))
        p = self.params
        surf.set_clip(ax.rect)
        if p.is_chaotic():  # аттрактор [−√γ·a, a]
            lo = ax.point(p.lower, p.lower)
            hi = ax.point(nm.A, nm.A)
            pygame.draw.rect(surf, theme.REGION, (lo[0], hi[1], hi[0] - lo[0], lo[1] - hi[1]))
        dashed_polyline(surf, theme.AXIS, [ax.point(-e, -e), ax.point(e, e)], dash=4, gap=4, width=1)
        pygame.draw.line(surf, theme.AXIS, (ax.px(0), ax.rect.y), (ax.px(0), ax.rect.bottom))
        br = p.branch
        # правая ветвь (удара нет) и левая (удар), без вертикального соединения в разрыве
        pygame.draw.line(surf, theme.SHIFTED, ax.point(br, -p.s * br), ax.point(e, -p.s * e), 2)
        if p.h > 0:
            pygame.draw.line(surf, theme.SHIFTED, ax.point(-e, p.s * e - p.h), ax.point(br, nm.A - p.h), 2)
        else:
            pygame.draw.line(surf, theme.SHIFTED, ax.point(-e, p.s * e), ax.point(br, nm.A), 2)
        bx = ax.px(br)
        dashed_polyline(surf, theme.CURSOR, [(bx, ax.rect.y), (bx, ax.rect.bottom)], dash=4, gap=4, width=1)
        pairs = self.motion.pairs()
        n = len(pairs)
        for i, (a, b) in enumerate(pairs):
            k = (i + 1) / n
            color = tuple(int(255 + (c - 255) * (0.25 + 0.75 * k)) for c in theme.CURSOR)
            pygame.draw.circle(surf, color, ax.point(a, b), 2 if n > 300 else 3)
        if self.twin:
            tp = self.twin.pairs()
            if tp:
                pygame.draw.circle(surf, theme.TWIN, ax.point(*tp[-1]), 11, 2)
        if pairs:
            pygame.draw.circle(surf, theme.CURSOR, ax.point(*pairs[-1]), 8, 2)
        if p.h > 0:
            pygame.draw.circle(surf, theme.SHIFTED, ax.point(br, nm.A - p.h), 4)
            pygame.draw.circle(surf, theme.BG, ax.point(br, nm.A), 4)
            pygame.draw.circle(surf, theme.SHIFTED, ax.point(br, nm.A), 4, 2)
        surf.set_clip(None)
        draw_text(surf, t("g_yn1"), (ax.rect.x + 5, ax.rect.y), int(u * 0.95), theme.FG, bold=True)
        draw_text(surf, t("y_star"), (bx + 4, ax.rect.bottom - 4), int(u * 0.85), theme.CURSOR, anchor="bottomleft")

    # --- 5. две близкие траектории: случайность из динамической неопределённости ---

    def _draw_twins(self, surf):
        u = self.u
        fs = int(u * 0.85)
        ax, dax = self.seq_ax, self.dy_ax
        p = self.params
        last = self.motion.crossings
        first = max(0, last - TRACK)
        ax.x0, ax.x1 = first - 0.5, first + TRACK + 0.5
        lim = max(1.25, min(self.ext, 3.0))
        ax.y0, ax.y1 = -lim if not p.is_chaotic() else p.lower - 0.25, lim if not p.is_chaotic() else nm.A + 0.25
        self._title(surf, "m_twins" if self.twin else "m_seq", self.twin_title, ax.rect.right)
        ax.frame(surf, fs, xticks=4, yticks=4)
        # точка ветвления: ниже неё через полпериода будет удар
        by = ax.py(p.branch)
        if ax.y0 < p.branch < ax.y1:
            dashed_polyline(surf, theme.CURSOR, [(ax.rect.x, by), (ax.rect.right, by)], dash=4, gap=4, width=1)
        surf.set_clip(ax.rect.inflate(8, 8))
        if self.split_n is not None and ax.x0 <= self.split_n <= ax.x1:
            sx = ax.px(self.split_n)
            dashed_polyline(surf, theme.NEGATIVE, [(sx, ax.rect.y), (sx, ax.rect.bottom)], dash=3, gap=3, width=1)
        main = [(ax.px(n), ax.py(ax.clip_y(a))) for n, a, _ in self.track]
        twin = [(ax.px(n), ax.py(ax.clip_y(b))) for n, _, b in self.track if b is not None]
        if len(twin) > 1:
            pygame.draw.aalines(surf, theme.TWIN_LIGHT, False, twin)
        if len(main) > 1:
            pygame.draw.aalines(surf, theme.AXIS, False, main)
        for pt in twin:
            pygame.draw.circle(surf, theme.TWIN, pt, 6, 2)
        for pt in main:
            pygame.draw.circle(surf, theme.PROCESS, pt, 3)
        surf.set_clip(None)
        draw_text(surf, t("g_yn"), (ax.rect.x + 5, ax.rect.y), int(u * 0.95), theme.FG, bold=True)
        if ax.y0 < p.branch < ax.y1:
            boxed_text(surf, t("g_ystar"), res.font(fs), theme.CURSOR, bottomright=(ax.rect.right - 3, by - 1))

        # нижний график: lg |Δyₙ| и оценка ε·γ^(n/2)
        dax.x0, dax.x1 = ax.x0, ax.x1
        dax.frame(surf, fs, xticks=4, yticks=3, xlabel=t("g_n"), zero=False,
                  yfmt=lambda v: f"10{superscript(int(round(v)))}")
        eps = TWINS.get(self.twin_key)
        if not eps:
            draw_text(surf, t("twin_hint"), dax.rect.center, fs, theme.MUTED, anchor="center")
            return
        surf.set_clip(dax.rect)
        n0 = self.twin_start
        slope = math.log10(p.s) if p.gamma > 1 else 0.0
        a = (max(dax.x0, n0), math.log10(eps) + (max(dax.x0, n0) - n0) * slope)
        b = (dax.x1, math.log10(eps) + (dax.x1 - n0) * slope)
        if b[0] > a[0]:
            dashed_polyline(surf, theme.THEORY, [dax.point(*a), dax.point(*b)], dash=5, gap=4, width=2)
        for n, ya, yb in self.track:
            if yb is None:
                continue
            dy = abs(ya - yb)
            pygame.draw.circle(surf, theme.TWIN, dax.point(n, dax.clip_y(math.log10(dy) if dy > 0 else -99)), 3)
        surf.set_clip(None)
        boxed_text(surf, t("g_dy"), res.font(fs, bold=True), theme.FG, topleft=(dax.rect.x + 5, dax.rect.y + 2))
        draw_legend(surf, [("dash", theme.THEORY, t("g_growth"))], dax.rect.right - 4, dax.rect.y + 3, fs)
        # подпись: когда разошлись и сколько ожидалось
        expect = math.log(1 / eps) / math.log(p.s) if p.gamma > 1 else float("inf")
        if self.split_n is not None:
            text = t("twin_split", n=self.split_n - n0, e=f"{expect:.1f}")
        elif not p.is_chaotic():
            text = t("twin_nochaos")
        else:
            text = t("twin_same", e=f"{expect:.1f}")
        size = fit_text(text, fs, ax.rect.width - 10)
        boxed_text(surf, text, res.font(size), theme.NEGATIVE if self.split_n is not None else theme.FG,
                   bottomleft=(ax.rect.x + 5, ax.rect.bottom - 3))

    # ---------- для автоматической проверки ----------

    def test_setup(self, preset=None, seconds=0.0):
        if preset:
            self._set_scenario(preset)
        for _ in range(int(seconds * 30)):
            self.update(1 / 30)


def superscript(k):
    table = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
    return str(k).translate(table)
