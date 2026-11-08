"""Вкладка «Корреляционная функция» демонстрации: наглядное построение корреляционной функции.
Переключатель вкладок сверху панели общий с вкладкой «Движение осциллятора» (App.tabs).

Сверху — реализация процесса, ниже — та же реализация, сдвинутая на k (или τ).
Затем обе накладываются, цветом выделяются произведения отклонений от среднего,
их среднее по всей выборке даёт очередной столбик корреляционной функции.
"""
import math
import time

import pygame

from .. import config
from .. import resources as res
from .. import theme
from ..i18n import t
from ..physics import correlation, markov, neimark as nm
from ..ui import param_plane
from ..ui.param_plane import ParamPlane, clamp
from ..ui.phase_portrait import PhasePortrait
from ..ui.plot import Axes, point_marker, graph_line, graph_lines, curve_line, fading_trail, boxed_text, dashed_polyline, label_box, point_process
from ..ui.widgets import Button, Segmented, Slider, draw_text, fit_text, remember_text
from .base import Screen

# Числа берутся из assets/config.json (раздел "demo", см. config.py); refresh() перечитывает их
S = TAU_STEP = KMAX = C_STEPS = CONT_HALF = CURSOR_SPAN = 0
CURSOR_SPEED = SHIFT_END = PRODUCT_END = 0.0


def refresh():
    global S, TAU_STEP, KMAX, C_STEPS, CONT_HALF, CURSOR_SPEED, CURSOR_SPAN, SHIFT_END, PRODUCT_END
    c = config.demo
    S = c.samples                  # отсчётов v(t) на полпериод
    TAU_STEP = c.tau_step          # шаг сдвига для непрерывного процесса, в отсчётах (π/8)
    KMAX = c.kmax                  # сдвигов для последовательности y_n
    C_STEPS = c.c_steps            # сдвигов для v(t): до τ = 6π
    CONT_HALF = c.cont_half        # полупериодов, по которым считается C(τ)
    CURSOR_SPEED = c.cursor_speed  # полупериодов в секунду: движение точки по фазовой плоскости
    CURSOR_SPAN = c.cursor_span    # курсор обходит не больше стольких полупериодов от начала окна
    # доли одного шага анимации: сдвиг копии, появление произведений, рост столбика
    SHIFT_END = c.shift_end
    PRODUCT_END = max(c.product_end, SHIFT_END + 0.05)


refresh()


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def draw_legend(surf, items, right, top, fs):
    """Легенда в одну строку, выровненная по правому краю, на белой подложке."""
    font = res.font(fs)
    swatch, gap = 22, 14
    imgs = [font.render(text, True, theme.FG) for _, _, text in items]
    width = sum(swatch + 6 + img.get_width() for img in imgs) + gap * (len(items) - 1)
    height = max(img.get_height() for img in imgs)
    x = right - width
    label_box(surf, pygame.Rect(x, top, width, height))
    for (kind, color, text), img in zip(items, imgs):
        cy = top + height // 2
        if kind == "dash":
            dashed_polyline(surf, color, [(x, cy), (x + swatch, cy)], dash=6, gap=4)
        elif kind == "circle":
            point_marker(surf,color,(x+swatch/2,cy),5)
        elif kind == "diamond":
            cx = x+swatch/2
            pygame.draw.polygon(surf,color,[(cx,cy-6),(cx+6,cy),(cx,cy+6),(cx-6,cy)])
        else:
            pygame.draw.rect(surf, color, (x + 6, cy - 5, swatch - 12, 10))
        surf.blit(img, (x + swatch + 6, top))
        remember_text(img.get_rect(topleft=(x + swatch + 6, top)), text)
        x += swatch + 6 + img.get_width() + gap


