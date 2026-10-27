#!/bin/sh
# Сборка Linux-версии в контейнере со старым glibc (2.31), чтобы программа запускалась
# на большинстве дистрибутивов. Запуск с хоста (из корня проекта):
#   docker run --rm -v "$PWD:/src" python:3.12-slim-bullseye sh /src/build/build_linux.sh
set -e
apt-get update -qq
apt-get install -y -qq --no-install-recommends binutils >/dev/null
pip install -q --root-user-action=ignore pygame-ce==2.5.8 pyinstaller==6.22.3
cd /src
pyinstaller --noconfirm --clean --log-level WARN --distpath /tmp/dist --workpath /tmp/work build/neimark.spec
python tools/package.py linux /tmp/dist/NeimarkCorrelation dist
