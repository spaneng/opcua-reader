#!/usr/bin/env python3

import os
import sys

## Add the current directory of the file to the path if it is not already there.
current_dir = os.path.dirname(__file__)
if not current_dir in sys.path:
    sys.path.append(current_dir)

from injector_report import generator

