import math
import unittest

from ncorr.physics import correlation, markov, neimark as nm


class MapTest(unittest.TestCase):
    def test_attractor_bounds(self):
        for p in (nm.PRESETS["H"], nm.PRESETS["E"], nm.Params(2.2, 1.5)):
            ys = nm.sequence(p, 20000, seed=3)
            self.assertGreaterEqual(min(ys), p.lower - 1e-9)
            self.assertLessEqual(max(ys), nm.A + 1e-9)

    def test_sign_pattern(self):
        # После положительной скорости следующая всегда отрицательна (маятник идёт назад, удара нет).
        # Две отрицательные подряд возможны только в аномальном режиме h > a: удар разворачивает скорость.
        for p in (nm.PRESETS["H"], nm.PRESETS["E"]):
            ys = nm.sequence(p, 20000, seed=2)
            pairs = list(zip(ys, ys[1:]))
            self.assertFalse(any(a > 0 and b > 0 for a, b in pairs))
            self.assertTrue(any(a < 0 and b < 0 for a, b in pairs))
            for a, b in pairs:
                if a < 0 and b < 0:
                    self.assertGreaterEqual(-p.s * a, nm.A)  # перед этим обязательно был удар
        normal = nm.Params(1.6, 0.8)  # h < a: знак чередуется строго
        ys = nm.sequence(normal, 20000, seed=2)
        self.assertTrue(all((a > 0) != (b > 0) for a, b in zip(ys, ys[1:])))

    def test_velocity_continuity(self):
        # v в конце полупериода равна -sqrt(gamma) * y (до удара)
        p = nm.Params(2.2, 1.5)
        self.assertAlmostEqual(nm.shape(3.141592653589793, p.delta), -p.s, places=12)


class MotionTest(unittest.TestCase):
    def test_crossings_follow_the_map(self):
        # движение во времени даёт ту же последовательность y_n, что и отображение step()
        p = nm.PRESETS["H"]
        mo = nm.Motion(p, 0.3)
        mo.advance(40 * 3.141592653589793 + 0.1)
        y = 0.3
        for half in mo.halves:
            self.assertAlmostEqual(half.y, y, places=9)
            y = nm.step(y, p)
        self.assertEqual(mo.crossings, 40)

    def test_frame_independence(self):
        # результат не зависит от того, какими кусками продвигать время
        p = nm.PRESETS["E"]
        a, b = nm.Motion(p, 0.42), nm.Motion(p, 0.42)
        a.advance(25.0)
        for _ in range(2500):
            b.advance(0.01)
        self.assertEqual(a.crossings, b.crossings)
        for (xa, va), (xb, vb) in ((a.state(), b.state()),):
            self.assertAlmostEqual(xa, xb, places=6)
            self.assertAlmostEqual(va, vb, places=6)

    def test_kick_jump(self):
        p = nm.PRESETS["H"]
        mo = nm.Motion(p, -0.7)  # через полпериода скорость 1.13 >= a: удар на h
        mo.advance(3.141592653589793)
        half = mo.halves[0]
        self.assertTrue(half.hit)
        self.assertAlmostEqual(half.before - half.after, p.h, places=12)
        self.assertLess(half.after, 0)  # аномальный режим: удар развернул скорость

    def test_escape_without_kicks(self):
        mo = nm.Motion(nm.Params(1.5, 0.0), 0.42)
        mo.advance(1000.0)
        self.assertTrue(mo.escaped)
        self.assertEqual(mo.hits, 0)


    def test_nearby_trajectory(self):
        # пока обе траектории на одной ветви, разница растёт ровно в √γ раз за полпериод;
        # расходятся они (одна получает удар, другая нет) примерно через ln(1/ε)/ln√γ полупериодов
        p = nm.PRESETS["H"]
        for eps in (1e-2, 1e-5, 1e-8):
            a = nm.Motion(p, 0.3)
            b = nm.Motion.near(a, eps)
            split = None
            for n in range(200):
                a.advance(math.pi)
                b.advance(math.pi)
                if a.halves[-2].hit != b.halves[-2].hit:
                    split = n + 1
                    break
                self.assertAlmostEqual(abs(a.current.y - b.current.y), eps * p.s ** (n + 1),
                                       delta=eps * 1e-6 * p.s ** n)
            expect = math.log(1 / eps) / math.log(p.s)
            self.assertIsNotNone(split)
            self.assertLess(abs(split - expect), 6)


