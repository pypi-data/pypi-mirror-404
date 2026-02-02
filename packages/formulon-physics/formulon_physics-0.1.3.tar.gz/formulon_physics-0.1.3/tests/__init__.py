# SPDX-FileCopyrightText: 2026-present SRIKALEESWARAR-S <srikaleeswarar675@gmail.com>
#
# SPDX-License-Identifier: MIT
"""
formulon
========

An open-source Python library providing classical physics formulas with
automatic input validation and NumPy support.

Designed for educational, scientific, and engineering use.
"""

from .__about__ import __version__

# --- Public physics formula modules ---
from .classicalphysics import *

# --- Public API ---
__all__ = [
    "__version__",
]

