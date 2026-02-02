# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Any


class EXAExceptions(Exception):
    def __init__(self, error: str, message: str, number: Any = None) -> None:
        self.error = error
        self.message = message
        self.number = number
