"""Экспериментальная (выборочная) корреляционная функция стационарного процесса:
по готовой выборке (Estimator) и накапливаемая во время движения (Running)."""


class Estimator:
    """Считает R[k]/R[0] по одному сдвигу за вызов, чтобы строить функцию по шагам."""

    def __init__(self, data):
        self.data = data
        n = len(data)
        self.mean = sum(data) / n
        self.centered = [x - self.mean for x in data]
        self.var = sum(x * x for x in self.centered) / n

    def raw(self, k):
        """Выборочное среднее произведения отклонений при сдвиге k."""
        c = self.centered
        n = len(c) - k
        if n <= 0:
            return 0.0
        return sum(a * b for a, b in zip(c, c[k:])) / n

    def normalized(self, k):
        return self.raw(k) / self.var if self.var > 0 else 0.0


class Running:
    """Корреляционная функция, которая копится на лету по мере появления новых значений.

    Хранит суммы y_n и y_n * y_{n-k} для k = 0..kmax, поэтому добавление одного значения
    стоит kmax + 1 умножений, а память не растёт с длиной реализации.
    """

    def __init__(self, kmax):
        self.kmax = kmax
        self.clear()

    def clear(self):
        self.count = 0
        self.total = 0.0
        self.sums = [0.0] * (self.kmax + 1)
        self.recent = []  # последние kmax + 1 значений, самое новое первым

    def push(self, y):
        self.recent.insert(0, y)
        if len(self.recent) > self.kmax + 1:
            self.recent.pop()
        self.count += 1
        self.total += y
        sums = self.sums
        for k, old in enumerate(self.recent):
            sums[k] += y * old

    @property
    def mean(self):
        return self.total / self.count if self.count else 0.0

    def moments(self):
        """M[k] = выборочное <y_n y_{n+k}>, k = 0..kmax, по стольким парам, сколько накоплено."""
        n = self.count
        return [s / (n - k) if n > k else 0.0 for k, s in enumerate(self.sums)]

    @property
    def var(self):
        return self.moments()[0] - self.mean ** 2 if self.count else 0.0

    def normalized(self):
        """R[k]/R[0], k = 0..kmax (пустой список, пока данных мало)."""
        if self.count <= self.kmax + 1:
            return []
        m, mean = self.moments(), self.mean
        r0 = m[0] - mean * mean
        if r0 <= 0:
            return []
        return [(x - mean * mean) / r0 for x in m]
