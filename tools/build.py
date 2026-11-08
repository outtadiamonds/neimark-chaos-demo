"""Сборка одной командой.

    python tools/build.py               # Windows: тесты + PyInstaller + обе версии (обычная и разработчика) в zip
    python tools/build.py linux         # Linux-архив в Docker (Docker Desktop должен быть уже запущен)
    python tools/build.py all           # оба архива
    python tools/build.py theory        # рисунки + PDF и страницы теории
    python tools/build.py test          # только тесты
    python tools/build.py run           # запустить программу из исходников

Флаги:
    --no-tests   не запускать тесты перед сборкой (быстрее, но рискованнее)
    --check      после сборки запустить собранную программу и сохранить скриншот в build/check-*.png
"""
import os
import shutil
import subprocess
import sys
import time
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "NeimarkCorrelation"
PY = sys.executable  # тот Python, которым запущен скрипт (обычно .venv)
DOCKER_IMAGE = "python:3.12-slim-bullseye"


def run(cmd, **kw):
    print("\n>", " ".join(cmd), flush=True)
    result = subprocess.run(cmd, cwd=ROOT, **kw)
    if result.returncode != 0:
        sys.exit(f"\nОшибка: команда завершилась с кодом {result.returncode}")


def tests():
    run([PY, "-m", "unittest", "discover", "-s", "tests", "-t", "."])


def theory():
    run([PY, os.path.join("tools", "make_figures.py")])
    run([PY, os.path.join("tools", "build_theory.py")])


def copy_atomic(src, dst):
    """Не обрезать старый файл: PNG иногда удерживается Windows как mapped section.

    Новый файл сначала целиком записывается рядом; NTFS может заменить имя,
    оставив старое содержимое доступным его текущему читателю.
    """
    handle, staged = tempfile.mkstemp(prefix=".build-", suffix=".part", dir=os.path.dirname(dst))
    os.close(handle)
    try:
        shutil.copy2(src, staged)
        for attempt in range(10):
            try:
                os.replace(staged, dst)
                return dst
            except PermissionError:
                if attempt == 9:
                    raise
                time.sleep(0.2)
    finally:
        if os.path.exists(staged):
            os.remove(staged)


def windows(check):
    if sys.platform != "win32":
        sys.exit("Windows-версию можно собрать только на Windows (PyInstaller не собирает под другую ОС).")
    # Проверяем блокировки до каких-либо изменений в существующих сборках.
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                  ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    paths = []
    target = os.path.join(ROOT, "dist", "windows")
    for base, _, files in os.walk(target):
        paths.extend(os.path.join(base, name) for name in files)
    for name in (NAME, NAME + "-dev"):
        archive = os.path.join(ROOT, "dist", name + "-windows-x64.zip")
        if os.path.isfile(archive):
            paths.append(archive)
    for path in paths:
        handle = kernel.CreateFileW(path, 0x80000000, 0, None, 3, 0, None)
        if handle == ctypes.c_void_p(-1).value:
            sys.exit("Сборка остановлена до изменения файлов: файл занят или недоступен. "
                     "Закройте программу и открытые ZIP-архивы: " + path)
        kernel.CloseHandle(handle)
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    # Компиляция и упаковка сначала во временную папку. Ошибка оставляет старую версию целой.
    with tempfile.TemporaryDirectory(prefix="package-", dir=os.path.join(ROOT, "build")) as stage:
        apps = os.path.join(stage, "windows")
        run([PY, "-m", "PyInstaller", "--noconfirm", "--clean", "--log-level", "WARN",
             "--distpath", apps, "--workpath", os.path.join(stage, "work"),
             os.path.join(ROOT, "build", "neimark.spec")])
        run([PY, os.path.join("tools", "package.py"), "windows", os.path.join(apps, NAME), stage])
        # Windows может держать сам каталог открытым в Проводнике.
        # Не переименовываем каталог: переносим только готовые файлы поверх.
        shutil.copytree(apps, target, dirs_exist_ok=True, copy_function=copy_atomic)
        for name in (NAME, NAME + "-dev"):
            archive = name + "-windows-x64.zip"
            os.replace(os.path.join(stage, archive), os.path.join(ROOT, "dist", archive))
    if check:
        exe = os.path.join(ROOT, "dist", "windows", NAME, NAME + ".exe")
        shot = os.path.join(ROOT, "build", "check-windows.png")
        run([exe, "--size", "1366x768", "--screen", "motion", "--preset", "H", "--seconds", "45", "--frames", "60",
             "--screenshot", shot])
        shot2 = os.path.join(ROOT, "build", "check-windows-corr.png")
        run([exe, "--size", "1366x768", "--screen", "demo", "--steps", "3", "--frames", "60", "--screenshot", shot2])
        print("Скриншоты собранной программы:", shot, shot2)


def docker_ready():
    try:
        return subprocess.run(["docker", "info"], capture_output=True).returncode == 0
    except FileNotFoundError:
        return False


def linux(check):
    if not docker_ready():
        sys.exit("Docker не запущен. Откройте Docker Desktop вручную, дождитесь, пока он загрузится, "
                 "и повторите команду.")
    mount = ROOT.replace("\\", "/") + ":/src"
    run(["docker", "run", "--rm", "-v", mount, DOCKER_IMAGE, "sh", "/src/build/build_linux.sh"])
    if check:
        run(["docker", "run", "--rm", "-v", mount, "ubuntu:20.04", "sh", "/src/build/linux-test/run.sh", "check"])
        print("Скриншоты:", os.path.join(ROOT, "build", "linux-test"))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    target = args[0] if args else "windows"
    check = "--check" in flags
    started = time.time()

    if target == "test":
        tests()
    elif target == "theory":
        theory()
    elif target == "run":
        run([PY, "main.py"])
    elif target in ("windows", "linux", "all"):
        if "--no-tests" not in flags:
            tests()
        if target in ("windows", "all"):
            windows(check)
        if target in ("linux", "all"):
            linux(check)
        print("\nГотово. Архивы в папке dist:")
        for name in sorted(os.listdir(os.path.join(ROOT, "dist"))):
            if name.endswith(".zip"):
                full = os.path.join(ROOT, "dist", name)
                stamp = time.strftime("%d.%m %H:%M", time.localtime(os.path.getmtime(full)))
                print(f"  {name}  ({os.path.getsize(full) // 1024} КБ, собран {stamp})")
    else:
        sys.exit(__doc__)
    print(f"\nВремя: {time.time() - started:.0f} с")


if __name__ == "__main__":
    main()
