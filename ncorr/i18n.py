"""Все надписи программы на русском и английском."""
import re

LANGS = ("ru", "en")
_lang = "ru"
OVERRIDES = {"ru": {}, "en": {}}  # надписи, изменённые в режиме разработчика (design.py)
TRACE = None  # в режиме разработчика: [(готовый текст, ключ)] за кадр — чтобы знать, какой ключ где нарисован

STRINGS = {
    # Шапка и меню
    "msu": ("Московский государственный университет имени М.В. Ломоносова",
            "Lomonosov Moscow State University"),
    "faculty": ("Факультет вычислительной математики и кибернетики",
                "Faculty of Computational Mathematics and Cybernetics"),
    "course": ("Компьютерная демонстрация по курсу «Статистическая физика»",
               "Computer demonstration for the course “Statistical Physics”"),
    "title1": ("Осциллятор Неймарка:", "Neimark oscillator:"),
    "title2": ("динамический хаос и корреляционная функция", "dynamic chaos and the correlation function"),
    "window_title": ("Осциллятор Неймарка", "Neimark oscillator"),
    "model": ("Демонстрация", "Demonstration"),
    "tab_motion": ("Движение осциллятора", "Oscillator motion"),
    "tab_corr": ("Корреляционная функция", "Correlation function"),
    "demo": ("Построение корреляционной функции", "Building the correlation function"),
    "theory": ("Теория", "Theory"),
    "authors": ("Авторы", "Authors"),
    "exit": ("Выход", "Exit"),
    "back": ("Назад", "Back"),
    "lang_switch": ("English", "Русский"),
    "fullscreen_hint": ("F11 — полноэкранный режим", "F11 — full screen"),

    # Демонстрация: панели
    "p1_d": ("Процесс: скорость yₙ в моменты прохождения x = 0 (через полпериода)",
             "Process: velocity yₙ at the moments x = 0 (every half-period)"),
    "p1_c": ("Процесс: скорость v(t)", "Process: velocity v(t)"),
    "p2_d": ("Та же реализация, сдвинутая на k = {k}", "The same realization shifted by k = {k}"),
    "p2_c": ("Та же реализация, сдвинутая на τ = {tau}", "The same realization shifted by τ = {tau}"),
    "p3_d": ("Наложение: произведение отклонений (yₙ − ⟨y⟩)(yₙ₊ₖ − ⟨y⟩) / D",
             "Overlay: product of deviations (yₙ − ⟨y⟩)(yₙ₊ₖ − ⟨y⟩) / D"),
    "p3_c": ("Наложение: произведение отклонений (v(t) − ⟨v⟩)(v(t+τ) − ⟨v⟩) / D",
             "Overlay: product of deviations (v(t) − ⟨v⟩)(v(t+τ) − ⟨v⟩) / D"),
    "p4_d": ("Корреляционная функция R(k) / R(0)", "Correlation function R(k) / R(0)"),
    "p4_c": ("Корреляционная функция C(τ) / C(0)", "Correlation function C(τ) / C(0)"),
    "axis_n": ("n", "n"),
    "axis_t": ("t / π", "t / π"),
    "axis_k": ("k", "k"),
    "axis_tau": ("τ / π", "τ / π"),
    "legend_exp": ("эксперимент (среднее по выборке)", "experiment (sample average)"),
    "legend_theory": ("теория (марковское разбиение)", "theory (Markov partition)"),
    "legend_orig": ("исходный", "original"),
    "legend_shift": ("сдвинутый", "shifted"),
    "legend_pos": ("вклад > 0", "contribution > 0"),
    "legend_neg": ("вклад < 0", "contribution < 0"),
    "mean": ("среднее", "mean"),
    "zoom_hint": ("колесо мыши — масштаб, перетаскивание — прокрутка",
                  "mouse wheel — zoom, drag — scroll"),

    # Демонстрация: управление
    "sec_process": ("Процесс", "Process"),
    "mode_d": ("yₙ за полпериода", "yₙ per half-period"),
    "mode_c": ("непрерывный v(t)", "continuous v(t)"),
    "sec_params": ("Параметры осциллятора", "Oscillator parameters"),
    "preset_H": ("Точка H", "Point H"),
    "preset_E": ("Точка E", "Point E"),
    "preset_custom": ("Свои", "Custom"),
    "gamma": ("γ — рост амплитуды за период", "γ — amplitude growth per period"),
    "h": ("h / a — величина удара", "h / a — kick size"),
    "plane": ("Область хаоса", "Chaos region"),
    "phase": ("Фазовая плоскость (x, v)", "Phase plane (x, v)"),
    "sec_build": ("Построение", "Construction"),
    "samples": ("Длина выборки N", "Sample length N"),
    "speed": ("Скорость анимации", "Animation speed"),
    "run": ("Пуск", "Run"),
    "pause": ("Пауза", "Pause"),
    "step": ("Шаг", "Step"),
    "reset": ("Заново", "Reset"),
    "build_all": ("Построить всё", "Build all"),
    "info_value_d": ("R({k}) / R(0) = {v}   теория: {t}", "R({k}) / R(0) = {v}   theory: {t}"),
    "info_value_c": ("C({tau}) / C(0) = {v}   теория: {t}", "C({tau}) / C(0) = {v}   theory: {t}"),
    "info_stats_d": ("⟨y⟩ = {mean}   D = {var}   δ = {delta}", "⟨y⟩ = {mean}   D = {var}   δ = {delta}"),
    "info_stats_c": ("⟨v⟩ = {mean}   D = {var}   δ = {delta}", "⟨v⟩ = {mean}   D = {var}   δ = {delta}"),
    "info_partition_exact": ("Марковское разбиение: N = {n} (точное)", "Markov partition: N = {n} (exact)"),
    "info_partition_approx": ("Марковское разбиение: N = {n} (приближённое)",
                              "Markov partition: N = {n} (approximate)"),
    "info_edges": ("Аттрактор [{lo}, 1], точка ветвления {br}",
                   "Attractor [{lo}, 1], branching point {br}"),

    # Движение осциллятора
    "m_osc": ("Движение осциллятора", "Oscillator motion"),
    "m_phase": ("Фазовая траектория (x, v)", "Phase trajectory (x, v)"),
    "m_time": ("Скорость во времени v(t) — проекция траектории", "Velocity in time v(t) — projection of the trajectory"),
    "m_map": ("Отображение за полпериода yₙ → yₙ₊₁", "Half-period map yₙ → yₙ₊₁"),
    "sec_scenario": ("Сценарий", "Scenario"),
    "sc_normal": ("Нормальный режим", "Normal mode"),
    "sc_free": ("Без ударов", "No kicks"),
    "v0": ("v₀ — начальная скорость", "v₀ — initial velocity"),
    "sec_run": ("Опыт", "Experiment"),
    "step_pi": ("Шаг π", "Step π"),
    "projection": ("Проекция", "Projection"),
    "sections": ("Точки x = 0", "Points x = 0"),
    "formula_title": ("Отображение за полпериода:", "Half-period map:"),
    "formula_note": ("удар при x = 0, если скорость ≥ a; величины безразмерные", "kick at x = 0 if velocity ≥ a; dimensionless units"),
    "kick_label": ("удар: v → v − h", "kick: v → v − h"),
    "escaped": ("Движение ушло на бесконечность: удар слишком слаб. Нажмите «Заново» или измените h.",
                "The motion went to infinity: the kick is too weak. Press “Reset” or change h."),
    "state_line": ("t = {t}   x = {x}   v = {v}", "t = {t}   x = {x}   v = {v}"),
    "count_line": ("Прохождений x = 0: {n}   ударов: {hits}", "Passages of x = 0: {n}   kicks: {hits}"),
    "params_line": ("√γ = {s} (рост за полпериода)   δ = {delta}", "√γ = {s} (growth per half-period)   δ = {delta}"),
    "region_in_anomalous": ("Аномальный режим (h > a), область хаоса", "Anomalous mode (h > a), chaos region"),
    "region_in_normal": ("Нормальный режим (h < a), область хаоса", "Normal mode (h < a), chaos region"),
    "region_out_weak": ("Вне области хаоса: h/a < γ − 1, амплитуда растёт", "Outside the chaos region: h/a < γ − 1, amplitude grows"),
    "region_out_strong": ("Вне области хаоса: h/a > 1 + √γ", "Outside the chaos region: h/a > 1 + √γ"),
    "lg_now_short": ("текущее состояние", "current state"),
    "lg_kick_short": ("удар", "kick"),
    "lg_section_short": ("yₙ — скорость при x = 0", "yₙ — velocity at x = 0"),
    "lg_twin": ("близкая траектория v₀ + ε", "nearby trajectory v₀ + ε"),
    "y_star": ("y* — бифуркация", "y* — bifurcation"),
    "sec_twin": ("Близкая траектория: v₀ + ε, ε =", "Nearby trajectory: v₀ + ε, ε ="),
    "twin_off": ("нет", "off"),
    "m_twins": ("Две траектории: v₀ и v₀ + ε", "Two trajectories: v₀ and v₀ + ε"),
    "m_seq": ("Последовательность yₙ", "Sequence yₙ"),
    "twin_same": ("пока совпадают; разойдутся через ≈ ln(1/ε)/ln√γ = {e}",
                  "still coincide; will split after ≈ ln(1/ε)/ln√γ = {e}"),
    "twin_split": ("разошлись через {n} полупериодов (оценка {e})", "split after {n} half-periods (estimate {e})"),
    "twin_hint": ("включите близкую траекторию справа", "turn on the nearby trajectory on the right"),
    "twin_nochaos": ("вне области хаоса эта оценка неприменима", "outside the chaos region this estimate does not apply"),

    # Подписи на графиках (оси, уровни, формулы)
    "g_x": ("x", "x"),
    "g_v": ("v", "v"),
    "g_a": ("a", "a"),
    "g_t": ("t / π", "t / π"),
    "g_n": ("n", "n"),
    "g_yn": ("yₙ", "yₙ"),
    "g_yn1": ("yₙ₊₁", "yₙ₊₁"),
    "g_ystar": ("y*", "y*"),
    "g_dy": ("|Δyₙ|", "|Δyₙ|"),
    "g_growth": ("ε·γ^(n/2)", "ε·γ^(n/2)"),
    "g_gamma": ("γ", "γ"),
    "g_ha": ("h/a", "h/a"),
    "g_mean_d": ("⟨y⟩", "⟨y⟩"),
    "g_mean_c": ("⟨v⟩", "⟨v⟩"),
    "g_overlay_d": ("⟨(yₙ − ⟨y⟩)(yₙ₊ₖ − ⟨y⟩)⟩ / D = {v}", "⟨(yₙ − ⟨y⟩)(yₙ₊ₖ − ⟨y⟩)⟩ / D = {v}"),
    "g_overlay_c": ("⟨(v(t) − ⟨v⟩)(v(t+τ) − ⟨v⟩)⟩ / D = {v}", "⟨(v(t) − ⟨v⟩)(v(t+τ) − ⟨v⟩)⟩ / D = {v}"),
    "map_formula": ("yₙ₊₁ = −√γ·yₙ − h·θ(−√γ·yₙ − a)", "yₙ₊₁ = −√γ·yₙ − h·θ(−√γ·yₙ − a)"),

    # Теория и авторы
    "theory_missing": ("Текст теории не найден.", "Theory text not found."),
    "lecturer": ("Лектор", "Lecturer"),
    "supervisor": ("Руководитель", "Supervisor"),
    "authors_title": ("Авторы", "Authors"),
    "to_be_added": ("будет добавлено", "to be added"),
}


