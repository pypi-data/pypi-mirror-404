#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2026-01-25
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : rootLP
# Module        : raw_code

"""
This modules gives the raw code inside a code editor view.
"""



# %% Libraries
import marimo as mo



# %% Function
def raw_code(name, code_editor) :
    '''
    This modules gives the raw code inside a code editor view.
    
    Parameters
    ----------
    name : str
        Name of script.
    code_editor : mo.code_editor
        Editor containing main script code.

    Returns
    -------
    md_rawcode : mo.md
        Raw code markdown view.

    Examples
    --------
    >>> from rootlp import raw_code
    ...
    >>> raw_code(name, code_editor)
    '''
    
    # Title
    title = name[0].upper() + name[1:].replace('_', ' ')

    string = f"""
# **{title} raw code**

We define the raw code used to create logic behind {name}.

You can edit the code before launching in next tab for customization.

---

{code_editor}
"""
    return mo.md(string)



# %% Test function run
if __name__ == "__main__":
    from corelp import test
    test(__file__)