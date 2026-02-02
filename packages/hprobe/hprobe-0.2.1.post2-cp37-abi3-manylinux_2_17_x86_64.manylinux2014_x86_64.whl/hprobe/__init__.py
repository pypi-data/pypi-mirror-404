import os
from pathlib import Path

# Rust 扩展模块
from .hprobe import *  # noqa

# 透传 Rust doc / __all__
import hprobe as _rust_mod

__doc__ = _rust_mod.__doc__
if hasattr(_rust_mod, "__all__"):
    __all__ = _rust_mod.__all__

if "HPROBE_DATA_ROOT" not in os.environ:
    PACKAGE_ROOT = Path(__file__).resolve().parent
    os.environ["HPROBE_DATA_ROOT"] = str(PACKAGE_ROOT)

# debug
# print(f"[hprobe] DATA_ROOT = {os.environ['HPROBE_DATA_ROOT']}")
