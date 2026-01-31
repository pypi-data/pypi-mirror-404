#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2025-11-30
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : rootLP
# Module        : user_inputs

"""
Gets last user inputs dictionnary from global variables.
"""



# %% Libraries
import inspect
import marimo as mo



# %% Function

def user_inputs(reset=False) :
    r"""
    Return a dictionary of variables defined by the user in the interactive environment.

    Parameters
    ----------
    reset : bool or str
        True to set as first call, String value to define a group of parameters

    Returns
    -------
    dict
        A dictionary containing the user's currently defined variables.

    Examples
    --------
    >>> from corelp import user_inputs
    >>> user_inputs(True)       # First call (initializes and clears import-related variables)
    None
    >>> a = 1               # User defines a variable
    >>> user_inputs()       # Now returns: {'a': 1}
    {'a': 1}
    """
    frame = inspect.currentframe().f_back
    ns = {**frame.f_globals, **frame.f_locals}

    # ---- Filter user variables (ignore internals starting with "_") ----
    ns = {key: value for key, value in ns.items() if not key.startswith("_")}

    # Validate status
    if reset :
        user_inputs.cache = None
        if isinstance(reset, str) : # Group reset
            user_inputs.current_group = reset
        else :
            user_inputs.current_group = None
            user_inputs.groups_values = {}
            user_inputs.groups_comments = {}


    # Case when user_inputs is on top : cache = None
    if user_inputs.cache is None :
        user_inputs.cache = ns
        return

    # Case when user_inputs is at bottom : cache = dict
    else :
        updated = { key: value for key, value in ns.items() if key not in user_inputs.cache or user_inputs.cache[key] is not value}
        values = {key: value for key, value in updated.items() if not key.endswith('_')}
        comments = {key: value for key, value in updated.items() if key.endswith('_')}
        
        # Group values
        if user_inputs.current_group is not None :
            user_inputs.groups_values[user_inputs.current_group] = values
            user_inputs.groups_comments[user_inputs.current_group] = comments

        # End
        user_inputs.current_group = None
        user_inputs.cache = None
        return values

user_inputs.cache = None
user_inputs.current_group = None
user_inputs.groups_values = {}
user_inputs.groups_comments = {}
user_inputs.export = lambda: (
    {key: value
     for group in user_inputs.groups_values.values()
     for key, value in group.items()},
    mo.md("---\n\n## **Script user inputs**\n\n" + "".join(
        f"### {group_name}\n\n"
        + "".join(f"{ui}\n\n" for ui in group.values())
        for group_name, group in user_inputs.groups_values.items()
    ))
)


# %% Test function run
if __name__ == "__main__":
    from corelp import test
    test(__file__)