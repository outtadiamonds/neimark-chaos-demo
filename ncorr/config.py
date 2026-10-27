"""Важные числа программы — файл assets/config.json.

Здесь, в SCHEMA, перечислены все настраиваемые числа: значение по умолчанию и что оно значит.
Файл config.json хранит значения (и пояснения к ним, раздел "_описание"); его можно править
в режиме разработчика (F12 → «Числа») или любым текстовым редактором. Файл попадает в сборку.
Если файла нет или какого-то числа в нём нет, берётся значение по умолчанию отсюда.

В коде числа читаются так: config.motion.track, config.demo.kmax и т. д. Модули, у которых
числа нужны на уровне модуля (motion.py, demo.py, neimark.py, param_plane.py), получают их
в функции refresh(); App.rebuild() вызывает её после изменения чисел и пересоздаёт экраны.
"""
import copy
import json

from . import resources as res

FILE = "config.json"

# (раздел, ключ, значение по умолчанию, что это, (минимум, максимум))
SCHEMA = [
    # --- физика ---
    ("physics", "limit", 1e4, "|x| или |v| больше этого — движение ушло на бесконечность, опыт останавливается",
     (10, 1e8)),
    ("physics", "history", 2000, "сколько последних полупериодов движения хранить (для графиков и отображения)",
     (100, 100000)),

    # --- вкладка «Движение осциллятора» ---
    ("motion", "phase_trail", 24, "сколько последних полупериодов видно в следе на фазовой плоскости", (1, 500)),
    ("motion", "time_window", 8, "ширина окна графика v(t), в полупериодах", (2, 100)),
    ("motion", "curve_samples", 40, "точек кривой на один полупериод (гладкость линий)", (4, 400)),
    ("motion", "flash_decay", 1.8, "как быстро гаснет красная вспышка удара, 1/с (меньше — дольше)", (0.1, 20)),
    ("motion", "track", 40, "сколько последних yₙ на графике «Две траектории»", (5, 500)),
    ("motion", "twins", [1e-2, 1e-5, 1e-8], "варианты ε для близкой траектории (через запятую)", (1e-15, 1)),
    ("motion", "twin_default", 1, "какое ε выбрано при запуске: 0 — нет, 1 — первое из списка, 2 — второе…",
     (0, 10)),
    ("motion", "speed", 1.0, "скорость анимации при запуске", (0.01, 10000)),
    ("motion", "speed_min", 0.25, "наименьшая скорость анимации на ползунке", (0.01, 100)),
    ("motion", "speed_max", 100.0, "наибольшая скорость анимации на ползунке", (1, 100000)),
    ("motion", "gamma_min", 1.0, "ползунок γ: от", (0.5, 10)),
    ("motion", "gamma_max", 4.0, "ползунок γ: до", (1, 20)),
    ("motion", "h_min", 0.0, "ползунок h/a: от", (0, 10)),
    ("motion", "h_max", 3.5, "ползунок h/a: до", (0.1, 20)),
    ("motion", "v0_min", -2.0, "ползунок v₀: от", (-100, 0)),
    ("motion", "v0_max", 2.0, "ползунок v₀: до", (0, 100)),
    ("motion", "v0_markov", 0.3, "начальная скорость в сценариях «Точка H» и «Точка E»", (-10, 10)),
    ("motion", "normal_gamma", 1.5, "сценарий «Нормальный режим»: γ", (1, 10)),
    ("motion", "normal_h", 0.8, "сценарий «Нормальный режим»: h/a (должно быть меньше 1)", (0, 1)),
    ("motion", "normal_v0", 0.42, "сценарий «Нормальный режим»: начальная скорость", (-10, 10)),
    ("motion", "free_gamma", 1.5, "сценарий «Без ударов»: γ", (1, 10)),
    ("motion", "free_v0", 0.42, "сценарий «Без ударов»: начальная скорость", (-10, 10)),

    # --- вкладка «Корреляционная функция» ---
    ("demo", "n_samples", 50000, "длина выборки N при запуске", (100, 1000000)),
    ("demo", "n_min", 1000, "ползунок длины выборки: от", (100, 1000000)),
    ("demo", "n_max", 100000, "ползунок длины выборки: до", (1000, 2000000)),
    ("demo", "kmax", 30, "сколько сдвигов k строить для yₙ (столбиков R(k))", (2, 200)),
    ("demo", "samples", 16, "отсчётов v(t) на полпериод в непрерывном режиме", (4, 64)),
    ("demo", "tau_step", 2, "шаг сдвига τ в непрерывном режиме, в отсчётах (2 при 16 отсчётах — это π/8)",
     (1, 64)),
    ("demo", "c_steps", 48, "сколько сдвигов τ строить для v(t) (48 · π/8 = 6π)", (2, 400)),
    ("demo", "cont_half", 20000, "по скольким полупериодам считается C(τ)", (1000, 200000)),
    ("demo", "speed", 1.0, "скорость анимации построения при запуске", (0.05, 20)),
    ("demo", "speed_min", 0.25, "наименьшая скорость анимации на ползунке", (0.01, 10)),
    ("demo", "speed_max", 4.0, "наибольшая скорость анимации на ползунке", (1, 100)),
    ("demo", "shift_end", 0.45, "доля шага анимации на сдвиг копии (0…1)", (0.05, 0.9)),
    ("demo", "product_end", 0.7, "доля шага, к которой появились произведения (больше shift_end, меньше 1)",
     (0.1, 0.95)),
    ("demo", "view_d", 60, "сколько yₙ видно в окне графиков при запуске", (10, 2000)),
    ("demo", "view_c", 12, "сколько полупериодов v(t) видно в окне графиков при запуске", (2, 200)),
    ("demo", "cursor_speed", 1.5, "скорость точки на маленькой фазовой плоскости, полупериодов в секунду",
     (0.1, 20)),
    ("demo", "cursor_span", 40, "точка обходит не больше стольких полупериодов от начала окна", (2, 500)),
    ("demo", "seed", 1, "номер случайной начальной точки ряда (другой номер — другая реализация)", (0, 10 ** 9)),
    ("demo", "gamma_min", 1.05, "наименьшее γ на плоскости параметров и ползунке", (1.0, 4)),
    ("demo", "gamma_max", 4.0, "наибольшее γ на плоскости параметров и ползунке", (1.5, 10)),

    # --- окно ---
    ("window", "min_width", 1024, "наименьшая ширина окна при запуске, px", (640, 4000)),
    ("window", "min_height", 640, "наименьшая высота окна при запуске, px", (400, 3000)),
    ("window", "fps", 60, "кадров в секунду", (10, 240)),
]