def set_lang(lang):
    global _lang
    _lang = lang


def lang():
    return _lang


def toggle():
    set_lang("en" if _lang == "ru" else "ru")


def base(key, lang=None):
    """Надпись из этого файла, без изменений из design.json."""
    return STRINGS[key][LANGS.index(lang or _lang)]


def raw(key, lang=None):
    """Надпись с учётом design.json, ещё без подстановки чисел."""
    lang = lang or _lang
    return OVERRIDES.get(lang, {}).get(key) or base(key, lang)


def t(key, **kw):
    s = raw(key)
    if kw:
        try:
            s = s.format(**kw)
        except (KeyError, IndexError, ValueError):  # в изменённой надписи испорчены {поля} — берём исходную
            s = base(key).format(**kw)
    if TRACE is not None:
        TRACE.append((s, key))
    return s


def traced_key(text):
    """Ключ, которым в этом кадре получен такой текст (самый поздний вызов t)."""
    for s, key in reversed(TRACE or ()):
        if s == text:
            return key
    return None


def _pattern(template):
    """Регулярное выражение для надписи с полями {…}: поля могут быть любым текстом."""
    parts = re.split(r"\{[^{}]*\}", template)
    return re.compile("(.*?)".join(re.escape(p) for p in parts) + "$", re.S)


def find_key(text):
    """Ключ надписи по её тексту на текущем языке, в том числе надписи с подставленными числами."""
    for key in STRINGS:
        if raw(key) == text:
            return key
    for key in STRINGS:
        template = raw(key)
        if "{" in template and _pattern(template).match(text):
            return key
    return None


def pick(entry):
    """Выбор из словаря {"ru": ..., "en": ...} с запасным вариантом."""
    if isinstance(entry, str):
        return entry
    return entry.get(_lang) or entry.get("ru") or ""