class PartitionTest(unittest.TestCase):
    def test_markov_points_from_paper(self):
        h = markov.build_partition(nm.PRESETS["H"])
        self.assertTrue(h.exact)
        self.assertEqual(h.n, 2)
        e = markov.build_partition(nm.PRESETS["E"])
        self.assertTrue(e.exact)
        self.assertEqual(e.n, 3)
        self.assertTrue(any(abs(x) < 1e-12 for x in e.points))

    def test_density_normalized(self):
        part = markov.build_partition(nm.Params(2.2, 1.5))
        w = part.stationary()
        pts = part.points
        self.assertAlmostEqual(sum(w[i] * (pts[i + 1] - pts[i]) for i in range(part.n)), 1.0, places=9)


class CorrelationTest(unittest.TestCase):
    def check(self, p, tol):
        theory, part, moments, mean = markov.discrete_theory(p, 6)
        ys = nm.sequence(p, 200000, seed=1)
        est = correlation.Estimator(ys)
        for k in range(7):
            self.assertAlmostEqual(theory[k], est.normalized(k), delta=tol)
        s = 8
        ctheory = markov.continuous_theory(p, s, 3 * s, part.moments(5)[0], mean)
        cest = correlation.Estimator(nm.velocity(ys[:40000], p, s))
        for j in range(0, 3 * s + 1, 2):
            self.assertAlmostEqual(ctheory[j], cest.normalized(j), delta=0.03)

    def test_point_h(self):
        # Штриховая кривая рис. 5 статьи
        self.check(nm.PRESETS["H"], 0.006)

    def test_point_e(self):
        # Сплошная кривая рис. 5: R[1] = R[2] ~ -0.12, R[3] ~ +0.15
        theory = markov.discrete_theory(nm.PRESETS["E"], 3)[0]
        self.assertAlmostEqual(theory[1], theory[2], places=6)
        self.assertAlmostEqual(theory[1], -0.118, places=3)
        self.assertAlmostEqual(theory[3], 0.146, places=3)
        self.check(nm.PRESETS["E"], 0.006)

    def test_approximate_partition(self):
        self.check(nm.Params(2.2, 1.5), 0.012)

    def test_running_estimator(self):
        # накопление на лету даёт то же, что и оценка по готовой выборке
        ys = nm.sequence(nm.PRESETS["E"], 20000, seed=4)
        run = correlation.Running(10)
        for y in ys:
            run.push(y)
        est = correlation.Estimator(ys)
        self.assertAlmostEqual(run.mean, est.mean, places=12)
        for k, r in enumerate(run.normalized()):
            self.assertAlmostEqual(r, est.normalized(k), delta=2e-3)

    def test_correlation_from_motion(self):
        # единая модель: корреляционная функция по скоростям y_n из движения во времени совпадает с теорией
        p = nm.PRESETS["H"]
        theory, part, moments, mean = markov.discrete_theory(p, 10)
        run = correlation.Running(10)
        mo = nm.Motion(p, 0.3)
        mo.on_cross = run.push
        mo.advance(60000 * math.pi + 0.1)
        self.assertEqual(run.count, 60000)
        for k, r in enumerate(run.normalized()):
            self.assertAlmostEqual(r, theory[k], delta=0.015)
        s = 8
        cexp = markov.continuous_theory(p, s, 3 * s, run.moments(), run.mean)
        cth = markov.continuous_theory(p, s, 3 * s, moments, mean)
        for a, b in zip(cexp, cth):
            self.assertAlmostEqual(a, b, delta=0.03)


if __name__ == "__main__":
    unittest.main()
