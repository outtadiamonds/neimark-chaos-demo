# Осциллятор Неймарка: динамический хаос и корреляционная функция

Компьютерная демонстрация для курса «Статистическая физика» (ВМК МГУ, https://cmcstatphys.ilc.msu.ru).
Авторы: В. А. Пупышев, А. С. Григорьев. Руководитель: О. А. Чичигина.

**Демонстрация** — две вкладки с переключателем сверху панели:
- **Движение осциллятора** (А. С. Григорьев, перенесено из его веб-версии) — груз на пружине, фазовая
  траектория, скорость v(t) как проекция траектории, отображение за полпериода; две близкие траектории
  (v₀ и v₀ + ε) показывают механизм появления случайности и точку бифуркации y*;
- **Корреляционная функция** (В. А. Пупышев) — наглядное построение: реализация → сдвинутая копия →
  наложение и произведения отклонений → очередной столбик R(k). Результат сравнивается с точной теорией
  (марковское разбиение, Стратонович–Рузмайкина–Чичигина, 1993).

## Для пользователя

Готовые архивы лежат в `dist/`:

- `NeimarkCorrelation-windows-x64.zip` — Windows 10/11, запуск `NeimarkCorrelation.exe`;
- `NeimarkCorrelation-linux-x64.zip` — Linux x86-64 (glibc ≥ 2.31), запуск `./NeimarkCorrelation`.
- `NeimarkCorrelation-dev-windows-x64.zip` — версия разработчика: F12 включает конструктор оформления;
  при выходе из него рядом собирается обновлённая обычная версия (PROJECT_GUIDE.md, раздел 11).

Ничего устанавливать не нужно: внутри архива есть всё, включая Python, шрифты и теорию в PDF.

Путеводитель по коду обеих частей для защиты: [PROJECT_GUIDE.md](PROJECT_GUIDE.md). Полное руководство по коду, архитектуре и сборке: [CODE_GUIDE.md](CODE_GUIDE.md). Краткая справка: [DEVELOPMENT.md](DEVELOPMENT.md).

Собрать архив одной командой: `.venv/Scripts/python tools/build.py` (Windows), `... tools/build.py linux` (Linux, нужен запущенный Docker Desktop) или двойной щелчок по `build.bat`.

## Структура

```
main.py                 точка входа
ncorr/physics/          физика без графики: отображение, марковская теория, оценка корреляции
ncorr/screens/          экраны: меню, вкладки демонстрации (движение, корреляционная функция), теория, авторы
ncorr/ui/               виджеты, оси графиков, плоскость параметров
ncorr/i18n.py           все надписи на русском и английском
assets/                 шрифты DejaVu, логотипы, страницы теории, authors.json
theory/                 исходники теории (Typst) и готовые PDF
tools/                  сборка теории, иконки, упаковка архивов
build/                  spec-файл PyInstaller и скрипт Linux-сборки
tests/                  проверка физики по статье и прогон интерфейса
```

## Разработка

```
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\python main.py
.venv\Scripts\python -m unittest discover -s tests -t .
```

Оформление (положение кнопок, тексты, шрифты, цвета) можно менять мышью: `python main.py`, затем F12 —
см. [PROJECT_GUIDE.md](PROJECT_GUIDE.md), раздел 11.

Авторы и руководитель заполняются в `assets/authors.json`, фото кладутся в `assets/authors/`
(имя файла указывается в поле `photo`). Код менять не нужно.

После правки текста теории: `python tools/build_theory.py` (пересобирает PDF и страницы для программы).

## Сборка

Windows (на Windows):

```
.venv\Scripts\python tools/make_icon.py
.venv\Scripts\pyinstaller --noconfirm --clean --distpath dist/windows --workpath build/work-windows build/neimark.spec
.venv\Scripts\python tools/package.py windows dist/windows/NeimarkCorrelation dist/NeimarkCorrelation-windows-x64.zip
```

Linux (в Docker, на любой ОС):

```
docker run --rm -v "<путь к проекту>:/src" python:3.12-slim-bullseye sh /src/build/build_linux.sh
```

Проверка Linux-архива на чистой системе без Python:

```
docker run --rm -v "<путь к проекту>:/src" ubuntu:20.04 sh /src/build/linux-test/run.sh ubuntu-20-04
```
