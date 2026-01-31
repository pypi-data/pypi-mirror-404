#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2026-01-18
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : rootLP
# Module        : menu

"""
This file allows to test menu

menu : This module creates a menu on the side of the marimo window.
"""



# %% Libraries
from corelp import print, debug
import pytest
from rootlp import menu
debug_folder = debug(__file__)



# %% Function test
def test_function() :
    '''
    Test menu function
    '''
    print('Hello world!')



# %% Instance fixture
@pytest.fixture()
def instance() :
    '''
    Create a new instance at each test function
    '''
    return menu()

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
    Test menu return values
    '''
    assert menu(*args, **kwargs) == expected, message



# %% Error test
@pytest.mark.parametrize("args, kwargs, error, error_message", [
    #([], {}, None, ""),
    ([], {}, None, ""),
])
def test_errors(args, kwargs, error, error_message) :
    '''
    Test menu error values
    '''
    with pytest.raises(error, match=error_message) :
        menu(*args, **kwargs)



# %% Test function run
if __name__ == "__main__":
    from corelp import test
    test(__file__)