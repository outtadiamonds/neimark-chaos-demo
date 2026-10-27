"""Прогон интерфейса без окна: нажимаем все кнопки, двигаем ползунки, меняем язык и размер."""
import os
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame  # noqa: E402

from ncorr import i18n  # noqa: E402
from ncorr.app import App  # noqa: E402


def click(app, pos):
    app._handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    app._handle(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos))


def drag(app, a, b):
    app._handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=a))
    app._handle(pygame.event.Event(pygame.MOUSEMOTION, pos=b, rel=(b[0] - a[0], b[1] - a[1]), buttons=(1, 0, 0)))
    app._handle(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=b))


def frames(app, n=5, dt=0.05):
    screen = app.screens[app.active]
    for _ in range(n):
        screen.update(dt)
        app.screen.fill((255, 255, 255))
        screen.draw(app.screen)
        app.lang_button.draw(app.screen)


class UiSmokeTest(unittest.TestCase):
    def setUp(self):
        from ncorr import config, design
        # тесты не трогают настоящие assets/config.json и design.json: числа по умолчанию, оформление пустое
        config.FILE = "config-test.json"
        design.FILE = "design-test.json"
        self._remove_test_files()
        i18n.set_lang("ru")
        self.app = App(size=(1280, 720))

    def tearDown(self):
        pygame.quit()
        self._remove_test_files()

    @staticmethod
    def _remove_test_files():
        from ncorr import config, design
        for path in (config.file_path(), design.file_path()):
            if os.path.exists(path):
                os.remove(path)

    def test_all_screens_and_language(self):
        app = self.app
        for name in ("menu", "motion", "theory", "authors", "demo"):
            app.show(name)
            for lang in ("ru", "en"):
                i18n.set_lang(lang)
                frames(app, 2)
        click(app, app.lang_button.rect.center)
        self.assertEqual(i18n.lang(), "ru")

    def test_menu_buttons(self):
        app = self.app
        for i, target in enumerate(("motion", "theory", "authors")):
            app.show("menu")
            click(app, app.screens["menu"].buttons[i].rect.center)
            self.assertEqual(app.active, target)
            frames(app, 2)

    def test_demo_interaction(self):
        app = self.app
        app.show("demo")
        demo = app.screens["demo"]
        click(app, demo.b_step.rect.center)
        frames(app, 30)
        self.assertGreaterEqual(demo.built, 1)
        click(app, demo.b_run.rect.center)
        frames(app, 60)
        click(app, demo.b_run.rect.center)
        self.assertFalse(demo.running)
        # ползунки и плоскость параметров
        tr = demo.s_gamma.track
        drag(app, (tr.x + tr.width // 2, tr.centery), (tr.x + tr.width // 3, tr.centery))
        self.assertEqual(demo.preset_sel.value, "custom")
        tr = demo.s_h.track
        drag(app, (tr.x + 5, tr.centery), (tr.right - 5, tr.centery))
        self.assertTrue(demo.params.is_chaotic())
        ax = demo.plane.axes.rect
        click(app, (ax.x + 5, ax.y + 5))  # вне области ABC: точка прижимается к границе
        self.assertTrue(demo.params.is_chaotic())
        tr = demo.s_n.track
        drag(app, (tr.right - 3, tr.centery), (tr.x + 3, tr.centery))
        self.assertEqual(len(demo.ys), 1000)
        # все пресеты в обоих режимах, построение целиком
        for mode_btn in demo.mode_sel.buttons:
            click(app, mode_btn.rect.center)
            for preset_btn in demo.preset_sel.buttons:
                click(app, preset_btn.rect.center)
                click(app, demo.b_all.rect.center)
                frames(app, 40)
                self.assertEqual(demo.built, len(demo.lags))
        # масштаб и прокрутка
        pygame.mouse.set_pos(demo.axes[0].rect.center)
        for y in (3, -6, 10):
            app._handle(pygame.event.Event(pygame.MOUSEWHEEL, x=0, y=y, flipped=False))
        drag(app, demo.axes[1].rect.center, (demo.axes[1].rect.x + 5, demo.axes[1].rect.centery))
        frames(app, 3)
        click(app, demo.b_reset.rect.center)
        self.assertEqual(demo.built, 0)
        click(app, demo.b_back.rect.center)
        self.assertEqual(app.active, "menu")

    def test_motion_interaction(self):
        app = self.app
        app.show("motion")
        mo = app.screens["motion"]
        self.assertTrue(mo.running)
        frames(app, 30)
        for seg in (mo.sc_row1, mo.sc_row2):
            for b in seg.buttons:
                click(app, b.rect.center)
                frames(app, 20, dt=0.2)
        self.assertEqual(mo.scenario, "free")
        for s in (mo.s_gamma, mo.s_h, mo.s_v0, mo.s_speed):
            tr = s.track
            drag(app, (tr.x + tr.width // 2, tr.centery), (tr.x + tr.width // 3, tr.centery))
        self.assertIsNone(mo.scenario)
        click(app, mo.b_step.rect.center)
        self.assertFalse(mo.running)
        self.assertGreaterEqual(mo.motion.crossings, 1)
        for b in (mo.b_proj, mo.b_sect, mo.b_proj, mo.b_sect, mo.b_run, mo.b_reset):
            click(app, b.rect.center)
            frames(app, 3)
        # без ударов движение уходит на бесконечность и останавливается
        click(app, mo.sc_row2.buttons[1].rect.center)
        mo.speed = 50.0
        frames(app, 200, dt=0.1)
        self.assertTrue(mo.motion.escaped)
        self.assertFalse(mo.running)
        # точка H: близкая траектория расходится (случайность, точка бифуркации)
        click(app, mo.sc_row1.buttons[0].rect.center)
        for b in mo.twin_sel.buttons:
            click(app, b.rect.center)
            frames(app, 2)
        self.assertEqual(mo.twin_key, "3")  # третье ε из config.json — 10⁻⁸
        mo.speed = 20.0
        frames(app, 60, dt=0.1)
        self.assertIsNotNone(mo.split_n)
        click(app, mo.twin_sel.buttons[0].rect.center)
        self.assertIsNone(mo.twin)
        frames(app, 3)

    def test_tabs(self):
        # из меню «Демонстрация» открывает вкладку движения; переключатель сверху ведёт на корреляцию и обратно
        app = self.app
        click(app, app.screens["menu"].buttons[0].rect.center)
        self.assertEqual(app.active, "motion")
        mo, demo = app.screens["motion"], app.screens["demo"]
        click(app, mo.sc_row1.buttons[1].rect.center)  # точка E на вкладке движения
        click(app, app.tabs.buttons[1].rect.center)
        self.assertEqual(app.active, "demo")
        self.assertEqual(app.tabs.value, "demo")
        self.assertEqual(demo.preset_sel.value, "E")  # параметры перешли вместе с переключением
        frames(app, 3)
        click(app, demo.preset_sel.buttons[0].rect.center)  # своя точка на вкладке корреляции
        click(app, app.tabs.buttons[0].rect.center)
        self.assertEqual(app.active, "motion")
        click(app, app.tabs.buttons[1].rect.center)
        self.assertEqual(demo.preset_sel.value, "H")  # на движении ничего не меняли — выбор сохранился
        frames(app, 3)
        click(app, demo.b_back.rect.center)
        self.assertEqual(app.active, "menu")

    def test_dev_mode(self):
        # конструктор: сдвиг мышью, шрифт, текст, цвет, отмена, сохранение и загрузка design.json
        from ncorr import design, theme
        app = self.app
        try:
            design.data = design.empty()
            design.apply_global()
            app.show("motion")
            app._handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F12, mod=0, unicode=""))
            dev = app.dev
            dev.auto_export = False
            dev.toolbar_pos = (0, 0)  # панель — в угол, чтобы не закрывала графики
            self.assertTrue(dev.active)
            mo = app.screens["motion"]
            before = mo.b_run.rect.copy()
            u = dev._u()
            drag(app, before.center, (before.centerx + 3 * u, before.centery - 2 * u))
            self.assertEqual(dev.selected, "motion.b_run")
            self.assertEqual(mo.b_run.rect.topleft, (before.x + 3 * u, before.y - 2 * u))
            self.assertFalse(mo.running is None)
            dev._scale_font(1.1)
            self.assertGreater(mo.b_run.font_size, int(u * 1.05))
            # текст кнопки «Заново»
            click(app, mo.b_reset.rect.center)
            self.assertEqual(dev.text_key, "reset")
            dev._edit_selected_text()
            for ch in "!!":
                app._handle(pygame.event.Event(pygame.TEXTINPUT, text=ch))
            app._handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode=""))
            self.assertEqual(i18n.t("reset"), "Заново!!")
            # заголовок раздела тоже двигается
            label = [it for it in design.items(app, "motion") if it.id == "motion.label.sec_twin"][0]
            pos = label.rect(u).center
            drag(app, pos, (pos[0], pos[1] + u))
            self.assertEqual(design.data["widgets"]["motion.label.sec_twin"]["dy"], 1.0)
            # цвет
            dev._open("colors")
            dev._pick_color("SHIFTED")
            dev.sliders[0].value = 200
            dev._on_rgb(200, True)
            self.assertEqual(theme.SHIFTED[0], 200)
            dev.modal = None
            frames(app, 2)
            dev.draw(app.screen)
            for modal in ("texts", "colors"):
                dev._open(modal)
                dev.draw(app.screen)
            dev.modal = None
            # отмена возвращает цвет, сохранение и загрузка — всё остальное
            dev._undo()
            self.assertNotEqual(theme.SHIFTED[0], 200)
            dev._save()
            design.data = design.empty()
            design.load()
            app._layout()
            self.assertEqual(i18n.t("reset"), "Заново!!")
            self.assertEqual(mo.b_run.rect.topleft, (before.x + 3 * u, before.y - 2 * u))
            # график двигается вместе с заголовком
            app._handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F12, mod=0, unicode=""))
            app._handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F12, mod=0, unicode=""))
            ax, title = mo.map_ax.rect.copy(), mo.map_title
            drag(app, ax.center, (ax.centerx + 2 * u, ax.centery + u))
            self.assertEqual(dev.selected, "motion.graph.map")
            self.assertEqual(mo.map_ax.rect.topleft, (ax.x + 2 * u, ax.y + u))
            self.assertEqual(mo.map_title, (title[0] + 2 * u, title[1] + u))
            corner = (mo.map_ax.rect.right - 3, mo.map_ax.rect.bottom - 3)
            drag(app, corner, (corner[0] - u, corner[1]))
            self.assertEqual(mo.map_ax.rect.width, ax.width - u)
            frames(app, 2)
            app.show("demo")
            demo = app.screens["demo"]
            ax = demo.axes[3].rect.copy()
            drag(app, ax.center, (ax.centerx, ax.centery - u))
            self.assertEqual(dev.selected, "demo.graph.correlation")
            self.assertEqual(demo.axes[3].rect.y, ax.y - u)
            frames(app, 2)
            app._handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F12, mod=0, unicode=""))
            self.assertFalse(dev.active)
        finally:
            design.load()

    def test_dev_text_on_graphs(self):
        # двойной щелчок по любой надписи (подпись оси, заголовок графика, вкладка) открывает её правку
        from ncorr import design
        from ncorr.ui import widgets
        app = self.app
        design.data = design.empty()
        design.apply_global()
        app.show("motion")
        dev = app.dev
        dev.auto_export = False
        dev.toolbar_pos = (0, 0)
        dev.toggle()

        def frame():  # как в App.run: кадр с записью надписей
            widgets.DRAWN, i18n.TRACE = [], []
            app.screens[app.active].draw(app.screen)
            app.lang_button.draw(app.screen)
            dev.texts, widgets.DRAWN, i18n.TRACE = widgets.DRAWN, None, None

        def double_click(pos):
            dev.last_click = (0.0, (0, 0))
            click(app, pos)
            click(app, pos)

        def key_under(text):
            frame()
            return [r for r, s, k in dev.texts if s == text][0].center

        try:
            mo = app.screens["motion"]
            double_click(key_under("t / π"))
            self.assertEqual((dev.modal, dev.edit_key), ("text", "g_t"))
            dev.buffer = "время t / π"
            app._handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode=""))
            self.assertEqual(i18n.t("g_t"), "время t / π")
            self.assertEqual(i18n.t("axis_t"), "t / π")  # такая же подпись на другой вкладке не изменилась
            double_click(key_under(i18n.t("tab_motion")))
            self.assertEqual(dev.edit_key, "tab_motion")  # не m_osc, хотя текст тот же
            dev.modal = None
            double_click(key_under(i18n.t("count_line", n=0, hits=0)))
            self.assertEqual(dev.edit_key, "count_line")  # надпись с подставленными числами
            dev.modal = None
            # выбранный график: «текст элемента» — его заголовок
            frame()
            click(app, mo.phase_ax.rect.center)
            self.assertEqual((dev.selected, dev.text_key), ("motion.graph.phase", "m_phase"))
            dev.modal = None
            dev.toggle()
        finally:
            design.data = design.empty()
            design.apply_global()

    def test_dev_numbers(self):
        # окно «Числа»: правка числа из config.json сразу перестраивает экраны; ошибка не ломает; отмена
        from ncorr import config
        from ncorr.screens import motion
        app = self.app
        app.show("motion")
        dev = app.dev
        dev.auto_export = False
        dev.toggle()
        dev._open("numbers")
        dev.draw(app.screen)
        self.assertTrue(dev._rows)
        dev._edit_number("motion", "track")
        dev.buffer = "60"
        app._handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode=""))
        self.assertEqual(config.motion.track, 60)
        self.assertEqual(motion.TRACK, 60)
        self.assertEqual(dev.modal, "numbers")
        self.assertIsNot(app.screens["motion"], None)
        frames(app, 3)
        dev._edit_number("motion", "twins")
        dev.buffer = "0.1, 1e-4"
        app._handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode=""))
        self.assertEqual(len(app.screens["motion"].twin_sel.buttons), 3)  # «нет» и два ε
        dev._edit_number("demo", "kmax")
        dev.buffer = "abc"
        app._handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode=""))
        self.assertEqual(config.demo.kmax, 30)
        dev.modal = None
        dev._undo()
        dev._undo()
        self.assertEqual(config.motion.track, 40)
        self.assertEqual(motion.TRACK, 40)
        app.show("demo")
        frames(app, 3)
        dev.toggle()

    def test_two_editions(self):
        # версия разработчика собирает обычную копированием себя: без метки, с новым design.json, в zip
        import shutil
        import tempfile
        import zipfile
        from ncorr import packaging
        plat = packaging.platform_name()
        tmp = tempfile.mkdtemp()
        try:
            show = os.path.join(tmp, "build", packaging.NAME)
            os.makedirs(packaging.assets_dir(show))
            open(os.path.join(show, packaging.exe_name(plat)), "w").close()
            pdf = os.path.join(tmp, "pdf")
            os.makedirs(pdf)
            for lang in ("ru", "en"):
                open(os.path.join(pdf, f"theory_{lang}.pdf"), "w").close()
            zips = packaging.make_both(plat, show, os.path.join(tmp, "dist"), pdf)
            self.assertEqual(len(zips), 2)
            dev = os.path.join(tmp, "build", packaging.DEV_NAME)
            self.assertTrue(os.path.exists(os.path.join(packaging.assets_dir(dev), packaging.MARKER)))
            self.assertFalse(os.path.exists(os.path.join(packaging.assets_dir(show), packaging.MARKER)))
            # экспорт из версии разработчика (рядом с ней)
            out = os.path.join(tmp, "user")
            shutil.copytree(dev, os.path.join(out, packaging.DEV_NAME))
            folder, archive = packaging.export_show(os.path.join(out, packaging.DEV_NAME),
                                                    {"design.json": b'{"x": 1}', "config.json": b"{}"})
            self.assertEqual(folder, os.path.join(out, packaging.NAME))
            self.assertFalse(os.path.exists(os.path.join(packaging.assets_dir(folder), packaging.MARKER)))
            with open(os.path.join(packaging.assets_dir(folder), "design.json"), "rb") as f:
                self.assertEqual(f.read(), b'{"x": 1}')
            with open(os.path.join(folder, "README.txt"), encoding="utf-8") as f:
                self.assertNotIn("РАЗРАБОТЧИКА", f.read())
            with zipfile.ZipFile(archive) as z:
                names = z.namelist()
            self.assertIn(f"{packaging.NAME}/theory_ru.pdf", names)
            self.assertNotIn(f"{packaging.NAME}/_internal/assets/{packaging.MARKER}", names)
            packaging.export_show(os.path.join(out, packaging.DEV_NAME), {"design.json": b"{}"})  # повторно — поверх старой
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_resize(self):
        app = self.app
        for name in ("demo", "motion"):
            app.show(name)
            for size in ((1024, 640), (1920, 1080), (2560, 1440)):
                app.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
                app._layout()
                frames(app, 2)


if __name__ == "__main__":
    unittest.main()
