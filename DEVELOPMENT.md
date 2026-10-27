# Разработка: сборка и устройство проекта

Все команды запускаются из корня проекта `C:\idk\phys`.

> Полное руководство по всему коду — [CODE_GUIDE.md](CODE_GUIDE.md). Здесь краткая справка.
>
> **Быстрая сборка одной командой:** `.venv/Scripts/python tools/build.py` (Windows), `tools/build.py linux` (Linux, Docker Desktop запустить вручную), `tools/build.py all` (оба), `tools/build.py theory` (теория). Или двойной щелчок по `build.bat`.

---

## 1. Подготовка (один раз)

Нужен Python 3.12 или новее.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
```

`requirements-dev.txt`:
- `pygame-ce` — графика и окно;
- `pyinstaller` — упаковка в `.exe` / бинарник;
- `typst` — вёрстка теории.

В готовую программу попадает только `pygame-ce`, остальное нужно лишь для сборки.

---

## 2. Запуск и проверка

Запустить программу:

```bash
.venv/Scripts/python main.py
```

Запустить сразу нужный экран:

```bash
.venv/Scripts/python main.py --screen demo
.venv/Scripts/python main.py --screen authors --lang en
```

Прогнать тесты (физика и интерфейс):

```bash
.venv/Scripts/python -m unittest discover -s tests -t .
```

---

## 3. Сборка архивов

Готовые архивы появляются в `dist/`:
- `NeimarkCorrelation-windows-x64.zip`;
- `NeimarkCorrelation-linux-x64.zip`.

В каждом архиве: программа, `theory_ru.pdf`, `theory_en.pdf`, `README.txt`.

### 3.1. Windows (собирается на Windows)

```bash
.venv/Scripts/pyinstaller --noconfirm --clean --distpath dist/windows --workpath build/work-windows build/neimark.spec
.venv/Scripts/python tools/package.py windows dist/windows/NeimarkCorrelation dist/NeimarkCorrelation-windows-x64.zip
```

Первая команда собирает папку `dist/windows/NeimarkCorrelation/` (`NeimarkCorrelation.exe` + `_internal/`). Вторая упаковывает её в zip вместе с теорией и README.

Проверить собранный exe:

```bash
dist/windows/NeimarkCorrelation/NeimarkCorrelation.exe
```

### 3.2. Linux (собирается в Docker на любой ОС)

1. Запусти Docker Desktop вручную и дождись, пока он полностью поднимется.
2. Выполни:

```bash
docker run --rm -v "C:/idk/phys:/src" python:3.12-slim-bullseye sh /src/build/build_linux.sh
```

Сборка идёт в Debian 11 (glibc 2.31), поэтому программа запускается на Ubuntu 20.04+, Debian 11+, Fedora 32+ и других дистрибутивах.

В Git Bash в начало команды нужно добавить `MSYS_NO_PATHCONV=1 `, иначе он портит путь `/src`. В PowerShell и cmd это не нужно.

### 3.3. Проверка Linux-архива на чистой системе (необязательно)

```bash
docker run --rm -v "C:/idk/phys:/src" ubuntu:20.04 sh /src/build/linux-test/run.sh ubuntu-20-04
```

Скрипт ставит в контейнер только виртуальный дисплей (Python там нет), распаковывает архив, запускает программу и сохраняет скриншоты в `build/linux-test/`. В конце выводит `OK ...`.

### 3.4. Когда что пересобирать

| Что изменилось | Что сделать |
|---|---|
| код в `ncorr/`, `main.py`, файлы в `assets/` (в т.ч. `authors.json`) | пересобрать оба архива (3.1 и 3.2) |
| текст теории в `theory/*.typ` | `python tools/build_theory.py`, потом пересобрать оба архива |
| рисунки теории или вид плоскости параметров | `python tools/make_figures.py`, `python tools/build_theory.py`, потом пересобрать оба архива |
| иконка | `python tools/make_icon.py`, потом пересобрать Windows |

Правки в коде сами в архивы не попадают. После любых изменений архивы нужно собрать заново.

---

## 4. Структура проекта

```
main.py                    точка входа, разбор аргументов командной строки
ncorr/                     код программы
├── app.py                 окно, главный цикл, переключение экранов, F11, кнопка языка
├── i18n.py                все надписи на русском и английском
├── theme.py               цвета, базовый размер шрифта, форматирование чисел
├── resources.py           пути к assets/ (и внутри сборки), загрузка шрифтов и картинок
├── physics/               физика и математика, без графики
│   ├── neimark.py         параметры осциллятора, правило yₙ → yₙ₊₁, генерация ряда, v(t)
│   ├── correlation.py     экспериментальная корреляционная функция
│   └── markov.py          точная теория: марковское разбиение, R(k) и C(τ)
├── screens/               экраны программы
│   ├── base.py            базовый класс экрана, шапка с логотипами МГУ и ВМК
│   ├── menu.py            главное меню
│   ├── motion.py          вкладка «Движение осциллятора»: пружина, фазовая траектория, v(t), отображение,
│   │                      две близкие траектории (случайность, точка бифуркации)
│   ├── demo.py            демонстрация: 4 графика + панель управления
│   ├── theory.py          теория: прокрутка страниц из assets/theory/
│   └── authors.py         авторы: данные из assets/authors.json
└── ui/                    элементы интерфейса
    ├── widgets.py         кнопка, переключатель, ползунок, вывод текста
    ├── plot.py            оси графиков, деления, пунктир, подложка под подписи
    ├── param_plane.py     плоскость параметров с областью хаоса ABC
    └── phase_portrait.py  фазовая плоскость (x, v): спираль, удары, движущаяся точка
assets/                    всё, что попадает внутрь программы
├── fonts/                 шрифты DejaVu (и лицензия)
├── img/                   логотипы МГУ и ВМК
├── authors/               фото авторов (сюда класть файлы)
├── authors.json           лектор, руководитель, авторы
└── theory/ru, theory/en   страницы теории картинками (генерируются)
theory/                    исходники теории
├── style.typ              общее оформление
├── theory_ru.typ          текст на русском
├── theory_en.typ          текст на английском
├── fig_*.png              рисунки (генерируются tools/make_figures.py)
└── theory_*.pdf           готовые PDF (генерируются, кладутся в архив)
tools/
├── make_figures.py        рисует рисунки для теории (theory/fig_*.png)
├── build_theory.py        собирает PDF и картинки теории из theory/*.typ
├── make_icon.py           рисует иконку build/icon.png и build/icon.ico
└── package.py             упаковывает сборку в zip с теорией и README
build/
├── neimark.spec           настройки PyInstaller (общие для Windows и Linux)
├── build_linux.sh         скрипт сборки внутри Docker
├── linux-test/run.sh      проверка Linux-архива на чистой системе
└── icon.png, icon.ico     иконка программы
tests/
├── test_physics.py        сверка с рис. 5 статьи и с экспериментом
└── test_ui_smoke.py       прогон интерфейса: кнопки, ползунки, язык, размеры окна
dist/                      готовые архивы (результат сборки)
```

---

## 5. Как это работает

### 5.1. Физика (`ncorr/physics/`)

**`neimark.py`**
- `Params(gamma, h)` — параметры. Свойства: `s` = √γ (растяжение за полпериода), `delta`, `lower` (нижний край аттрактора), `branch` (точка ветвления), `h_range()` (допустимые h при данном γ).
- `PRESETS` — точки H и E из статьи.
- `step(y, p)` — главное правило: `y → −√γ·y`, и если результат ≥ 1, вычесть `h`.
- `sequence(p, n, seed)` — ряд из `n` чисел `yₙ`. Первые 500 шагов отбрасываются, чтобы процесс вышел на стационарный режим.
- `shape`, `velocity` — непрерывная скорость v(t) внутри полупериода (для режима «непрерывный v(t)»).

**`correlation.py`**
- `Estimator(data)` — один раз вычисляет среднее и дисперсию.
- `normalized(k)` возвращает ρ(k) = R(k)/R(0) для одного сдвига. Считается по одному сдвигу за вызов, чтобы анимация строила столбики по очереди.

**`markov.py`**
- `build_partition(p)` — ищет марковское разбиение: итерирует края аттрактора и точку ветвления, пока не перестанут появляться новые точки. Если разбиение не замыкается, совпадающими считаются точки ближе заданной точности («приближённое»).
- `MarkovPartition.stationary()` — стационарная плотность.
- `MarkovPartition.moments(k)` — ⟨yₙ·yₙ₊ₖ⟩ через оператор Перрона–Фробениуса.
- `discrete_theory(p, kmax)` — теоретическая ρ(k) (оранжевый пунктир).
- `continuous_theory(...)` — теоретическая C(τ) для v(t).

### 5.2. Экран демонстрации (`ncorr/screens/demo.py`)

Константы в начале файла:
- `KMAX` — сколько сдвигов строить (30);
- `S`, `TAU_STEP`, `C_STEPS`, `CONT_HALF` — настройки непрерывного режима.

Путь данных:
1. Параметры меняются (пресет, ползунки, плоскость) → `_recompute()`: генерируется ряд, считается теория, создаётся `Estimator`.
2. Кнопки «Пуск», «Шаг», «Построить всё» → `_begin_step()` / `update()`: шаг анимации идёт по фазам:
   - копия сдвигается;
   - появляются произведения;
   - растёт столбик.
3. Каждый кадр `draw()` рисует всё заново:
   - `_draw_process()` — графики 1–3: ряд, копия, наложение;
   - `_draw_correlation()` — график 4: столбики и теория;
   - `_draw_info()` — числа в правой панели.

Фазовая плоскость: `self.cursor` — положение точки в полупериодах. Оно растёт в `update()` и обходит начало видимого окна (`_cursor_range()`). `PhasePortrait.draw()` рисует спираль для последних полупериодов, `_draw_cursor()` отмечает то же место на графике процесса.

Прочее:
- `layout()` пересчитывает положение всех элементов при изменении размера окна.
- `handle()` — мышь (колесо — масштаб, перетаскивание — прокрутка), пробел, стрелка вправо.

### 5.3. Остальное

- **`app.py`** хранит все экраны в словаре `screens`, `show(name)` переключает экран. Кнопка языка общая для всех экранов. В Linux отключается GL-ускорение окна (`SDL_FRAMEBUFFER_ACCELERATION=0`), чтобы программа работала и при сломанном OpenGL.
- **`i18n.py`**: каждая надпись — пара `("русский", "english")`. В коде надписи получают через `t("ключ")`.
- **`resources.py`** находит `assets/` и рядом с исходниками, и внутри собранной программы (`sys._MEIPASS`).

---

## 6. Частые правки

| Хочу | Где |
|---|---|
| поменять надпись или перевод | `ncorr/i18n.py` |
| поменять цвета | `ncorr/theme.py` (`POSITIVE`, `NEGATIVE`, `THEORY`, `SHIFTED`, …) |
| изменить авторов, лектора, руководителя | `assets/authors.json` |
| добавить фото автора | файл в `assets/authors/`, имя файла в поле `"photo"` в `authors.json` |
| изменить текст теории | `theory/theory_ru.typ`, `theory/theory_en.typ`, затем `python tools/build_theory.py` |
| число строящихся сдвигов | `KMAX` в `ncorr/screens/demo.py` |
| длина выборки по умолчанию | `self.n_samples` в `DemoScreen.__init__` (`demo.py`) |
| добавить пресет параметров | `PRESETS` в `neimark.py` и кнопку в `self.preset_sel` в `demo.py` |
| правило осциллятора | `step()` в `ncorr/physics/neimark.py` |
| что попадает в сборку | `build/neimark.spec` |
| README внутри архивов | словарь `README` в `tools/package.py` |

После правок: запустить тесты (раздел 2), затем пересобрать архивы (раздел 3).
