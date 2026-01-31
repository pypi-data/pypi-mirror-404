#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2025-08-25
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : coreLP

"""
A library that gathers core functions for python programming.
"""



# %% Source import
sources = {
'Path': 'corelp.modules.Path_LP.Path',
'debug': 'corelp.modules.debug_LP.debug',
'folder': 'corelp.modules.folder_LP.folder',
'getmodule': 'corelp.modules.getmodule_LP.getmodule',
'icon': 'corelp.modules.icon_LP.icon',
'kwargsself': 'corelp.modules.kwargsself_LP.kwargsself',
'prop': 'corelp.modules.prop_LP.prop',
'rfrom': 'corelp.modules.rfrom_LP.rfrom',
'selfkwargs': 'corelp.modules.selfkwargs_LP.selfkwargs',
'test': 'corelp.modules.test_LP.test'
}



# %% Lazy imports
if __name__ == "__main__":
    from modules.getmodule_LP.getmodule import getmodule # type: ignore
else :
    from .modules.getmodule_LP.getmodule import getmodule
__getattr__, __all__ = getmodule(sources)