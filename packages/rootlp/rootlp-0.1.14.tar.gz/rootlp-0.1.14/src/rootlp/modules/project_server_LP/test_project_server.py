#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2026-01-18
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : rootLP
# Module        : project_server

"""
This file allows to test project_server

project_server : This module creates and run a custom marimo server for the project.
"""



# %% Libraries
from corelp import print, debug
import pytest
from rootlp import project_server
debug_folder = debug(__file__)



# %% Function test
def test_function() :
    '''
    Test project_server function
    '''
    print('Hello world!')



# %% Instance fixture
@pytest.fixture()
def instance() :
    '''
    Create a new instance at each test function
    '''
    return project_server()

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
    Test project_server return values
    '''
    assert project_server(*args, **kwargs) == expected, message



# %% Error test
@pytest.mark.parametrize("args, kwargs, error, error_message", [
    #([], {}, None, ""),
    ([], {}, None, ""),
])
def test_errors(args, kwargs, error, error_message) :
    '''
    Test project_server error values
    '''
    with pytest.raises(error, match=error_message) :
        project_server(*args, **kwargs)



# %% Test function run
if __name__ == "__main__":
    from corelp import test
    test(__file__)