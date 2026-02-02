# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

"""
Created on Sun Aug 18 09:57:40 2019

@author: lpaone
"""

from pycivil.EXAStructural import templateRCRect as est

# import EXAStructural as es

# Setting new instance of section with
# id = 1 and name = "First Section"
section = est.RCTemplRectEC2(1, "First Section")
section.setElementType("beam")

# Setting dimension concrete
section.setDimH(500.0)
section.setDimW(300.0)

# Setting rebar
section.addSteelArea("MT", 40.0, 500.0)
section.addSteelArea("MB", 40.0, 1000.0)

# Setting materials
concrete = "C32/40"
steel = "B450C"
sigmacMax = 0.6 * 32
sigmasMax = 0.8 * 450
homogeneization = 15.0
section.setMaterials(concrete, steel, sigmacMax, sigmasMax, homogeneization)

print("Area di calcestruzzo: %1.3E [mm^2]" % section.calConcreteArea())
print("Area di acciaio:      %1.3E [mm^2]\n" % section.calSteelArea())

section.getSection()

print("Baricentro acciaio:")
print("------------------")
print(section.calBarycenterOfSteel())
print("\nBaricentro calcestruzzo:")
print("-----------------------")
print(section.calBarycenterOfConcrete())
print("\nBaricentro sezione omogeneizzata:")
print("--------------------------------")
print(section.calBarycenter())
print("\nArea calcestruzzo   : %1.3E" % section.calProp_Ac())
print("Area acciaio        : %1.3E" % section.calProp_As())
print("Area omogeneizzata  : %1.3E" % section.calProp_Ah())
print("Proprietà Scx       : %1.3E" % section.calProp_Scx())
print("Proprietà Ssx       : %1.3E" % section.calProp_Ssx())
print("Proprietà Shx       : %1.3E" % section.calProp_Shx())
print("Proprietà Scy       : %1.3E" % section.calProp_Scy())
print("Proprietà Ssy       : %1.3E" % section.calProp_Ssy())
print("Proprietà Shy       : %1.3E" % section.calProp_Shy())
print("Proprietà Icx       : %1.3E" % section.calProp_Icx())
print("Proprietà Isx       : %1.3E" % section.calProp_Isx())
print("Proprietà Ihx       : %1.3E" % section.calProp_Ihx())
print("Proprietà Icy       : %1.3E" % section.calProp_Icy())
print("Proprietà Isy       : %1.3E" % section.calProp_Isy())
print("Proprietà Ihy       : %1.3E" % section.calProp_Ihy())


sol = section.solverSLS_NM(N=-500.0 * 1e3, M=100.0 * 1e6)
print(f"sigma_c = {sol[0]:1.3E} - sigma_s = {sol[1]:2.3E} - xi = {sol[2]:3.3E} ")
print("\nCalcestruzzo con N < 0:")
print("-----------------------")
print(section.getConcrStress())
print("\nAcciaio con N < 0:")
print("-----------------")
print(section.getSteelStress())

sol = section.solverSLS_NM(N=+500.0 * 1e3, M=200.0 * 1e6)
print(sol)
print(f"sigma_c = {sol[0]:1.3E} - sigma_s = {sol[1]:2.3E} - xi = {sol[2]:3.3E} ")
print("\nCalcestruzzo con N > 0:")
print("-----------------------")
print(section.getConcrStress())
print("\nAcciaio con N > 0:")
print("-----------------")
print(section.getSteelStress())
