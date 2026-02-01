# __init__.py

"""
Init file for package structure.
Get the version from pyproject.toml version tag
"""

from importlib.metadata import version

__version__ = version("rcdl")
