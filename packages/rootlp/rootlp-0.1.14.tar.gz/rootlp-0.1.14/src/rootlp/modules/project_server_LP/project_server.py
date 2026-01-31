#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2026-01-18
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : rootLP
# Module        : project_server

"""
This module creates and run a custom marimo server for the project.
"""



# %% Libraries
from pathlib import Path
import marimo as mo
from fastapi import FastAPI
import uvicorn
import webbrowser
import threading
import psutil
import socket
import sys



# %% Function
def project_server(project) :
    '''
    This module creates and run a custom marimo server for the project.
    
    Parameters
    ----------
    project : module
        project to module on which we want to do the server.

    Examples
    --------
    >>> from rootlp import project_server
    >>> import myproject
    ...
    >>> project_server(myproject)
    '''

    # Source folder
    folder = Path(project.__file__).parent # project / __init__.py
    name = folder.name

    # Initialize marimo asgi app
    server = mo.create_asgi_app()
    server = server.with_app(path=f"/", root=folder/"pages/home_LP/home.py")

    # Analyse sources
    notebooks = ['pages', 'process', 'analyse']
    for source in project.sources.values() :
        split = source.split(".") # project.folder.module_LP.module
        if split[0] != name : raise SyntaxError('Project name is not consistent in sources')
        if len(split) != 4 or split[1] not in notebooks : continue
        server = server.with_app(path=f"/{split[3]}", root=folder / f"{split[1]}/{split[2]}/{split[3]}.py")

    # Create and configure FastAPI
    app = FastAPI()
    app.mount(f"/{name}", server.build())

    # Prints
    url = f'http://localhost:9797/{name}/'
    print("\n" + "*" * (len(name) + 4))
    print(f"| {name.upper()} |")
    print("*" * (len(name) + 4) + "\n")

    # Port
    if is_port_in_use(9797) :
        ask_free = input("Port 9797 is already in use, do you want to kill the corresponding process? [y]/n >>> ")
        if str(ask_free).lower() in ["y", "yes", "true", "1", ""] :
            killed = free_port(9797)
        else :
            killed = False
        if not killed :
            print('Terminate server launch.')
            return

    # Run the server
    print(f"Ctrl+Click in terminal or copy-paste the following URL in browser:\n")
    print(f"   ➜  {url} \n")
    print(f"📌 Do not close this terminal window until you finished with {name}!")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host="localhost", port=9797, log_level="critical")



def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("", port))  # empty host = all interfaces
            return False
        except OSError:
            return True

def free_port(port):
    killed = False

    for conn in psutil.net_connections(kind='inet'):
        if conn.laddr and conn.laddr.port == port:
            try:
                proc = psutil.Process(conn.pid)
                print(f"Killing process {proc.pid} ({proc.name()}) using port {port}.")
                proc.kill()
                killed = True
                print("Process killed successfully.")
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"Could not kill process on port {port}: {e}.")

    if not killed:
        print(f"No process found using port {port}")
    return killed



# %% Test function run
if __name__ == "__main__":
    from corelp import test
    test(__file__)