"""Procgen2 - Procedurally Generated Game-Like RL Environments."""

import importlib.metadata
import os
import sys

# Configure Qt6 for headless rendering
# This must be set before any Qt libraries are loaded
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Set Qt plugin path if bundled plugins exist
_package_dir = os.path.dirname(os.path.abspath(__file__))
_qt_plugins_dir = os.path.join(_package_dir, "qt6_plugins")
if os.path.exists(_qt_plugins_dir):
    os.environ["QT_PLUGIN_PATH"] = _qt_plugins_dir

from gymnasium_procgen.env import ProcgenEnv, ProcgenGym3Env
from gymnasium_procgen.registration import register_environments

__version__ = importlib.metadata.version("gymnasium_procgen")
__all__ = ["ProcgenEnv", "ProcgenGym3Env", "__version__"]

register_environments()
