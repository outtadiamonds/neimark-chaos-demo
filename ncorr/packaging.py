"""Две версии программы и архивы для сайта.

Обе версии — одна и та же собранная программа:
    NeimarkCorrelation      — обычная, для показа (её и выкладывают на сайт);
    NeimarkCorrelation-dev  — версия разработчика: в ней работает конструктор (F12).
Версию разработчика отличает только файл-метка assets/dev_edition.txt. Поэтому версия разработчика
может сама собрать обычную версию: скопировать свою папку без метки, положить туда текущий
design.json и упаковать в zip. Для этого не нужны ни Python, ни PyInstaller (export_show).

Модуль используют tools/package.py (при сборке из исходников) и devmode.py (в самой программе).
"""
import os
import shutil
import sys
import zipfile

NAME = "NeimarkCorrelation"
DEV_NAME = NAME + "-dev"
MARKER = "dev_edition.txt"

_SHOW = {
    "windows": """Осциллятор Неймарка: динамический хаос и корреляционная функция
Компьютерная демонстрация по курсу «Статистическая физика», ВМК МГУ.

Запуск: откройте папку и запустите NeimarkCorrelation.exe.
Ничего устанавливать не нужно. Требуется 64-битная Windows 10 или 11.
Если Windows показывает «Система Windows защитила ваш компьютер»,
нажмите «Подробнее» → «Выполнить в любом случае» (программа не подписана).

Теория: theory_ru.pdf (на русском), theory_en.pdf (in English).
Язык интерфейса переключается кнопкой English/Русский. F11 — полноэкранный режим.

----
Neimark oscillator: dynamic chaos and the correlation function
Run NeimarkCorrelation.exe. Nothing needs to be installed (64-bit Windows 10/11).
""",
    "linux": """Осциллятор Неймарка: динамический хаос и корреляционная функция
Компьютерная демонстрация по курсу «Статистическая физика», ВМК МГУ.

Запуск: распакуйте архив и запустите файл NeimarkCorrelation в папке программы
(двойной щелчок или в терминале: ./NeimarkCorrelation).
Ничего устанавливать не нужно. Требуется 64-битный Linux (x86-64) с графическим
окружением (X11 или Wayland) и glibc 2.31 или новее (Ubuntu 20.04+, Debian 11+,
Fedora 32+, Astra Linux 1.7+ и т. п.).
Если файл не запускается, сделайте его исполняемым: chmod +x NeimarkCorrelation

Теория: theory_ru.pdf (на русском), theory_en.pdf (in English).
Язык интерфейса переключается кнопкой English/Русский. F11 — полноэкранный режим.

----
Neimark oscillator: dynamic chaos and the correlation function
Unpack and run ./NeimarkCorrelation. Nothing needs to be installed
(x86-64 Linux with a graphical session, glibc 2.31 or newer).
""",
}

_DEV = """ВЕРСИЯ РАЗРАБОТЧИКА (с конструктором оформления). Не для выкладки на сайт.

F12 — режим разработчика: мышью двигаются и растягиваются кнопки, заголовки и графики,
меняются тексты (кнопка «Все тексты»), шрифты и цвета. Всё сохраняется в
_internal/assets/design.json.

Когда вы выходите из режима разработчика (F12 или закрытие окна), программа сама собирает
рядом с этой папкой обычную версию для показа:
    ../NeimarkCorrelation/                        — готовая к запуску папка
    ../NeimarkCorrelation-{platform}-x64.zip      — архив для сайта
Обычную версию можно сразу запускать и отдавать: режима разработчика в ней нет.

Остальное — как в обычной версии:
"""

MARKER_TEXT = ("Эта метка включает конструктор оформления (F12). В обычной версии программы её нет.\n"
               "This marker enables the design editor (F12). The regular version does not contain it.\n")


def platform_name():
    return "windows" if sys.platform == "win32" else "linux"


def exe_name(platform):
    return NAME + (".exe" if platform == "windows" else "")


