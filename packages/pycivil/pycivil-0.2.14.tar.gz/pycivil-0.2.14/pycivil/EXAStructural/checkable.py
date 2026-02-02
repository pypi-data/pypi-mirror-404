# Copyright (c) 2026 Luigi Paone <ppc.luigi.paone@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from copy import deepcopy
from enum import Enum
from typing import List, Dict, Any

from pycivil.EXAUtils.EXAExceptions import EXAExceptions as Ex
from pycivil.EXAStructural.codes import Code
from pycivil.EXAStructural.loads import ForcesOnSection


class Checkable:
    def __init__(self):
        self.__results = {}
        self.__ck = None
        self.__criteria = None
        self.__criteriaForCheck = []
        self.__code = None
        self.__loads = None
        self.__loadsSelector = None

    def _getResults(self):
        return self.__results

    def _setCode(self, code: Code) -> None:
        if not isinstance(code, Code):
            raise Ex("002", "code must be a Code type", type(code))
        self.__code = code

    def _setLoads(self, loads: List[ForcesOnSection]) -> None:
        if not isinstance(loads, list):
            raise Ex("001", "loads must be a list type", type(loads))
        self.__loads = loads

    def _setCriteria(self, criteria: List[str]) -> None:
        self.__criteria = criteria

    def _setCheckableObj(self, obj):
        self.__ck = obj

    def _setLoadsSelector(self, s):
        if not isinstance(s, list):
            raise Ex("001", "s must be a list type", type(s))
        self.__loadsSelector = s

    def _validateCriteria(self, criteria: List[str]) -> None:
        if not isinstance(criteria, list):
            raise Ex("0001", "criteria must be a List[str]", type(criteria))

        for v in criteria:
            if not isinstance(v, str):
                raise Ex("0001", "criteria must be a List[str]", type(v))
            assert self.__criteria is not None
            if v not in self.__criteria:
                raise Ex("0001", "value is not in criteria", v)

        self.__criteriaForCheck = criteria

    def _ck(self):
        return self.__ck

    def _criteriaForCheck(self):
        return self.__criteriaForCheck

    def check(
        self,
        criteria: List[str],
        loads: List[ForcesOnSection],
        law: Code,
        loadSelector: List[List[int]],
    ) -> Dict[Any, Any]:
        raise NotImplementedError("Need to be implemented")

    def getResults(self):
        return deepcopy(self.__results)


class Checker:
    def __init__(self):
        self.__checkable = None
        self.__results: Dict[Any, Any] | None = None

    def _setResults(self, r):
        if isinstance(r, dict):
            self.__results = r
        else:
            raise TypeError("arguments must be a dict type")

    def check(
        self,
        criteria: List[str],
        loads: List[ForcesOnSection],
        law: Code,
        loadsSelector: List[List[int]] | None = None,
    ) -> None:
        if self.__checkable is None:
            raise ValueError("Before launch check need to use setCheckable() method")
        if loadsSelector is None:
            loadsSelector = []
        self.__results = self.__checkable.check(criteria, loads, law, loadsSelector)

    def setCheckable(self, c: Checkable) -> None:
        if not isinstance(c, Checkable):
            raise TypeError("arguments must be a checkable")

        self.__checkable = c

    def getResults(self) -> Dict[Any, Any] | None:
        return self.__results


class CheckableCriteriaEnum(str, Enum):
    SLE_NM = "SLE-NM"
    SLE_F = "SLE-F"
    SLU_NM = "SLU-NM"
    SLU_T = "SLU-T"
    SLU_NM_FIRE = "SLU-NM-FIRE"
