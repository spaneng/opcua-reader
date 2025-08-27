#!/bin/bash

set -e

rm -rf include/

mkdir include/
touch include/__init__.py

uv pip install --target=./include/ jinja2
uv pip install --target=./include/ weasyprint
uv pip install --target=./include/ tzlocal
uv pip install --target=./include/ pydoover

#uv pip install --target=./include/ git+https://github.com/spaneng/pydoover.git

# uv pip install --target=./include/ jinja2
# uv pip install --target=./include/ weasyprint
# uv pip install --target=./include/ tzlocal
# #  pip install --target=./include/ ../../pydoover
# uv pip install --target=./include/ pydoover