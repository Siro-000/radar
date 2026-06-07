"""Radar — semantic recall layer.

Set native-library workarounds before any submodule imports torch / faiss /
tokenizers. On macOS the OpenMP runtime ships in several wheels (torch, faiss,
tokenizers) and loading more than one copy aborts the process with a SIGSEGV
(exit 139). These must be set in the environment *before* the native libs load,
so this package __init__ is the single correct place. ``setdefault`` keeps any
value the user already exported.
"""

import os as _os

_os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
_os.environ.setdefault("OMP_NUM_THREADS", "1")
_os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
