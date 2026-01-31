#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2026-01-25
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : rootLP
# Module        : overview

"""
This module returns a markdown with the overview of a main script.
"""



# %% Libraries
import marimo as mo



# %% Function
def overview(name) :
    '''
    This module returns a markdown with the overview of a main script.
    
    Parameters
    ----------
    name : str
        Name of script.

    Returns
    -------
    md_overview : mo.md
        Overview markdown.

    Examples
    --------
    >>> from rootlp import overview
    ...
    >>> overview(name)
    '''

    # Title
    title = name[0].upper() + name[1:].replace('_', ' ')

    string = f"""
# **{title} code overview**

In the next tab is defined the raw code for {name}, using functions from the custom package. You can use this notebook as a template to learn how to use these functions. For any help, please contact authors.

Below is the definition of this script main function (`{name}`), which can be identified by the `@main` decorator. All the logic of the script is orchestrated from this function.

A *main script function* generally aims to transform data stored on disk into processed data that is also saved back to disk. As such, it usually defines:
- a path **from which to import** the input data
- a path **where to save** the processed data

---

## **Sections and Checkpoints**

The processing logic is divided into **sections**, which are identified by the `@{name}.section` decorator.

Each section can be seen as a *checkpoint* in the pipeline:
- It computes intermediate data of interest
- These computations may be heavy or time-consuming
- Results are cached into a **dedicated folder**

Thanks to this mechanism, re-running the script on the same data allows previously computed results to be automatically loaded from disk, avoiding unnecessary recomputation.

The `section` decorator attaches a new attribute named `path` (of type `pathlib.Path`) to the decorated function. This attribute points to the directory associated with the section, where cached data and intermediate outputs are stored.

---

## **Bulk Processing and Batches**

Another feature of the `@main` decorator is support for **bulk processing**.

The basic use case is to define a single import directory that contains one batch of data to process. However, it is also possible to define a function that:
- selects subfolders based on specific criteria
- returns a list of independent import subfolders
This function is stored as `{name}.bulk`.

Each of these subfolders is treated as a separate **batch** and can be processed in a single run.

A typical use case is to launch a large processing job overnight after collecting sufficient data during the day. In this scenario, faulty batches can be skipped to avoid interrupting the processing of the remaining batches.

---

## **Export Directory Structure**

In the export directory, a dedicated **processing folder** is created for each run.
This folder is named using the launch timestamp (e.g. hour and date) to clearly distinguish multiple runs.

Inside this processing folder, three subfolders are created:

- **import_folder**
  A symbolic link to the `import_path`, allowing easy identification of the input data used.

- **export_folder**
  Contains all processed data, organized by batch and by section.

- **_outputs**
  Contains symbolic links to selected output files of interest, grouped by file type and batch.

---

## **Export Folder Layout**

Inside the `export_folder`:
- One folder is created per **batch**
- Inside each batch folder, one folder is created per **section**
- These section folders store cached data, intermediate results, and section-specific outputs

The overall structure of the `export_path` directory is as follows:

```text
export_path/
├── import_path/ (by default export_path is the parent of import_path)
│   ├── import_data.xx
│   └── ...
└── extract_signals_YYYY-MM-DD-HHhMMminSSs/
    ├── import_folder -> /path/to/import_path (symlink)
    ├── export_folder/
    │   ├── batch_00/
    │   │   ├── 000_section/
    │   │   │   ├── cache_hash.pkl/
    │   │   │   ├── output_00.xx/
    │   │   │   └── ...
    │   │   ├── 001_section/
    │   │   │   ├── cache_hash.pkl/
    │   │   │   ├── output_00.xx/
    │   │   │   └── ...
    │   │   └── ...
    │   ├── batch_01/
    │   │   ├── 000_section/
    │   │   └── ...
    │   └── ...
    └── _outputs/
        ├── output_file_00/
        │   ├── batch_00.xx (symlink)
        │   ├── batch_01.xx (symlink)
        │   └── ...
        ├── output_file_01/
        │   ├── batch_00.xx (symlink)
        │   ├── batch_01.xx (symlink)
        │   └── ...
        └── ...
```

---

## **Execution Parameters**

The `@main` decorator adds several execution parameters to the function call:

1. **`import_path`** and **`export_path`**
   - If set to `None`, a file dialog prompts the user to select an import directory
   - The export path is then automatically defined as the **parent directory** of the import path
   - Paths are passed to the function as `pathlib.Path` objects for improved usability

2. **`new`** (`bool`)
   - If `True`, a new processing folder is created using the current launch timestamp
   - If `False`, the most recent processing folder is reused

3. **`overnight`** (`bool`)
   - If `True`, errors in individual batches are skipped
   - This allows long-running bulk processing jobs to continue without interruption
"""
    return mo.md(string)



# %% Test function run
if __name__ == "__main__":
    from corelp import test
    test(__file__)