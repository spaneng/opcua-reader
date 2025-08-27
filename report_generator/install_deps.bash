#!/usr/bin/bash

set -e

rm -rf include/

mkdir include/
touch include/__init__.py

python -m pip install --target=./include/ jinja2
python -m pip install --target=./include/ weasyprint
python -m pip install --target=./include/ tzlocal

# python -m pip install --target=./include/ pydoover
python -m pip install --target=./include/ git+https://github.com/spaneng/pydoover.git

# uv pip install --target=./include/ jinja2
# uv pip install --target=./include/ weasyprint
# uv pip install --target=./include/ tzlocal
# #  pip install --target=./include/ ../../pydoover
# uv pip install --target=./include/ pydoover