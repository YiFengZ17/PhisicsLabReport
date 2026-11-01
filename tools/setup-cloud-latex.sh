#!/usr/bin/env bash
# 在云端 Ubuntu 容器中安装编译报告所需的 XeLaTeX、中文字体与绘图依赖。
# 用法：bash tools/setup-cloud-latex.sh （也可把下面的命令粘贴进云端环境的 Setup script）
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq --no-install-recommends \
  texlive-xetex texlive-lang-chinese texlive-latex-extra texlive-science \
  texlive-pictures texlive-fonts-recommended lmodern latexmk \
  fonts-noto-cjk fonts-texgyre fonts-texgyre-math poppler-utils
pip install -q matplotlib numpy
