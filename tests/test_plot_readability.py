"""Маркеры не скрывают знак малого значения, подписи не перекрывают числа."""
import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

from ncorr import resources, theme
from ncorr.ui import widgets
from ncorr.ui.plot import Axes, point_process


class PlotReadabilityTest(unittest.TestCase):
    def setUp(self):
        pygame.display.init()
        pygame.font.init()
        resources.clear_cache()

    def test_small_markers_stay_on_their_side_of_zero(self):
        ax = Axes((20,20,200,200),(0,2),(-1,1))
        for secondary in (False,True):
            for value in (-.03,.03):
                surf = pygame.Surface((240,240))
                surf.fill(theme.BG)
                point_process(surf,ax,[(1,value)],theme.PROCESS,secondary=secondary,stems=False)
                painted = [(x,y) for x in range(110,131) for y in range(110,131)
                           if surf.get_at((x,y))[:3] != theme.BG]
                self.assertTrue(painted)
                self.assertLessEqual(max(x for x,y in painted)-min(x for x,y in painted),6)
                if value>0:
                    self.assertLess(max(y for x,y in painted),ax.py(0))
                else:
                    self.assertGreater(min(y for x,y in painted),ax.py(0))

    def test_gamma_slider_reserves_space_for_value(self):
        previous = widgets.DRAWN
        try:
            for width in (250,300,370):
                for size in (15,20,25):
                    widgets.DRAWN=[]
                    s=widgets.Slider(lambda:'γ — рост амплитуды за период',1,4,2.618,
                                     lambda *_:None,fmt=lambda _: '2.618',font_size=size)
                    s.layout((10,10,width,65))
                    s.draw(pygame.Surface((450,100)))
                    label,value=widgets.DRAWN[:2]
                    self.assertLess(label[0].right,value[0].left)
        finally:
            widgets.DRAWN=previous
