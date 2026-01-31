#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2026-01-18
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : rootLP
# Module        : menu

"""
This module creates a menu on the side of the marimo window.
"""



# %% Libraries
from pathlib import Path
import marimo as mo



# %% Function
def menu(project) :
    '''
    This module creates a menu on the side of the marimo window.
    
    Parameters
    ----------
    project : module
        project module described by menu.

    Examples
    --------
    >>> from rootlp import menu
    >>> import myproject
    ...
    >>> menu(myproject)
    '''

    # Mode
    if project is None :
        return
    if mo.app_meta().mode == "edit" :
        return

    # Folder
    folder = Path(project.__file__).parent # project / __init__.py
    name = folder.name

    # Analyse sources
    nav_menu = {}
    process_menu = {}
    analyse_menu = {}
    for source in project.sources.values() :
        split = source.split(".") # project.folder.module_LP.module
        if split[0] != name : raise SyntaxError('Project name is not consistent in sources')
        if len(split) != 4 : continue
        icon = get_icon(folder, split)
        match split[1] :
            case "pages" : nav_menu[f'/{name}/{split[3]}'] = f'{icon}{func2title(split[3])}'
            case "process" : process_menu[f'/{name}/{split[3]}'] = f'{icon}{func2title(split[3])}'
            case "analyse" : analyse_menu[f'/{name}/{split[3]}'] = f'{icon}{func2title(split[3])}'
            case _ : pass
    if len(process_menu) :
        nav_menu['Process'] = {}
        for key, value in process_menu.items() :
            nav_menu[key] = value
    if len(analyse_menu) :
        nav_menu['Analyse'] = {}
        for key, value in analyse_menu.items() :
            nav_menu[key] = value

    # Sidebar
    sidebar = mo.sidebar(
    [
        mo.md(f"# {func2title(name)}"),
        mo.nav_menu(nav_menu, orientation="vertical"),
    ]
)

    return sidebar



def func2title(name) :
    capital = name[0].upper()
    name = name[1:].lower()
    name = name.replace('_', ' ')
    name = name.replace('2', ' to ')
    return f'{capital}{name}'



def get_icon(folder, split) :
    icon_file = folder / f'{split[1]}/{split[2]}/icon.txt'
    if not icon_file.exists() :
        return ''
    return mo.icon(f'lucide:{icon_file.read_text()}')



# %% Test function run
if __name__ == "__main__":
    from corelp import test
    test(__file__)