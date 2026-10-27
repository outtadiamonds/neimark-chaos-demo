"""Теоретическая корреляционная функция через марковское разбиение оси скоростей.

Как в FPAllbook (с. 76) и в статье 1993 г.: образы краёв аттрактора и точки ветвления
разбивают ось скоростей на отрезки. Когда новые точки перестают появляться (или
попадают с заданной точностью в уже существующие), каждый отрезок I_i линейно
отображается на объединение отрезков, и процесс y_n становится марковским.

Стационарная плотность кусочно-постоянна, а оператор Перрона-Фробениуса переводит
кусочно-линейные функции в кусочно-линейные. Поэтому
    <y_0 y_k> = integral z (P^k [y w])(z) dz
вычисляется точно конечными суммами.
"""
import bisect
import math

from .neimark import A, step


class MarkovPartition:
    def __init__(self, points, p, exact):
        self.points = points  # отсортированные точки разбиения
        self.exact = exact    # True, если разбиение замкнулось без округления
        self.n = len(points) - 1
        # для каждого отрезка: slope, offset, первый и последний целевые отрезки
        self.maps = []
        for i in range(self.n):
            l, r = points[i], points[i + 1]
            c = -p.h if r <= p.branch + 1e-12 else 0.0
            hi = _nearest(points, -p.s * l + c)
            lo = _nearest(points, -p.s * r + c)
            if hi <= lo:
                hi = lo + 1
            # точная аффинная замена, переводящая [l, r] на [points[lo], points[hi]] с разворотом
            slope = -(points[hi] - points[lo]) / (r - l)
            offset = points[hi] - slope * l
            self.maps.append((slope, offset, lo, hi))

    def transfer(self, c0, c1):
        """Один шаг оператора Перрона-Фробениуса для кусочно-линейной функции c0 + c1*z."""
        n0 = [0.0] * self.n
        n1 = [0.0] * self.n
        for i, (slope, offset, lo, hi) in enumerate(self.maps):
            a0, a1 = c0[i], c1[i]
            if a0 == 0.0 and a1 == 0.0:
                continue
            k = 1.0 / abs(slope)
            b0 = (a0 - a1 * offset / slope) * k
            b1 = (a1 / slope) * k
            for j in range(lo, hi):
                n0[j] += b0
                n1[j] += b1
        return n0, n1

    def stationary(self, tol=1e-13, max_iter=20000):
        """Кусочно-постоянная стационарная плотность w_i."""
        pts = self.points
        lengths = [pts[i + 1] - pts[i] for i in range(self.n)]
        total = sum(lengths)
        w = [1.0 / total] * self.n
        zero = [0.0] * self.n
        for _ in range(max_iter):
            pw, _ = self.transfer(w, zero)
            # «ленивая» цепь (w + Pw)/2 сходится и для периодических компонент
            new = [(x + y) * 0.5 for x, y in zip(w, pw)]
            mass = sum(x * L for x, L in zip(new, lengths))
            new = [x / mass for x in new]
            if max(abs(x - y) for x, y in zip(new, w)) < tol:
                return new
            w = new
        return w

    def moments(self, kmax):
        """M[k] = <y_n y_{n+k}> для k = 0..kmax и среднее <y>."""
        pts = self.points
        w = self.stationary()
        mean = sum(w[i] * (pts[i + 1] ** 2 - pts[i] ** 2) / 2.0 for i in range(self.n))
        c0 = [0.0] * self.n
        c1 = list(w)  # функция y * w(y)
        out = []
        for _ in range(kmax + 1):
            m = 0.0
            for i in range(self.n):
                l, r = pts[i], pts[i + 1]
                m += c0[i] * (r * r - l * l) / 2.0 + c1[i] * (r ** 3 - l ** 3) / 3.0
            out.append(m)
            c0, c1 = self.transfer(c0, c1)
        return out, mean


def _nearest(points, x):
    i = bisect.bisect_left(points, x)
    if i == 0:
        return 0
    if i == len(points):
        return len(points) - 1
    return i if points[i] - x < x - points[i - 1] else i - 1


def build_partition(p, max_points=3000):
    """Строит разбиение из орбит верхнего края a и его образа после удара a - h.

    Сначала ищется точное (марковское) разбиение; если его нет, новые точки,
    попавшие ближе eps к существующим, считаются совпавшими с ними.
    """
    span = A - p.lower
    for eps in (1e-9, 2e-4 * span, 1e-3 * span):
        pts = _orbit_points(p, eps, max_points)
        if pts is not None:
            return MarkovPartition(pts, p, exact=(eps == 1e-9))
    return MarkovPartition(_orbit_points(p, 3e-3 * span, 10 ** 9), p, exact=False)


def _orbit_points(p, eps, max_points):
    pts = [p.branch]
    queue = [A - p.h, p.lower, A]
    while queue:
        q = queue.pop()
        q = min(max(q, p.lower), A)
        i = _nearest(pts, q)
        if abs(pts[i] - q) <= eps:
            continue
        bisect.insort(pts, q)
        if len(pts) > max_points:
            return None
        queue.append(step(q, p))
    # края аттрактора должны совпадать с краями разбиения точно
    if pts[0] - p.lower <= eps:
        pts[0] = p.lower
    else:
        pts.insert(0, p.lower)
    if A - pts[-1] <= eps:
        pts[-1] = A
    else:
        pts.append(A)
    return pts


def discrete_theory(p, kmax, partition=None):
    """Нормированная R[k]/R[0], k = 0..kmax; также разбиение и сырые моменты."""
    part = partition or build_partition(p)
    m, mean = part.moments(kmax + 1)
    r0 = m[0] - mean * mean
    return [(x - mean * mean) / r0 for x in m[:kmax + 1]], part, m, mean


def continuous_theory(p, samples, lags, moments, mean):
    """Нормированная C(tau)/C(0) скорости v(t) при tau = j*pi/samples, j = 0..lags.

    v(t) = y_n f(u), фаза u равномерна на [0, pi), поэтому при tau = m*pi + r
    <v(t) v(t+tau)> = (M[m] * int_0^{pi-r} f(u) f(u+r) du + M[m+1] * int_{pi-r}^{pi} f(u) f(u+r-pi) du) / pi.
    Интегралы берутся по тем же отсчётам, что и в эксперименте.
    """
    from .neimark import shape_table
    f = shape_table(p, samples)
    fmean = sum(f) / samples
    vmean = mean * fmean
    need = lags // samples + 2
    if len(moments) < need + 1:
        raise ValueError("not enough moments")
    out = []
    for j in range(lags + 1):
        m, r = divmod(j, samples)
        same = sum(f[u] * f[u + r] for u in range(samples - r))
        cross = sum(f[u] * f[u + r - samples] for u in range(samples - r, samples))
        out.append((moments[m] * same + moments[m + 1] * cross) / samples - vmean * vmean)
    c0 = out[0]
    return [x / c0 for x in out]
