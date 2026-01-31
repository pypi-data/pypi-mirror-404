#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2026-01-23
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : coreLP
# Module        : icon

"""
This module gives the path to pythonLP icon.
"""



# %% Libraries
from pathlib import Path




# %% Function
def icon() :
    '''
    This module gives the path to pythonLP icon.
    
    Returns
    -------
    path : pathlib.Path
        path to icon.

    Examples
    --------
    >>> from corelp import icon
    ...
    >>> icon()
    '''

    folder = Path(__file__).parents[2] # corelp / modules / icon_LP / icon.py
    return folder / 'icon_pythonLP.png'



# %% Test function run
if __name__ == "__main__":
    from corelp import test
    test(__file__)