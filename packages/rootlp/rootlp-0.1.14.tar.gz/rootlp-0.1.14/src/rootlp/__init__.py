#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2026-01-10
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : rootLP

"""
A library that gathers root functions for custom script execution.
"""



# %% Source import
sources = {
'Section': 'rootlp.modules.Section_LP.Section',
'execution_panel': 'rootlp.modules.execution_panel_LP.execution_panel',
'main': 'rootlp.modules.main_LP.main',
'menu': 'rootlp.modules.menu_LP.menu',
'mo': 'rootlp.modules.mo_LP.mo',
'overview': 'rootlp.modules.overview_LP.overview',
'print': 'rootlp.modules.print_LP.print',
'project_server': 'rootlp.modules.project_server_LP.project_server',
'raw_code': 'rootlp.modules.raw_code_LP.raw_code',
'user_inputs': 'rootlp.modules.user_inputs_LP.user_inputs'
}



# %% Lazy imports
from corelp import getmodule
__getattr__, __all__ = getmodule(sources)