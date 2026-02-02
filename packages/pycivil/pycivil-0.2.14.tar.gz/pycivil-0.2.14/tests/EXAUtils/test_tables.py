# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path

import pycivil.EXAStructural.lawcodes.codeNTC2018 as Code
import pytest
from pycivil.EXAUtils.tables import Ex, Table


def test_table_codeNTC2018(tmp_path: Path):
    table = Code.WindActionsZones.tab01

    tab = Table(table)
    descr_1 = (
        "Valle d'Aosta, Piemonte, Lombardia,"
        "Trentino Alto Adige, Veneto, "
        "Friuli Venezia Giulia "
        "(con l'eccezione della provincia di Trieste)"
    )
    assert tab.valueAt(1) == (1, "Zona 1", descr_1, 25, 1000, 0.4)
    tab.setChoose(3)
    assert tab.choose() == 3
    pytest.raises(Ex, tab.setChoose, 0)

    print(tab)
