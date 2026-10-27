"""Осциллятор Неймарка в аномальном режиме.

Уравнение движения (a = 1):
    x'' - 2*delta*x' + (1 + delta^2)*x = -h * theta(x' - a) * x' * delta(x).

Между ударами решение точное: если при прохождении x = 0 скорость равна y,
то x(u) = y e^{delta u} sin u,  v(u) = y f(u),  f(u) = e^{delta u}(delta sin u + cos u).
Через полпериода (u = pi) скорость равна -sqrt(gamma) * y, gamma = e^{2 pi delta}.
Если она оказалась >= a, происходит удар, уменьшающий её на h.
"""
import math
import random

A = 1.0  # критическая скорость a; все величины измеряются в единицах a


class Params:
    def __init__(self, gamma, h):
        self.gamma = float(gamma)
        self.h = float(h)

    @property
    def s(self):
        """Коэффициент растяжения за полпериода, gamma^(1/2)."""
        return math.sqrt(self.gamma)

    @property
    def delta(self):
        return math.log(self.gamma) / (2.0 * math.pi)

    @property
    def lower(self):
        """Нижний край аттрактора, -gamma^(1/2) a."""
        return -self.s * A

    @property
    def upper(self):
        return A

    @property
    def branch(self):
        """Точка ветвления -gamma^(-1/2) a: левее неё за полпериода происходит удар."""
        return -A / self.s

    def h_range(self):
        """Допустимые h/a при данном gamma (область ABC на плоскости параметров)."""
        return self.gamma - 1.0, 1.0 + self.s

    def is_chaotic(self):
        lo, hi = self.h_range()
        return self.gamma > 1.0 and lo - 1e-12 <= self.h <= hi + 1e-12

    def __eq__(self, other):
        return isinstance(other, Params) and (self.gamma, self.h) == (other.gamma, other.h)

    def __repr__(self):
        return f"Params(gamma={self.gamma:.6g}, h={self.h:.6g})"


GOLDEN = (1.0 + math.sqrt(5.0)) / 2.0

# Марковские точки из статьи (Стратонович, Рузмайкина, Чичигина, 1993, рис. 4)
PRESETS = {
    "H": Params(GOLDEN ** 2, GOLDEN ** 2 - 1.0),  # N = 2 интервала
    "E": Params(GOLDEN ** 2, GOLDEN ** 2),         # N = 3 интервала
}


def step(y, p):
    """Отображение за полпериода y_n -> y_{n+1}."""
    z = -p.s * y
    if z >= A:
        z -= p.h
    return z


def sequence(p, n, seed=None, burn=500):
    """Последовательность скоростей y_n в моменты прохождения x = 0 (после удара)."""
    rng = random.Random(seed)
    y = rng.uniform(p.branch, A)
    for _ in range(burn):
        y = step(y, p)
    out = [0.0] * n
    for i in range(n):
        out[i] = y
        y = step(y, p)
    return out


def shape(u, delta):
    """f(u): скорость в фазе u полупериода при единичной начальной скорости."""
    return math.exp(delta * u) * (delta * math.sin(u) + math.cos(u))


def shape_table(p, samples):
    """f в серединах `samples` равных частей полупериода."""
    d = p.delta
    return [shape((j + 0.5) * math.pi / samples, d) for j in range(samples)]


def velocity(ys, p, samples):
    """Непрерывная скорость v(t), по `samples` отсчётов на полпериод (шаг pi/samples)."""
    f = shape_table(p, samples)
    out = []
    for y in ys:
        out.extend(y * fj for fj in f)
    return out


def position(u, delta):
    """g(u) = e^{δu} sin u: координата в фазе u полупериода при единичной начальной скорости."""
    return math.exp(delta * u) * math.sin(u)


class HalfPeriod:
    """Один полупериод движения: начинается в момент t0 при x = 0 со скоростью y (после удара)."""

    __slots__ = ("n", "t0", "y", "before", "after", "hit")

    def __init__(self, n, t0, y):
        self.n = n          # номер полупериода от начала движения
        self.t0 = t0
        self.y = y
        self.before = None  # скорость в конце полупериода до удара
        self.after = None   # скорость после удара (= y следующего полупериода)
        self.hit = False


class Motion:
    """Движение осциллятора во времени, точно по событиям (для вкладки «Движение осциллятора»).

    Между прохождениями x = 0 решение аналитическое, поэтому численного интегрирования нет:
    состояние — номер текущего полупериода и время s, прошедшее с его начала.
    Каждые pi единиц времени применяется то же правило step(), что и в остальной программе.
    """

    LIMIT = 1e4      # при |x| или |v| больше этого движение считается ушедшим на бесконечность
    HISTORY = 2000   # сколько полупериодов хранить (для графиков и отображения)

    def __init__(self, p, v0):
        self.p = p
        self.t = 0.0
        self.s = 0.0
        self.halves = [HalfPeriod(0, 0.0, float(v0))]
        self.crossings = 0
        self.hits = 0
        self.escaped = False
        self.on_cross = None  # функция(y) — вызывается с каждой новой скоростью y_n

    @classmethod
    def near(cls, other, dv):
        """Копия движения other в текущий момент, но со скоростью текущего полупериода больше на dv."""
        mo = cls(other.p, 0.0)
        cur = other.current
        mo.t, mo.s = other.t, other.s
        mo.halves = [HalfPeriod(cur.n, cur.t0, cur.y + dv)]
        mo.crossings = other.crossings
        return mo

    @property
    def current(self):
        return self.halves[-1]

    def state(self):
        """Текущие координата и скорость."""
        y, d = self.current.y, self.p.delta
        return y * position(self.s, d), y * shape(self.s, d)

    def advance(self, dt):
        """Продвинуть время на dt. Возвращает число ударов, случившихся за это время."""
        hits_before = self.hits
        while dt > 0 and not self.escaped:
            if self.current.y == 0.0:  # покой: x = 0, v = 0, ничего не происходит
                self.t += dt
                break
            left = math.pi - self.s
            if dt < left:
                self.s += dt
                self.t += dt
                dt = 0.0
            else:
                dt -= left
                self.t = self.current.t0 + math.pi
                self._cross()
            x, v = self.state()
            if max(abs(x), abs(v), abs(self.current.y)) > self.LIMIT:
                self.escaped = True
        return self.hits - hits_before

    def _cross(self):
        half = self.current
        half.before = -self.p.s * half.y
        half.after = step(half.y, self.p)
        half.hit = half.after != half.before
        self.crossings += 1
        self.hits += half.hit
        self.halves.append(HalfPeriod(half.n + 1, self.t, half.after))
        self.s = 0.0
        if len(self.halves) > self.HISTORY * 3 // 2:  # чистим пачками, чтобы не сдвигать список каждый раз
            del self.halves[:len(self.halves) - self.HISTORY]
        if self.on_cross:
            self.on_cross(half.after)

    def pairs(self):
        """Наблюдаемые пары (y_n, y_{n+1}) для графика отображения за полпериода."""
        return [(h.y, h.after) for h in self.halves if h.after is not None]
