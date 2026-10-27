"""Делает из собранной программы обе версии и архивы для сайта (см. ncorr/packaging.py).

python tools/package.py <windows|linux> <папка сборки NeimarkCorrelation> <папка для архивов>

Результат:
    <папка сборки>                         обычная версия (README и теория положены внутрь)
    <рядом>/NeimarkCorrelation-dev         версия разработчика (с конструктором F12)
    <папка для архивов>/NeimarkCorrelation-<платформа>-x64.zip       — для сайта
    <папка для архивов>/NeimarkCorrelation-dev-<платформа>-x64.zip   — для себя
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from ncorr import packaging  # noqa: E402


def main(platform, app_dir, dist_dir):
    for out in packaging.make_both(platform, app_dir, dist_dir, os.path.join(ROOT, "theory")):
        print(out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main(*sys.argv[1:4])
