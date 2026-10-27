#!/bin/sh
# Проверка Linux-архива на чистой системе без Python: распаковать и снять скриншоты.
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq --no-install-recommends xvfb xauth unzip >/dev/null
cd /tmp && unzip -q /src/dist/NeimarkCorrelation-linux-x64.zip
ls -l NeimarkCorrelation/NeimarkCorrelation
cd NeimarkCorrelation
xvfb-run -a -s "-screen 0 1600x900x24" ./NeimarkCorrelation --size 1600x900 --screen motion --preset H --seconds 45 --frames 30 --screenshot /src/build/linux-test/$1-motion.png
xvfb-run -a -s "-screen 0 1600x900x24" ./NeimarkCorrelation --size 1600x900 --screen demo --steps 5 --frames 10 --screenshot /src/build/linux-test/$1-demo.png
xvfb-run -a -s "-screen 0 1600x900x24" ./NeimarkCorrelation --size 1600x900 --lang en --frames 5 --screenshot /src/build/linux-test/$1-menu.png
echo "OK $1 $(ldd --version | head -1)"
