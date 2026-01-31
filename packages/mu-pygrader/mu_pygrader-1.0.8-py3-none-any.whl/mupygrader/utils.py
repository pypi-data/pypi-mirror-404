"""
utils.py
weavebj1 - 2025

Basic repository needs

Part of python-grader library
"""

import os
import sys

def repo_path():
    """
    Gets the path of the repository (breaks if this file moves)
    """
    return os.path.dirname(__file__)


def in_repo(search_file):
    """
    Returns the path of a file if it exists
    """
    search_dir = repo_path()
    for root, _, files in os.walk(search_dir):
        for file in files:
            if search_file == file:
                return os.path.join(root, file)
    return None


def running_in_exe():
    """
    Returns true if the code is running in an exe file
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def exe_resource_path():
    """
    Retrieves the path for files in the exe that are placed into a temp directory
    """
    return getattr(sys, '_MEIPASS')


def guarantee_path(path):
    """
    Makes sure that the file is on the system path
    """
    sys.path.append(os.path.dirname(os.path.abspath(path)))



def file_strip(path):
    """
    Removes all except for the base name (including a ./ at the start)
    """
    filename = os.path.basename(path)
    return os.path.splitext(filename)[0].replace('.','')


def nothing_function():
    """
    Does nothing. Used to replace breakpoint
    """
    return