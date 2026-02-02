# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from pycivil import EXAGeotechnical as geot
from pycivil import EXAParametric as param

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

title = "CENTROPADANA - tombino sottostrada - manufatto I.62 - DN 1000"
circle = param.CircularTubeShape01(
    descr=title, B=1000 + 200 + 300, H=1000 + 100 + 300 + 200, Tw=200, Tt=200, Tb=200
)

circle.assignTopLayer(soilTop)
circle.assignBotLayer(soilBot)
circle.springs()
print(circle)

circle.assignSeismicAction(0.065, 0.2)
circle.setTopCover(7600.0 - 600.0 + 150)
circle.setPaverThickness(600.0, 20.0)

circle.buildFEModel()

circle.model().save("circular", ".msh")
