#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2026-01-23
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : coreLP
# Module        : icon

"""
This file allows to test icon

icon : This module gives the path to pythonLP icon.
"""



# %% Libraries
from corelp import print, debug
import pytest
from corelp import icon
debug_folder = debug(__file__)



# %% Function test
def test_function() :
    '''
    Test icon function
    '''
    print('Hello world!')



# %% Instance fixture
@pytest.fixture()
def instance() :
    '''
    Create a new instance at each test function
    '''
    return icon()

def test_instance(instance) :
    '''
    Test on fixture
    '''
    pass


# %% Returns test
@pytest.mark.parametrize("args, kwargs, expected, message", [
    #([], {}, None, ""),
    ([], {}, None, ""),
])
def test_returns(args, kwargs, expected, message) :
    '''
    Test icon return values
    '''
    assert icon(*args, **kwargs) == expected, message



# %% Error test
@pytest.mark.parametrize("args, kwargs, error, error_message", [
    #([], {}, None, ""),
    ([], {}, None, ""),
])
def test_errors(args, kwargs, error, error_message) :
    '''
    Test icon error values
    '''
    with pytest.raises(error, match=error_message) :
        icon(*args, **kwargs)



# %% Test function run
if __name__ == "__main__":
    from corelp import test
    test(__file__)