"""Контракт представления движения без записи config/design и без сборки."""
import math
import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from ncorr import config, i18n, theme
from ncorr.physics import neimark as nm
from ncorr.screens import motion
from ncorr.ui import plot


class MotionPresentationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    def setUp(self):
        translations = patch.dict(i18n.STRINGS, {"motion_scale": ("Масштаб: ×{scale}", "Scale: ×{scale}")})
        translations.start()
        self.addCleanup(translations.stop)
        self.screen = motion.MotionScreen(SimpleNamespace(tabs=Mock(), panel_open=True))
        self.screen.layout(1280, 720)
        self.surf = pygame.Surface((1280, 720))

    def assert_bounded(self):
        s = self.screen
        self.assertGreater(s.params.gamma, 1)
        lo, hi = s.params.h_range()
        self.assertLessEqual(lo, s.params.h)
        self.assertLessEqual(s.params.h, hi)
        self.assertLessEqual(s.params.lower, s.v0)
        self.assertLessEqual(s.v0, nm.A)
        self.assertEqual(s.s_gamma.value, s.params.gamma)
        self.assertEqual(s.s_h.value, s.params.h)
        self.assertEqual(s.s_v0.value, s.v0)
        self.assertEqual((s.s_h.vmin, s.s_h.vmax), (lo, hi))
        self.assertEqual((s.s_v0.vmin, s.s_v0.vmax), (s.params.lower, nm.A))

    def test_slider_callbacks_keep_bounded_parameters(self):
        for callback, values in ((self.screen._on_gamma, (0.5, 1, 1.5, 4, 20)),
                                 (self.screen._on_h, (-100, 0, 1, 100)),
                                 (self.screen._on_v0, (-100, 0, 100))):
            for value in values:
                with self.subTest(callback=callback.__name__, value=value):
                    callback(value, False)
                    self.assert_bounded()
                    self.assertIsNone(self.screen.scenario)

    def test_manual_boundary_settings_stay_bounded_after_many_crossings(self):
        s = self.screen
        for gamma in (1.05,1.2,1.5,2,2.618033988749895,3.8,4):
            lo,hi = nm.Params(gamma,0).h_range()
            for h in (lo,(lo+hi)/2,hi):
                for v0 in (-math.sqrt(gamma),-.3,0,.3,1):
                    with self.subTest(gamma=gamma,h=h,v0=v0):
                        s._on_gamma(gamma,True)
                        s._on_h(h,True)
                        s._on_v0(v0,True)
                        s.motion.advance(500*math.pi)
                        self.assertFalse(s.motion.escaped)
                        self.assertTrue(all(s.params.lower-1e-10 <= half.y <= 1+1e-10
                                            for half in s.motion.halves))

    def test_free_preset_survives_until_manual_parameter_change(self):
        for name in ("_on_gamma", "_on_h", "_on_v0"):
            self.screen._set_scenario("free")
            self.assertEqual(self.screen.params.h, 0)
            self.assertEqual(self.screen.v0, motion.SCENARIOS["free"][1])
            self.screen._on_speed(5, True)
            self.assertEqual(self.screen.params.h, 0)
            getattr(self.screen, name)(1.5, True)
            self.assert_bounded()

    def test_gamma_respects_config_with_physical_intersection(self):
        with patch.object(config.motion, "gamma_min", 1.2), \
                patch.object(config.motion, "gamma_max", 2):
            self.screen._on_gamma(10, True)
            self.assertEqual(self.screen.params.gamma, 2)
            self.screen._on_gamma(0, True)
            self.assertEqual(self.screen.params.gamma, 1.2)
            self.assert_bounded()

    def test_escape_limit_is_local_and_inherited_by_restarted_twin(self):
        original = nm.Motion.LIMIT
        s = self.screen
        s._set_scenario("free")
        self.assertEqual(s.motion.LIMIT, 8 * s.initial_ext)
        s._set_twin(next(iter(motion.TWINS)))
        self.assertEqual(s.twin.LIMIT, s.motion.LIMIT)
        s._advance(1000 * math.pi)
        self.assertTrue(s.motion.escaped)
        self.assertFalse(s.running)
        self.assertLess(s.motion.crossings, 30)
        self.assertEqual(nm.Motion.LIMIT, original)
        self.assertEqual(nm.Motion(s.params, s.v0).LIMIT, original)
        s._set_twin(next(iter(motion.TWINS)))
        self.assertEqual(s.twin.LIMIT, s.motion.LIMIT)

    def test_free_escape_checks_state_between_crossings(self):
        s = self.screen
        s._set_scenario("free")
        s.motion.current.y = s.motion.LIMIT * 0.999
        s._advance(0.05)
        self.assertTrue(s.motion.escaped)
        self.assertEqual(s.motion.crossings, 0)

    def test_mass_and_spring_shrink_to_visible_minima(self):
        s = self.screen
        initial = s._oscillator_sizes()
        s.ext *= 4
        smaller = s._oscillator_sizes()
        self.assertLess(smaller[0], initial[0])
        self.assertLess(smaller[1], initial[1])
        s.ext *= 1000
        self.assertEqual(s._oscillator_sizes(), (6, 2))
        with patch.object(motion, "t", wraps=motion.t) as translate:
            s._draw_oscillator(self.surf)
        self.assertTrue(any(c.args[0] == "motion_scale" for c in translate.call_args_list))

    def test_lower_axes_are_aligned_across_sizes_and_panel_modes(self):
        s = self.screen
        for size in ((1024, 640), (1280, 720), (1920, 1080), (2560, 1440)):
            for panel in (True, False):
                s.app.panel_open = panel
                s.layout(*size)
                s._draw_map(self.surf)
                with patch.object(plot, "point_process", create=True):
                    s._draw_twins(self.surf)
                self.assertEqual(s.map_ax.rect.top, s.seq_ax.rect.top)
                self.assertEqual(s.map_ax.rect.height, s.seq_ax.rect.height)
                for y in (-s.ext, 0, s.ext):
                    self.assertEqual(s.map_ax.py(y), s.seq_ax.py(y))

    def test_sequence_uses_shared_renderer_with_physical_points(self):
        s = self.screen
        s._set_twin(next(iter(motion.TWINS)))
        s._advance(3 * math.pi)
        with patch.object(plot, "point_process", create=True) as render, \
                patch.object(motion, "curve_line") as line, \
                patch.object(motion, "dashed_polyline") as dashed:
            s._draw_twins(self.surf)
        self.assertEqual(render.call_count, 2)
        main, twin = render.call_args_list
        self.assertEqual(main.args[2], [(n, a) for n, a, _ in s.track])
        self.assertEqual(twin.args[2], [(n, b) for n, _, b in s.track])
        self.assertEqual(main.args[3], theme.PROCESS)
        self.assertEqual(twin.args[3], theme.TWIN)
        self.assertTrue(main.kwargs["stems"])
        self.assertTrue(twin.kwargs["secondary"])
        self.assertEqual(main.kwargs["highlight"], main.args[2][-1])
        self.assertEqual(twin.kwargs["highlight"], twin.args[2][-1])
        line.assert_not_called()
        dashed.assert_not_called()

    def test_lower_projection_joins_latest_pair_and_sequence_sample(self):
        s = self.screen
        s._advance(3 * math.pi + 0.2)
        s._draw_map(self.surf)
        with patch.object(plot, "point_process", create=True):
            s._draw_twins(self.surf)
        a, b = s.motion.pairs()[-1]
        with patch.object(motion, "dashed_polyline") as dashed:
            s._draw_sequence_projection(self.surf)
            expected = [s.map_ax.point(a, b), s.seq_ax.point(s.motion.crossings, b)]
            self.assertEqual(dashed.call_args.args[2], expected)
            self.assertEqual(expected[0][1], expected[1][1])
            s.show_projection = False
            dashed.reset_mock()
            s._draw_sequence_projection(self.surf)
            dashed.assert_not_called()

    def test_no_projection_before_first_pair(self):
        with patch.object(motion, "dashed_polyline") as dashed:
            self.screen._draw_sequence_projection(self.surf)
        dashed.assert_not_called()

    def test_track_is_bounded_even_when_track_changes_during_run(self):
        s = self.screen
        with patch.object(motion, "TRACK", 9):
            s._advance(200 * math.pi)
            self.assertEqual(len(s.track), 9)
            self.assertEqual(s.track[-1][0], s.motion.crossings)
            with patch.object(motion, "TRACK", 5), \
                    patch.object(plot, "point_process", create=True) as render:
                s._draw_twins(self.surf)
                self.assertEqual(len(s.track), 5)
                self.assertEqual(len(render.call_args.args[2]), 5)
                s._advance(50 * math.pi)
                self.assertEqual(len(s.track), 5)


if __name__ == "__main__":
    unittest.main()
