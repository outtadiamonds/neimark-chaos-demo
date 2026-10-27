import os
import sys

import pygame

from . import config, design, devmode, i18n, resources as res, theme
from .physics import neimark as nm
from .screens import demo as demo_screen, motion as motion_screen
from .ui import param_plane
from .i18n import t
from .screens.authors import AuthorsScreen
from .screens.demo import DemoScreen
from .screens.menu import MenuScreen
from .screens.motion import MotionScreen
from .screens.theory import TheoryScreen
from .ui import widgets
from .ui.widgets import Button, Segmented



def _dpi_aware():
    """Без этого Windows растягивает окно при масштабе 125-150% и картинка мылится."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


class App:
    def __init__(self, size=None, fullscreen=False, lang="ru"):
        _dpi_aware()
        os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
        if sys.platform.startswith("linux"):
            # Программный вывод окна: не зависит от OpenGL, который бывает сломан в виртуалках
            os.environ.setdefault("SDL_FRAMEBUFFER_ACCELERATION", "0")
        pygame.display.init()
        pygame.font.init()
        res.clear_cache()
        i18n.set_lang(lang)
        config.load()  # важные числа из assets/config.json
        self._refresh_config()
        design.load()  # оформление из assets/design.json (режим разработчика)
        desktop = pygame.display.get_desktop_sizes()[0]
        if size is None:
            size = (max(config.window.min_width, int(desktop[0] * 0.9)),
                    max(config.window.min_height, int(desktop[1] * 0.85)))
            size = (min(size[0], desktop[0]), min(size[1], desktop[1]))
        self.window_size = size
        self.fullscreen = False
        self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        icon = res.image("img", "cmc_logo.png")
        if icon:
            pygame.display.set_icon(pygame.transform.smoothscale(icon, (64, 64)))
        self._caption()
        self.lang_button = Button(lambda: t("lang_switch"), self._toggle_lang)
        # Две вкладки демонстрации; переключатель общий, его кладут в свои widgets оба экрана
        self.tabs = Segmented([("motion", lambda: t("tab_motion")), ("demo", lambda: t("tab_corr"))],
                              "motion", self._switch_tab)
        self._create_screens()
        self.active = "menu"
        self.running = True
        self.dev = devmode.DevMode(self) if devmode.allowed() else None
        if fullscreen:
            self.toggle_fullscreen()
        self._layout()

    def _create_screens(self):
        self.screens = {
            "menu": MenuScreen(self),
            "motion": MotionScreen(self),
            "demo": DemoScreen(self),
            "theory": TheoryScreen(self),
            "authors": AuthorsScreen(self),
        }

    @staticmethod
    def _refresh_config():
        """Передать числа из config.json модулям, которые держат их на уровне модуля."""
        nm.Motion.LIMIT = config.physics.limit
        nm.Motion.HISTORY = config.physics.history
        motion_screen.refresh()
        demo_screen.refresh()
        param_plane.refresh()

    def rebuild(self):
        """После изменения чисел (режим разработчика): пересоздать экраны с новыми числами."""
        self._refresh_config()
        active = self.active
        self._create_screens()
        self.active = active
        self.show(active)

    def _caption(self):
        pygame.display.set_caption(t("window_title"))

    def _toggle_lang(self):
        i18n.toggle()
        self._caption()

    def _switch_tab(self, name):
        if name == "demo":
            self.screens["motion"].sync_correlation()
        self.show(name)

    def _layout(self):
        w, h = self.screen.get_size()
        for s in self.screens.values():
            s.layout(w, h)
        u = theme.unit(h)
        tabs = getattr(self.screens[self.active], "tabs_rect", None)
        if tabs is not None:
            self.tabs.font_size = int(u * 1.1)
            self.tabs.layout(tabs)
        rect = getattr(self.screens[self.active], "lang_rect", None)
        if rect is None:
            rect = pygame.Rect(int(w * 0.04), h - int(h * 0.1), int(w * 0.14), int(h * 0.06))
        self.lang_button.rect = rect
        self.lang_button.font_size = int(u * (1.05 if self.active in ("demo", "motion") else 1.4))
        design.apply_layout(self, u)

    def show(self, name):
        self.active = name
        if name in ("motion", "demo"):
            self.tabs.value = name
        self.screens[name].enter()
        self._layout()

    def quit(self):
        self.running = False

    def toggle_fullscreen(self):
        if self.fullscreen:
            self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        else:
            self.window_size = self.screen.get_size()
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.fullscreen = not self.fullscreen
        self._layout()

    def _handle(self, event):
        if event.type == pygame.QUIT:
            if self.dev and self.dev.active:
                self.dev.toggle()  # закрытие окна в режиме разработчика — тоже выход: сохранить и собрать
            self.running = False
        elif event.type == pygame.WINDOWSIZECHANGED:
            self._layout()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self.toggle_fullscreen()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F12 and self.dev:
            self.dev.toggle()
        elif self.dev and self.dev.active:
            self.dev.handle(event)  # в режиме разработчика мышь и клавиатура — у конструктора
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.fullscreen:
                self.toggle_fullscreen()
            elif self.active != "menu":
                self.show("menu")
        elif not self.lang_button.handle(event):
            self.screens[self.active].handle(event)

    def run(self, frames=None, screenshot=None):
        clock = pygame.time.Clock()
        n = 0
        while self.running:
            dt = min(clock.tick(config.window.fps) / 1000.0, 0.1)
            for event in pygame.event.get():
                self._handle(event)
            screen = self.screens[self.active]
            screen.update(dt)
            recording = self.dev and self.dev.active
            widgets.DRAWN = [] if recording else None  # запомнить, где какие надписи (двойной щелчок — правка)
            i18n.TRACE = [] if recording else None
            self.screen.fill(theme.BG)
            screen.draw(self.screen)
            self.lang_button.draw(self.screen)
            if recording:
                self.dev.texts, widgets.DRAWN, i18n.TRACE = widgets.DRAWN, None, None
                self.dev.draw(self.screen)
            elif self.dev:
                self.dev.draw_status(self.screen)
            pygame.display.flip()
            n += 1
            if frames is not None and n >= frames:
                if screenshot:
                    pygame.image.save(self.screen, screenshot)
                break
        pygame.quit()
