"""Пошаговое объяснение, независимость оценки от анимации и согласованная лупа."""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

from ncorr import config, resources
from ncorr.screens.demo import DemoScreen


class DemoPresentationTest(unittest.TestCase):
    def setUp(self):
        pygame.font.init()
        resources.clear_cache()
        tabs = Mock()
        tabs.handle.return_value = False
        self.screen = DemoScreen(SimpleNamespace(tabs=tabs, panel_open=True))
        self.screen.layout(1366, 768)

    def test_explanation_waits_when_paused_and_steps_through_pairs(self):
        s = self.screen
        s._step_click()
        s.update(100)
        self.assertEqual(s.phase, 0)
        s._step_click()
        self.assertEqual(s._stage()[:2], ("pair", 0))
        s._step_click()
        self.assertEqual(s._stage()[:3], ("product", 0, 1))
        self.assertEqual(s.built, 0)
        for _ in range(2*config.demo.preview_pairs+2):
            if s.built:
                break
            s._step_click()
        self.assertEqual(s.built, 1)
        self.assertEqual(s._value(0), 1)

    def test_auto_explanation_respects_speed_for_stage_and_cursor(self):
        s = self.screen
        s._begin_step()
        s.running = True
        s.speed = 0.05
        s.update(1)
        slow_phase, slow_cursor = s.phase, s.cursor
        s._reset()
        s.cursor = 0
        s._begin_step()
        s.running = True
        s.speed = 1
        s.update(1)
        self.assertAlmostEqual(s.phase, 20*slow_phase)
        self.assertAlmostEqual(s.cursor, 20*slow_cursor)
        s.running = False
        phase = s.phase
        s.update(10)
        self.assertEqual(s.phase, phase)

    def test_preview_does_not_change_full_sample_estimate(self):
        s = self.screen
        expected = s.est.normalized(3)
        s.built = 3
        s._begin_step()
        self.assertEqual(len(s.preview), config.demo.preview_pairs)
        s.phase = .5
        s._stage()
        s.view["d"] = [120, 15]
        s._finish_step()
        self.assertAlmostEqual(s.values[3], expected)

    def test_loupe_aligns_first_three_plots_and_resets(self):
        s = self.screen
        surf = pygame.Surface((1366,768))
        s._draw_process(surf)
        ax = s.axes[1]
        s._apply_zoom(1, (ax.px(12), ax.py(.6)), (ax.px(24), ax.py(-.6)))
        self.assertEqual(s.view["d"][0], 12)
        self.assertEqual(s.view["d"][1], 12)
        s._draw_process(surf)
        self.assertEqual(s.axes[0].x0, s.axes[2].x0)
        self.assertEqual(s.axes[0].x1, s.axes[2].x1)
        self.assertEqual(s.axes[0].y0, s.axes[1].y0)
        self.assertAlmostEqual(s.axes[2].y0, (s.axes[0].y0-s.est.mean)/s.sigma)
        s._reset_view()
        self.assertIsNone(s.zoom_ylim)
        self.assertEqual(s.view["d"], [0,config.demo.view_d])

    def test_loupe_can_draw_immediately_before_cursor_update(self):
        s = self.screen
        surf = pygame.Surface((1366,768))
        s._draw_process(surf)
        ax = s.axes[0]
        s._apply_zoom(0,(ax.px(10),ax.py(.6)),(ax.px(25),ax.py(-.6)))
        # При старом курсоре 0 и новом начале 10 мини-портрет раньше падал.
        s.portrait.draw(surf,s.cursor,s._cursor_range()[0])
        self.assertEqual(s.cursor, 0)

    def test_cli_snapshot_keeps_copy_and_products_at_same_lag(self):
        s = self.screen
        s.test_setup(steps=3)
        lag,_ = s.current_lag()
        self.assertEqual(s.shift,lag)
        self.assertEqual(s.built,3)

    def test_loupe_events_select_without_panning(self):
        s = self.screen
        s._draw_process(pygame.Surface((1366,768)))
        ax = s.axes[0]
        a,b = (ax.px(10), ax.py(.5)), (ax.px(25), ax.py(-.5))
        s._toggle_loupe()
        s.handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=a))
        s.handle(pygame.event.Event(pygame.MOUSEMOTION,pos=b))
        s.handle(pygame.event.Event(pygame.MOUSEBUTTONUP,button=1,pos=b))
        self.assertIsNone(s._pan)
        self.assertIsNone(s.zoom_drag)
        self.assertFalse(s.zoom_select)
        self.assertLessEqual(s.view["d"][1], 16)


if __name__ == "__main__":
    unittest.main()