def assets_dir(app_dir):
    """Папка assets внутри собранной программы (PyInstaller 6, режим onedir)."""
    return os.path.join(app_dir, "_internal", "assets")


def readme(platform, dev):
    text = (_DEV.format(platform=platform) if dev else "") + _SHOW[platform]
    return text.replace("\n", "\r\n") if platform == "windows" else text


def fill_folder(platform, folder, dev, pdf_dir=None, files=None):
    """Положить в папку программы README, теорию, метку версии разработчика и файлы assets (имя → байты)."""
    with open(os.path.join(folder, "README.txt"), "w", encoding="utf-8", newline="") as f:
        f.write(readme(platform, dev))
    if pdf_dir:
        for lang in ("ru", "en"):
            shutil.copy2(os.path.join(pdf_dir, f"theory_{lang}.pdf"), folder)
    assets = assets_dir(folder)
    marker = os.path.join(assets, MARKER)
    if dev:
        with open(marker, "w", encoding="utf-8") as f:
            f.write(MARKER_TEXT)
    elif os.path.exists(marker):
        os.remove(marker)
    for name, data in (files or {}).items():
        with open(os.path.join(assets, name), "wb") as f:
            f.write(data)


def zip_folder(platform, folder, out, root):
    """Упаковать папку программы в zip с корневой папкой root (исполняемый бит Linux сохраняется).

    Архив пишется во временный файл и подменяется в конце: недописанный zip не появится.
    """
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    tmp = out + ".part"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for base, _, files in os.walk(folder):
            for name in sorted(files):
                full = os.path.join(base, name)
                arc = os.path.join(root, os.path.relpath(full, folder)).replace(os.sep, "/")
                info = zipfile.ZipInfo.from_file(full, arc)
                if platform == "linux" and name == NAME:
                    info.external_attr = 0o100755 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                with open(full, "rb") as f:
                    z.writestr(info, f.read())
    os.replace(tmp, out)
    return out


def make_both(platform, show_dir, dist_dir, pdf_dir):
    """При сборке: из папки PyInstaller сделать обе версии и оба архива."""
    fill_folder(platform, show_dir, dev=False, pdf_dir=pdf_dir)
    zips = [zip_folder(platform, show_dir, os.path.join(dist_dir, f"{NAME}-{platform}-x64.zip"), NAME)]
    dev_dir = os.path.join(os.path.dirname(show_dir), DEV_NAME)
    shutil.rmtree(dev_dir, ignore_errors=True)
    shutil.copytree(show_dir, dev_dir)
    fill_folder(platform, dev_dir, dev=True)
    zips.append(zip_folder(platform, dev_dir, os.path.join(dist_dir, f"{DEV_NAME}-{platform}-x64.zip"), DEV_NAME))
    return zips


def export_show(app_dir, files, out_dir=None, zip_dir=None):
    """Собрать обычную версию из версии разработчика app_dir; files — {"design.json": байты, …} для assets.

    Возвращает (папка, архив). Папка: out_dir/NeimarkCorrelation, архив — в zip_dir (по умолчанию там же).
    """
    platform = platform_name()
    out_dir = out_dir or os.path.dirname(os.path.abspath(app_dir))
    show = os.path.join(out_dir, NAME)
    if os.path.abspath(show) == os.path.abspath(app_dir):  # версия разработчика сама лежит в папке с этим именем
        show = os.path.join(out_dir, NAME + "-show")
    if os.path.exists(show):
        if not os.path.isfile(os.path.join(show, exe_name(platform))):
            raise RuntimeError(f"папка {show} занята другими файлами — переименуйте её")
        shutil.rmtree(show)  # если обычная версия сейчас запущена, здесь будет ошибка «файл занят»
    shutil.copytree(app_dir, show, ignore=shutil.ignore_patterns(MARKER))
    fill_folder(platform, show, dev=False, files=files)
    archive = zip_folder(platform, show, os.path.join(zip_dir or out_dir, f"{NAME}-{platform}-x64.zip"), NAME)
    return show, archive