class DemoScreen(Screen):
    # графики, которые можно двигать в режиме разработчика: имя → (оси, заголовок)
    GRAPHS = {
        "process": (("axes", 0), ("titles", 0)),
        "shifted": (("axes", 1), ("titles", 1)),
        "overlay": (("axes", 2), ("titles", 2)),
        "correlation": (("axes", 3), ("titles", 3)),
    }

    def __init__(self, app):
        super().__init__(app)
        self.mode = "d"
        self.params = nm.PRESETS["H"]
        c = config.demo
        self.n_samples = c.n_samples
        self.speed = c.speed
        self.seed = c.seed
        self.running = False
        self.filling = False
        self.view = {"d": [0, c.view_d], "c": [0, c.view_c * S]}  # [начало, длина] окна просмотра
        self._pan = None
        self.explain = True
        self.zoom_select = False
        self.zoom_drag = None
        self.zoom_ylim = None

        self.mode_sel = Segmented([("d", lambda: t("mode_d")), ("c", lambda: t("mode_c"))], "d", self._set_mode)
        self.preset_sel = Segmented([("H", lambda: t("preset_H")), ("E", lambda: t("preset_E")),
                                     ("custom", lambda: t("preset_custom"))], "H", self._set_preset)
        g, h = self.params.gamma, self.params.h
        self.s_gamma = Slider(lambda: t("gamma"), param_plane.GAMMA_MIN, param_plane.GAMMA_MAX, g, self._on_gamma, fmt=lambda v: f"{v:.3f}")
        self.s_h = Slider(lambda: t("h"), *self.params.h_range(), h, self._on_h, fmt=lambda v: f"{v:.3f}")
        self.plane = ParamPlane(self._on_plane)
        self.portrait = PhasePortrait()
        self.cursor = 0.0  # положение точки на фазовой плоскости, в полупериодах
        self.s_n = Slider(lambda: t("samples"), c.n_min, c.n_max, self.n_samples, self._on_n, log=True,
                          fmt=lambda v: f"{int(round(v, -2)):,}".replace(",", " "))
        self.s_speed = Slider(lambda: t("speed"), c.speed_min, c.speed_max, self.speed, self._on_speed, log=True,
                              fmt=lambda v: f"× {v:.2g}")
        self.b_run = Button(lambda: t("pause") if self.running else t("run"), self._toggle_run)
        self.b_step = Button(lambda: t("step"), self._step_click)
        self.b_reset = Button(lambda: t("reset"), self._reset)
        self.b_all = Button(lambda: t("build_all"), self._build_all)
        self.explain_sel = Segmented([("explain", lambda: t("explain_mode")),
                                      ("fast", lambda: t("fast_mode"))], "explain", self._set_explain)
        self.b_loupe = Button(lambda: t("loupe_active") if self.zoom_select else t("loupe"), self._toggle_loupe)
        self.b_view = Button(lambda: t("whole_process"), self._reset_view)
        self.b_back = Button(lambda: t("back"), lambda: app.show("menu"))
        self.widgets = [app.tabs, self.mode_sel, self.preset_sel, self.s_gamma, self.s_h, self.plane, self.s_n,
                        self.s_speed, self.explain_sel, self.b_loupe, self.b_view, self.b_run, self.b_step, self.b_reset, self.b_all, self.b_back]
        self._recompute()

    # ---------- данные ----------

    def _recompute(self):
        p = self.params
        self.ys = nm.sequence(p, int(self.n_samples), seed=self.seed)
        theory, part, moments, mean = markov.discrete_theory(p, KMAX)
        self.partition = part
        if self.mode == "d":
            self.unit = 1
            self.data = self.ys
            self.lags = list(range(KMAX + 1))
            self.theory = theory
        else:
            self.unit = S
            self.data = nm.velocity(self.ys[:CONT_HALF], p, S)
            self.lags = [i * TAU_STEP for i in range(C_STEPS + 1)]
            self.theory = markov.continuous_theory(p, S, self.lags[-1], moments, mean)
        self.est = correlation.Estimator(self.data)
        self.portrait.set_data(p, self.ys)
        self.sigma = math.sqrt(max(self.est.var,1e-30))
        self.dev_max = max(abs(min(self.est.centered)), abs(max(self.est.centered))) / self.sigma
        self.lo, self.hi = min(self.data), max(self.data)
        self.values = {}
        self._clamp_view()
        self._reset()

    def _value(self, lag):
        if lag not in self.values:
            self.values[lag] = self.est.normalized(lag)
        return self.values[lag]

    # ---------- анимация ----------

    def _reset(self):
        self.built = 0          # сколько столбиков уже построено
        self.phase = None       # фаза анимации текущего шага 0..1 или None
        self.shift = 0.0        # показываемый сдвиг, в отсчётах
        self.shift_from = 0.0
        self.running = False
        self.filling = False
        self._single_step = False

    def _begin_step(self):
        if self.built >= len(self.lags):
            self.running = False
            return
        self._value(self.lags[self.built])
        self.shift_from = self.shift
        self.phase = 0.0
        start, length = self._visible_range()
        count = min(config.demo.preview_pairs, length, len(self.data)-self.lags[self.built]-start)
        self.preview = list(range(start, start+max(1,int(count))))

    def _finish_step(self):
        self.shift = float(self.lags[self.built])
        self.phase = None
        self.built += 1

    def _toggle_run(self):
        self.filling = False
        self._single_step = False
        if self.built >= len(self.lags):
            self._reset()
        self.running = not self.running

    def _set_explain(self, name):
        self.explain = name == "explain"
        self._reset()

    def _duration(self):
        if not self.explain:
            return 1/1.2
        c = config.demo
        return c.explain_shift + 2*len(self.preview)*c.explain_pair + c.explain_average

    def _stage(self):
        """(стадия, индекс пары, число показанных произведений, рост итогового столбика)."""
        if self.phase is None:
            return "done", None, None, 1.0
        if not self.explain:
            return "fast", None, None, ease((self.phase-PRODUCT_END)/(1-PRODUCT_END))
        c = config.demo
        elapsed = self.phase*self._duration()
        if elapsed < c.explain_shift:
            return "shift", None, 0, 0.0
        elapsed -= c.explain_shift
        pair = int(elapsed/(2*c.explain_pair))
        if pair < len(self.preview):
            product = elapsed%(2*c.explain_pair) >= c.explain_pair
            return "product" if product else "pair", self.preview[pair], pair+int(product), 0.0
        elapsed -= 2*len(self.preview)*c.explain_pair
        return "average", None, None, ease(elapsed/c.explain_average)

    def _step_click(self):
        self.running = self.filling = False
        self._single_step = not self.explain
        if self.phase is None:
            self._begin_step()
        elif not self.explain:
            self._finish_step()
        else:
            c = config.demo
            boundaries = [c.explain_shift]
            boundaries += [c.explain_shift+j*c.explain_pair for j in range(1,2*len(self.preview)+1)]
            boundaries += [self._duration()]
            elapsed = self.phase*self._duration()
            nxt = next((v for v in boundaries if v > elapsed+1e-6), self._duration())
            self.phase = nxt/self._duration()+1e-8
            shift_fraction = min(1, nxt/c.explain_shift)
            target = self.lags[self.built]
            self.shift = self.shift_from+(target-self.shift_from)*ease(shift_fraction)
            if self.phase >= 1:
                self._finish_step()

    def _build_all(self):
        self.running = False
        self.phase = None
        self.filling = True

    def _cursor_range(self):
        """Полупериоды, которые обходит курсор: начало видимого окна и его длина."""
        start, length = self.view[self.mode]
        first = start // self.unit
        span = max(2, min(length // self.unit, CURSOR_SPAN))
        return first, min(first + span, len(self.ys) - 2)

    def update(self, dt):
        first, last = self._cursor_range()
        self.cursor += dt * CURSOR_SPEED * self.speed
        if not first <= self.cursor < last:
            self.cursor = float(first)
        if self.filling:
            start = time.perf_counter()
            while self.built < len(self.lags) and time.perf_counter() - start < 0.03:
                self._value(self.lags[self.built])
                self.built += 1
            self.shift = float(self.lags[self.built - 1]) if self.built else 0.0
            if self.built >= len(self.lags):
                self.filling = False
            return
        if self.phase is None:
            if self.running:
                self._begin_step()
            return
        if not self.running and not self._single_step:
            return
        self.phase += dt * self.speed / self._duration()
        target = self.lags[self.built]
        self.shift = self.shift_from + (target - self.shift_from) * ease(self.phase / (config.demo.explain_shift/self._duration() if self.explain else SHIFT_END))
        if self.phase >= 1.0:
            self._finish_step()

    def current_lag(self):
        """Сдвиг, для которого показаны произведения, и их видимость 0..1."""
        if self.phase is not None:
            if self.explain:
                stage, _, count, _ = self._stage()
                return self.lags[self.built], 0.0 if stage == "shift" else 1.0
            return self.lags[self.built], ease((self.phase - SHIFT_END) / (PRODUCT_END - SHIFT_END))
        if self.built:
            return self.lags[self.built - 1], 1.0
        return None, 0.0

    # ---------- параметры ----------

    def _set_mode(self, mode):
        self.mode = mode
        self.zoom_ylim = None
        self._recompute()

    def _set_preset(self, name):
        if name in nm.PRESETS:
            p = nm.PRESETS[name]
            self._show_params(p.gamma, p.h)
            self._apply(p.gamma, p.h)

    def _show_params(self, gamma, h):
        self.s_gamma.value = gamma
        self.s_h.set_range(*nm.Params(gamma, 0).h_range())
        self.s_h.value = h
        self.plane.gamma, self.plane.h = gamma, h
        preset = "custom"
        for name, p in nm.PRESETS.items():
            if abs(p.gamma - gamma) < 1e-9 and abs(p.h - h) < 1e-9:
                preset = name
        self.preset_sel.value = preset

    def use_params(self, gamma, h):
        """Взять параметры с вкладки «Движение осциллятора» (прижав их к области хаоса)."""
        g, h = clamp(gamma, h)
        self._show_params(g, h)
        self._apply(g, h)

    def _apply(self, gamma, h):
        p = nm.PRESETS.get(self.preset_sel.value) or nm.Params(gamma, h)
        if p != self.params:
            self.params = p
            self._recompute()

    def _on_gamma(self, v, final):
        g, h = clamp(v, self.s_h.value)
        self._show_params(g, h)
        if final:
            self._apply(g, h)

    def _on_h(self, v, final):
        g, h = clamp(self.s_gamma.value, v)
        self._show_params(g, h)
        if final:
            self._apply(g, h)

    def _on_plane(self, g, h, final):
        self._show_params(g, h)
        if final:
            self._apply(g, h)

    def _on_n(self, v, final):
        self.s_n.value = round(v, -2)
        if final and int(self.s_n.value) != self.n_samples:
            self.n_samples = int(self.s_n.value)
            self._recompute()

    def _on_speed(self, v, final):
        self.speed = v

    # ---------- окно просмотра ----------

    def _toggle_loupe(self):
        self.zoom_select = not self.zoom_select
        self.zoom_drag = self._pan = None

    def _reset_view(self):
        self.view[self.mode] = [0, config.demo.view_d if self.mode == "d" else config.demo.view_c*S]
        self.zoom_ylim = None
        self.zoom_select = False
        self.zoom_drag = None
        self._clamp_view()

    def _apply_zoom(self, index, a, b):
        ax = self.axes[index]
        left, right = sorted((max(ax.rect.left,min(ax.rect.right,a[0])), max(ax.rect.left,min(ax.rect.right,b[0]))))
        if right-left < 8:
            return
        start, end = ax.data_x(left)*self.unit, ax.data_x(right)*self.unit
        self.view[self.mode] = [start, end-start]
        self._clamp_view()
        if abs(a[1]-b[1]) > 12:
            def value(py):
                py = max(ax.rect.top,min(ax.rect.bottom,py))
                return ax.y1-(py-ax.rect.y)/ax.rect.height*(ax.y1-ax.y0)
            lo,hi = sorted((value(a[1]),value(b[1])))
            if index == 2:
                lo,hi = self.est.mean+lo*self.sigma,self.est.mean+hi*self.sigma
            if hi-lo > 1e-8:
                self.zoom_ylim = lo,hi
        self.zoom_select = False

    def _clamp_view(self):
        v = self.view[self.mode]
        lo_len, hi_len = (3, 2000) if self.mode == "d" else (S // 2, 200 * S)
        v[1] = int(min(max(v[1], lo_len), hi_len))
        v[0] = int(min(max(v[0], 0), len(self.data) - v[1] - self.lags[-1] - 2))

    def _plots_hit(self, pos):
        return any(ax.rect.collidepoint(pos) for ax in self.axes[:3])

    def handle(self, event):
        if super().handle(event):
            return True
        v = self.view[self.mode]
        if self.zoom_select and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i,ax in enumerate(self.axes[:3]):
                if ax.rect.collidepoint(event.pos):
                    self.zoom_drag = (i,event.pos,event.pos)
                    return True
        if self.zoom_drag and event.type == pygame.MOUSEMOTION:
            self.zoom_drag = (self.zoom_drag[0],self.zoom_drag[1],event.pos)
            return True
        if self.zoom_drag and event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            i,a,_ = self.zoom_drag
            self._apply_zoom(i,a,event.pos)
            self.zoom_drag = None
            return True
        if event.type == pygame.MOUSEWHEEL and self._plots_hit(pygame.mouse.get_pos()):
            ax = self.axes[0]
            mx = pygame.mouse.get_pos()[0]
            anchor = (mx - ax.rect.x) / ax.rect.width
            old = v[1]
            v[1] = old * (1.25 ** (-event.y))
            self._clamp_view()
            v[0] = int(v[0] + anchor * (old - v[1]))
            self._clamp_view()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self._plots_hit(event.pos):
            self._pan = (event.pos[0], v[0])
            return True
        if event.type == pygame.MOUSEMOTION and self._pan:
            per_px = v[1] / self.axes[0].rect.width
            v[0] = int(self._pan[1] - (event.pos[0] - self._pan[0]) * per_px)
            self._clamp_view()
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self._pan:
            self._pan = None
            return True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self._toggle_run()
                return True
            if event.key == pygame.K_RIGHT:
                self._step_click()
                return True
        return False

    # ---------- раскладка ----------

    def layout(self, w, h):
        # Панель имеет фиксированное число рядов: оставляем место двум мини-графикам
        # на всех высотах, включая 1200 px, где старый порог прятал их при F11.
        u = max(10, h // 56)
        self.u = u
        m = int(u * 1.1)
        pw = int(max(w * 0.27, 300))
        px = w - pw - m if self.app.panel_open else w + 12
        self.panel = pygame.Rect(px, m, pw, h - 2 * m)
        fs = int(u * 1.05)
        for wdg in (self.mode_sel, self.preset_sel, self.b_run, self.b_step, self.b_reset, self.b_all, self.b_back, self.explain_sel, self.b_loupe, self.b_view):
            wdg.font_size = fs
        for s in (self.s_gamma, self.s_h, self.s_n, self.s_speed):
            s.font_size = int(u * 0.95)
        self.plane.font_size = int(u * 0.85)

        x, width = px + 12, pw - 24
        row = int(u * 2.2)
        gap = int(u * 0.55)
        slider_h = int(u * 2.9)
        y = m + 10
        self.labels = []
        self.tabs_rect = pygame.Rect(x, y, width, int(u * 2.3))  # переключатель вкладок ставит App
        y += self.tabs_rect.height + gap * 2

        def section(key):
            nonlocal y
            self.labels.append((key, (x, y)))
            y += int(u * 1.55)

        section("sec_process")
        self.mode_sel.layout((x, y, width, row))
        y += row + gap
        section("sec_params")
        self.preset_sel.layout((x, y, width, row))
        y += row + gap
        self.s_gamma.layout((x, y, width, slider_h))
        y += slider_h + gap
        self.s_h.layout((x, y, width, slider_h))
        y += slider_h + gap
        plane_top = y

        # снизу вверх: назад, информация, кнопки, ползунки построения
        bottom = self.panel.bottom - 10
        self.b_back.rect = pygame.Rect(x, bottom - row, width, row)
        self.lang_rect = pygame.Rect(x, bottom - row, width // 2 - 4, row)
        info_lines = 2
        y2 = bottom - row - gap * 2 - int(u * 1.35) * info_lines
        self.info_pos = (x, y2)
        y2 -= gap * 2 + row
        self.b_all.rect = pygame.Rect(x, y2, width, row)
        y2 -= gap + row
        bw = (width - 2 * 6) // 3
        self.b_run.rect = pygame.Rect(x, y2, bw, row)
        self.b_step.rect = pygame.Rect(x + bw + 6, y2, bw, row)
        self.b_reset.rect = pygame.Rect(x + 2 * (bw + 6), y2, width - 2 * (bw + 6), row)
        y2 -= gap + row
        self.explain_sel.layout((x,y2,width,row))
        y2 -= gap + slider_h
        self.s_speed.layout((x, y2, width, slider_h))
        y2 -= gap + slider_h
        self.s_n.layout((x, y2, width, slider_h))
        y2 -= int(u * 1.55) + gap
        self.labels.append(("sec_build", (x, y2)))

        plane_h = y2 - plane_top - gap * 2
        self.plane.visible = self.portrait.visible = True
        self.portrait.font_size = int(u * 0.85)
        if self.plane.visible:
            half = (width - 10) // 2
            body = (plane_top + int(u * 1.4), plane_h - int(u * 1.4))
            self.labels.append(("plane", (x, plane_top), half))
            self.plane.layout((x, body[0], half, body[1]))
            self.labels.append(("phase", (x + half + 10, plane_top), half))
            side = min(half, body[1])
            self.portrait.layout((x + half + 10 + (half - side) // 2, body[0] + (body[1] - side) // 2, side, side))

        # графики слева
        lx = m + int(u * 3.2)
        lw = (px - m - lx - 30) if self.app.panel_open else (w - 48 - lx)
        title_h, ticks_h, pgap = int(u * 1.5), int(u * 1.5), int(u * 0.6)
        weights = (1.0, 1.0, 1.15, 1.4)
        free = h - 2 * m - 4 * (title_h + ticks_h) - 3 * pgap
        toolbar_h = int(u*2.1)
        self.b_loupe.rect = pygame.Rect(lx,m,int(u*7),toolbar_h)
        self.b_view.rect = pygame.Rect(lx+int(u*7.4),m,int(u*11),toolbar_h)
        status_x = self.b_view.rect.right+u
        self.status_rect = pygame.Rect(status_x,m,max(1,lx+lw-status_x),toolbar_h)
        free -= toolbar_h+pgap
        y = m+toolbar_h+pgap
        self.axes = []
        self.titles = []
        for wgt in weights:
            ph = int(free * wgt / sum(weights))
            self.titles.append((lx, y))
            self.axes.append(Axes((lx, y + title_h, lw, ph), (0, 1), (-1, 1)))
            y += title_h + ph + ticks_h + pgap

    # ---------- рисование ----------

    def draw(self, surf):
        w, h = surf.get_size()
        u = self.u
        pygame.draw.rect(surf, theme.PANEL, self.panel, border_radius=8)
        pygame.draw.rect(surf, theme.BORDER, self.panel, 1, border_radius=8)
        # заголовки двух маленьких окон (с ограничением ширины) рисуются одним размером
        small = min([fit_text(t(key), int(u * 0.9), limit[0], bold=True) for key, _, *limit in self.labels if limit],
                    default=int(u * 0.9))
        for key, pos, *limit in self.labels:
            text = t(key)
            scale = self.label_scale.get(key, 1.0)
            size = int(small * scale) if limit else fit_text(text, int(u * 1.05 * scale),
                                                              self.panel.right - 12 - pos[0], bold=True)
            draw_text(surf, text, pos, size, theme.FG, bold=True)
        super().draw(surf)
        self.portrait.draw(surf, self.cursor, self._cursor_range()[0])
        self._draw_info(surf)
        self._draw_process(surf)
        self._draw_correlation(surf)
        self._draw_status(surf)
        if self.zoom_drag:
            _,a,b = self.zoom_drag
            rect = pygame.Rect(min(a[0],b[0]),min(a[1],b[1]),abs(b[0]-a[0]),abs(b[1]-a[1]))
            layer = pygame.Surface(rect.size,pygame.SRCALPHA)
            layer.fill(theme.PROCESS+(35,))
            surf.blit(layer,rect)
            pygame.draw.rect(surf,theme.PROCESS,rect,2)

    def _fmt_lag(self, lag):
        if self.mode == "d":
            return str(lag)
        x = lag / S
        return "0" if lag == 0 else f"{x:g}π"

    def _draw_info(self, surf):
        u = self.u
        x, y = self.info_pos
        fs = int(u * 0.95)
        lag, _ = self.current_lag()
        lines = []
        if lag is not None:
            key = "info_value_d" if self.mode == "d" else "info_value_c"
            lines.append(t(key, k=lag, tau=self._fmt_lag(lag), v=theme.num(self._value(lag)),
                           t=theme.num(self.theory[lag])))
        else:
            lines.append("")
        lines.append(t("info_stats_" + self.mode, mean=theme.num(self.est.mean), var=theme.num(self.est.var),
                       delta=theme.num(self.params.delta)))

        width = self.panel.right - 12 - x
        for line in lines:
            draw_text(surf, line, (x, y), fit_text(line, fs, width), theme.FG)
            y += int(u * 1.35)

    def _visible_range(self):
        start, length = self.view[self.mode]
        return start, length

    def _draw_series(self, surf, ax, values, offset, first, last, color, normalize=False, stems=True):
        """Рисует отсчёты values[first:last] в позициях (i - offset)."""
        mean = self.est.mean
        points = [((i-offset)/self.unit, (values[i]-mean)/self.sigma if normalize else values[i])
                  for i in range(max(first,0),min(last,len(values)))]
        if self.mode == "d":
            point_process(surf,ax,points,color,secondary=color==theme.SHIFTED,stems=stems)
        else:
            curve_line(surf,color,False,[ax.point(x,y) for x,y in points])

    def _draw_process(self, surf):
        u = self.u
        fs = int(u * 0.85)
        start, length = self._visible_range()
        x0, x1 = start / self.unit, (start + length) / self.unit
        pad = 0.08 * (self.hi - self.lo)
        ylim = self.zoom_ylim or (self.lo - pad, self.hi + pad)
        xlabel = t("axis_n") if self.mode == "d" else t("axis_t")
        d = "d" if self.mode == "d" else "c"
        lag_now = self.shift
        tau_text = self._fmt_lag(int(round(lag_now))) if self.mode == "d" else f"{lag_now / S:.2f}π"

        # 1. исходная реализация
        ax = self.axes[0]
        ax.x0, ax.x1, ax.y0, ax.y1 = x0, x1, *ylim
        draw_text(surf, t("p1_" + d), self.titles[0], int(u * 1.0), bold=True)
        ax.frame(surf, fs, xlabel=xlabel)
        my = round(ax.py(self.est.mean))
        dashed_polyline(surf, theme.MUTED, [(ax.rect.x, my), (ax.rect.right, my)], dash=5, gap=4, width=1)
        draw_text(surf, t("g_mean_" + d), (ax.rect.right - 4, my - 2), fs, theme.MUTED,
                  anchor="bottomright")
        surf.set_clip(ax.rect.inflate(8, 8))
        self._draw_series(surf, ax, self.data, 0, start, start + length + 1, theme.PROCESS)
        self._draw_cursor(surf, ax)
        self._draw_pair_marker(surf,ax,False)
        surf.set_clip(None)

        # 2. сдвинутая копия
        ax = self.axes[1]
        ax.x0, ax.x1, ax.y0, ax.y1 = x0, x1, *ylim
        key = "p2_d" if self.mode == "d" else "p2_c"
        draw_text(surf, t(key, k=tau_text, tau=tau_text), self.titles[1], int(u * 1.0), bold=True,
                  color=theme.SHIFTED)
        ax.frame(surf, fs, xlabel=xlabel)
        surf.set_clip(ax.rect.inflate(8, 8))
        first = start + int(lag_now)
        self._draw_series(surf, ax, self.data, lag_now, first, first + length + 2, theme.SHIFTED)
        surf.set_clip(None)
        self._draw_shift_arrow(surf, ax, lag_now)
        self._draw_pair_marker(surf,ax,True)

        # 3. наложение и произведения
        ax = self.axes[2]
        lim = min(self.dev_max, 4.0) * 1.1
        ax.x0, ax.x1, ax.y0, ax.y1 = x0, x1, -lim, lim
        if self.zoom_ylim:
            ax.y0,ax.y1 = [(v-self.est.mean)/self.sigma for v in self.zoom_ylim]
        draw_text(surf, t("p3_" + d), self.titles[2], int(u * 1.0), bold=True)
        ax.frame(surf, fs, xlabel=xlabel)
        lag, alpha = self.current_lag()
        surf.set_clip(ax.rect)
        if lag is not None and alpha > 0:
            layer = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            c = self.est.centered
            var = max(self.est.var,1e-30)
            n_vis = length
            bar_w = max(1, int(ax.rect.width / n_vis * (0.6 if self.mode == "d" else 1.0)) + (0 if self.mode == "d" else 1))
            if self.mode == "d":
                bar_w = min(round(2*config.window.process_marker_radius),bar_w)
            step = max(1, int(n_vis / ax.rect.width))
            zero = ax.py(0)
            stage, active, count, _ = self._stage()
            indices = range(start, min(start+length+1,len(c)-lag),step)
            if self.explain and self.phase is not None and count is not None:
                indices = self.preview[:count]
            for i in indices:
                prod = c[i] * c[i + lag] / var
                px = ax.px(i / self.unit)
                py = ax.py(ax.clip_y(prod))
                color = theme.POSITIVE if prod >= 0 else theme.NEGATIVE
                top, bot = min(py, zero), max(py, zero)
                rect = pygame.Rect(int(px - bar_w / 2), int(top), bar_w, max(1, int(bot - top)))
                pygame.draw.rect(layer, color + (120,), rect)
            layer.set_alpha(int(255 * alpha))
            surf.blit(layer, (0, 0))
        self._draw_series(surf, ax, self.data, 0, start, start + length + 1, theme.PROCESS, normalize=True,
                          stems=False)
        first = start + int(lag_now)
        self._draw_series(surf, ax, self.data, lag_now, first, first + length + 2, theme.SHIFTED, normalize=True,
                          stems=False)
        if self.explain and self.phase is not None:
            stage,active,_,_ = self._stage()
            if active is not None:
                x = active/self.unit
                y1 = self.est.centered[active]/self.sigma
                y2 = self.est.centered[active+lag]/self.sigma
                point_marker(surf,theme.PROCESS,ax.point(x,y1),6,2)
                point_marker(surf,theme.SHIFTED,ax.point(x,y2),8,2)
        surf.set_clip(None)
        items = [("circle", theme.PROCESS, t("legend_orig")), ("diamond", theme.SHIFTED, t("legend_shift")),
                 ("rect", theme.POSITIVE, t("legend_pos")), ("rect", theme.NEGATIVE, t("legend_neg"))]
        draw_legend(surf, items, ax.rect.right - 6, ax.rect.y + 5, fs)

    def _draw_status(self, surf):
        lag, _ = self.current_lag()
        if lag is not None:
            stage,active,_,_ = self._stage()
            if self.explain and self.phase is not None and stage in ("pair","product"):
                product = self.est.centered[active]*self.est.centered[active+lag]/max(self.est.var,1e-30)
                txt = t("explain_"+stage, n=active, value=theme.num(product))
            elif self.explain and self.phase is not None and stage == "shift":
                txt = t("explain_shift")
            else:
                txt = t("explain_full", n=len(self.data)-lag, value=theme.num(self._value(lag)))
            size = fit_text(txt,int(self.u*.95),self.status_rect.width,bold=True)
            draw_text(surf,txt,self.status_rect.midleft,size,theme.FG,anchor="midleft",bold=True)

    def _draw_pair_marker(self, surf, ax, shifted):
        if not self.explain or self.phase is None:
            return
        _,active,_,_ = self._stage()
        if active is None:
            return
        lag = self.lags[self.built] if shifted else 0
        x,y = ax.point(active/self.unit,self.data[active+lag])
        old = surf.get_clip()
        surf.set_clip(ax.rect)
        point_marker(surf,theme.SHIFTED if shifted else theme.PROCESS,(x,y),10,2)
        surf.set_clip(old)

    def _draw_cursor(self, surf, ax):
        """Отмечает на графике процесса то место, где сейчас точка на фазовой плоскости."""
        n = int(self.cursor)
        if self.mode == "d":
            point_marker(surf, theme.CURSOR, (ax.px(n), ax.py(self.ys[n])), 7, 2)
        else:
            u = (self.cursor - n) * math.pi
            v = self.ys[n] * nm.shape(u, self.params.delta)
            px = ax.px(self.cursor)
            graph_line(surf, theme.CURSOR, (px, ax.rect.y), (px, ax.rect.bottom), 1)
            point_marker(surf, theme.CURSOR, (px, ax.py(v)), 5)

    def _draw_shift_arrow(self, surf, ax, lag):
        if lag < 0.5:
            return
        y = ax.rect.y + 8
        xa = ax.rect.x + 10
        xb = xa + (ax.px(lag / self.unit) - ax.px(0))
        xb = min(xb, ax.rect.right - 10)
        graph_line(surf, theme.SHIFTED, (xa, y), (xb, y), 2)
        pygame.draw.polygon(surf, theme.SHIFTED, [(xa, y), (xa + 7, y - 4), (xa + 7, y + 4)])

    def _draw_correlation(self, surf):
        u = self.u
        fs = int(u * 0.85)
        ax = self.axes[3]
        xmax = self.lags[-1] / self.unit
        ax.x0, ax.x1, ax.y0, ax.y1 = -0.5 * self.lags[1] / self.unit, xmax + 0.5 * self.lags[1] / self.unit, -1.05, 1.05
        d = "d" if self.mode == "d" else "c"
        draw_text(surf, t("p4_" + d), self.titles[3], int(u * 1.0), bold=True)
        ax.frame(surf, fs, xlabel=t("axis_k") if self.mode == "d" else t("axis_tau"), yticks=4)
        spacing = ax.px(self.lags[1] / self.unit) - ax.px(0)
        bw = max(2, int(spacing * 0.6))
        zero = ax.py(0)

        def bar(lag, value, color):
            px = ax.px(lag / self.unit)
            py = ax.py(value)
            top, bot = min(py, zero), max(py, zero)
            pygame.draw.rect(surf, color, (int(px - bw / 2), int(top), bw, max(1, int(bot - top))))

        for lag in self.lags[:self.built]:
            bar(lag, self._value(lag), theme.BAR)
        if self.phase is not None:
            lag = self.lags[self.built]
            grow = self._stage()[3]
            if grow > 0:
                bar(lag, self._value(lag) * grow, theme.BAR_CURRENT)
            px = ax.px(self.shift / self.unit)
            graph_line(surf, theme.SHIFTED, (px, ax.rect.y), (px, ax.rect.bottom), 1)

        # теория
        if self.mode == "d":
            pts = [ax.point(k, self.theory[k]) for k in self.lags]
            dashed_polyline(surf, theme.THEORY, pts, width=2)
            for p in pts:
                point_marker(surf, theme.THEORY, p, 3)
        else:
            pts = [ax.point(j / S, self.theory[j]) for j in range(len(self.theory))]
            dashed_polyline(surf, theme.THEORY, pts, width=2)

        items = [("rect", theme.BAR, t("legend_exp")), ("dash", theme.THEORY, t("legend_theory"))]
        draw_legend(surf, items, ax.rect.right - 6, ax.rect.y + 5, fs)

    # ---------- для автоматической проверки ----------

    def test_setup(self, mode=None, preset=None, build=False, steps=0):
        if mode:
            self.mode_sel.value = mode
            self._set_mode(mode)
        if preset and preset in nm.PRESETS:
            self.preset_sel.value = preset
            self._set_preset(preset)
        if build:
            self._build_all()
        for _ in range(steps):
            self._begin_step()
            self._finish_step()
        if steps:
            self._begin_step()
            self.phase = 0.85
            self.shift = float(self.lags[self.built])