SECTIONS = {
    "physics": "Физика",
    "motion": "Вкладка «Движение осциллятора»",
    "demo": "Вкладка «Корреляционная функция»",
    "window": "Окно",
}

DEFAULTS = {}
for _sec, _key, _val, _what, _lim in SCHEMA:
    DEFAULTS.setdefault(_sec, {})[_key] = _val
values = copy.deepcopy(DEFAULTS)


class _Section:
    def __init__(self, name):
        self._name = name

    def __getattr__(self, key):
        return values[self._name][key]


physics = _Section("physics")
motion = _Section("motion")
demo = _Section("demo")
window = _Section("window")


def file_path():
    return res.path(FILE)


def entry(section, key):
    return next(e for e in SCHEMA if e[0] == section and e[1] == key)


def coerce(section, key, value):
    """Привести значение к типу и пределам из SCHEMA; ValueError, если это не число."""
    _, _, default, _, (lo, hi) = entry(section, key)
    if isinstance(default, list):
        items = value if isinstance(value, list) else [v for v in str(value).replace(";", ",").split(",") if v.strip()]
        out = [min(max(float(v), lo), hi) for v in items]
        if not out:
            raise ValueError("пустой список")
        return out
    number = float(str(value).replace(",", ".").replace("−", "-"))
    number = min(max(number, lo), hi)
    return int(round(number)) if isinstance(default, int) else number


def use_defaults():
    global values
    values = copy.deepcopy(DEFAULTS)


def load():
    """Прочитать assets/config.json; неизвестные ключи и ошибочные значения пропускаются."""
    use_defaults()
    try:
        with open(file_path(), encoding="utf-8") as f:
            saved = json.load(f)
    except (OSError, ValueError):
        return
    for section, items in saved.items():
        if section not in DEFAULTS or not isinstance(items, dict):
            continue
        for key, value in items.items():
            if key in DEFAULTS[section]:
                try:
                    values[section][key] = coerce(section, key, value)
                except (ValueError, TypeError):
                    pass


def dumps():
    data = copy.deepcopy(values)
    data["_описание"] = {f"{s}.{k}": what for s, k, _, what, _ in SCHEMA}
    return json.dumps(data, ensure_ascii=False, indent=1)


def save():
    with open(file_path(), "w", encoding="utf-8") as f:
        f.write(dumps())


def set_value(section, key, value):
    values[section][key] = coerce(section, key, value)


def fmt(value):
    if isinstance(value, list):
        return ", ".join(fmt(v) for v in value)
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)
