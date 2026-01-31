#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2026-01-25
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : rootLP
# Module        : execution_panel

"""
This module creates the executio panel of a main script.
"""



# %% Libraries
import marimo as mo
from rootlp import user_inputs



# %% Function
def execution_panel(name) :
    '''
    This module creates the executio panel of a main script.
    
    Parameters
    ----------
    name : str
        Name of script.

    Returns
    -------
    launch : mo.ui.button
        Launch button.
    parameters : dict
        Dictionnary with execution parameters.
    md_execution : mo.md
        Execution panel markdown.

    Examples
    --------
    >>> from rootlp import execution_panel
    ...
    >>> execution_panel(name)
    '''

    # Title
    title = name[0].upper() + name[1:].replace('_', ' ')

    launch = mo.ui.run_button(label=f"**--->>> {name} <<<---**")
    launch.center()

    user_inputs(True)
    import_path = mo.ui.text(placeholder="copy-paste import path", full_width=True)
    export_path = mo.ui.text(placeholder="copy-paste export path", full_width=True)
    new = mo.ui.switch(value=True, label="**New**: check to create new processing folder each time [default: True]")
    overnight = mo.ui.switch(value=False, label="**Overnight**: check to ignore bulk processing errors [default: False]")
    parameters_execution = user_inputs()

    # Markdown output
    md_execution = f"""
# **{title} launch script**

---

## **Script execution inputs**

### Launch script button

{launch}

Execution logs will appear on the right panel -->

(Check user inputs parameters before launching)

### Execution parameters

**Import path** : Folder with data to process [default: will open a browse window]
{import_path}

**Export path** : Folder where to save [default: import path **parent**]
{export_path}

{mo.hstack([new, overnight])}
"""

    return launch, parameters_execution, mo.md(md_execution)



# %% Test function run
if __name__ == "__main__":
    from corelp import test
    test(__file__)