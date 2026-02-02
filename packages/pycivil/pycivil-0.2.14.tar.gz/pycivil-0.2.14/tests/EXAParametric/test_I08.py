# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import sys
import pytest
from pathlib import Path
from filecmp import cmp

from pycivil.EXAGeotechnical import base as geot
from pycivil.EXAParametric import tube as param

def test_tube_001(tmp_path: Path) -> None:

    E_top = geot.ModulusYoung()
    E_top.setChoose(9)
    Et = (E_top.value()[2] + E_top.value()[2]) / 2 * 0.1

    E_bot = geot.ModulusYoung()
    E_bot.setChoose(2)
    Eb = (E_bot.value()[2] + E_bot.value()[2]) / 2 * 0.1

    ni_top = geot.RatioPoisson()
    ni_top.setChoose(5)
    nit = (ni_top.value()[2] + ni_top.value()[2]) / 2

    ni_bot = geot.RatioPoisson()
    ni_bot.setChoose(3)
    nib = (ni_bot.value()[2] + ni_bot.value()[2]) / 2

    soilTop = geot.SoilLayer("Terreno superiore - Ghiaia")
    soilTop.setEt(Et)
    soilTop.setNit(nit)
    soilTop.setDry(gamma=20, phi=30, coe=0)
    print(soilTop)

    soilBot = geot.SoilLayer("Terreno inferiore - Argilla Limosa")
    soilBot.setEt(Eb)
    soilBot.setNit(nib)
    soilBot.setCu(0.05)
    print(soilBot)

    title = "CENTROPADANA - tombino sottostrada - manufatto I.08 - DN 1000"
    circle = param.CircularTubeShape01(
        descr=title, B=1000 + 200 + 300, H=1000 + 100 + 300 + 200, Tw=200, Tt=200, Tb=200
    )

    circle.assignTopLayer(soilTop)
    circle.assignBotLayer(soilBot)

    circle.springs()
    print(circle)

    circle.assignSeismicAction(0.261, 0.2)
    circle.setTopCover(600.0 - 300.0 + 150)
    circle.setPaverThickness(300.0, 20.0)

    circle.buildFEModel()

    fileName = "I08"
    fileExtension = ".mgt"
    circle.exportFEModel(str(tmp_path / f"{fileName}"), fileExtension)
    filePath = tmp_path / f"{fileName}{fileExtension}"
    circle.model().clear()

    assert filePath.exists()

    file_benchmark = Path(__file__).parent / Path(f"{fileName}{fileExtension}")
    assert cmp(file_benchmark, filePath, False)

if __name__ == "__main__":
    sys.exit(pytest.main(Path(__file__)))
