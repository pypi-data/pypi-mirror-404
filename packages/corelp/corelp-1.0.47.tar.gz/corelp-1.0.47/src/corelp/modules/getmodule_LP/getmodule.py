#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2025-08-25
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : coreLP
# Module        : getmodule

"""
This function is to be used in a library __init__ file. It creates lazy imports of the module imported and defines __getattr__ and __all__ for this library.
"""



# %% Libraries
import importlib



# %% Function
def getmodule(sources) :
    f'''
    This function is to be used in a library __init__ file. It creates lazy imports of the module imported and defines __getattr__ and __all__ for this library from a sources dictionnary dict("object"="path2object").
    
    Parameters
    ----------
    sources : dict
        source dictionnary.

    Returns
    -------
    _getattr : function
        Function to replace __getattr__ variable.
    _all : list
        list of module names corresponding to __all__.

    Raises
    ------
    AttributeError
        When trying to import a module which is not in the library.

    Examples
    --------
    >>> from corelp import getmodule
    ...
    >>> # In __init__.py file
    ... __getattr__, __all__ = getmodule(sources)
    '''

    # Name
    first_key = list(sources.keys())[0]
    name = sources[first_key].split('.')[0]

    # Objects to return
    _lazy = {}
    _all = list(sources.keys())
    def _getattr(attr) :

        # Cached
        if attr in _lazy:
            return _lazy[attr]

        try :
            module = sources.get(attr, None)
            if module is None :
                raise KeyError(f"{attr} was not found in sources")
        except KeyError:
            raise AttributeError(f'module {name} has no attribute {attr}')

        mod = importlib.import_module(module)
        obj = getattr(mod, attr, None)
        if obj is None :
            raise AttributeError(f"module {module} has no object {attr}")
        _lazy[attr] = obj  # Cache it
        return obj

    return _getattr, _all



# %% Test function run
if __name__ == "__main__":
    from corelp import test
    test(__file__)