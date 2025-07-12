"""Procgen2 - Procedurally Generated Game-Like RL Environments."""

import importlib.metadata

from gymnasium_procgen.env import ProcgenEnv, ProcgenGym3Env
from gymnasium_procgen.registration import register_environments

__version__ = importlib.metadata.version("mypackage")
__all__ = ["ProcgenEnv", "ProcgenGym3Env", "__version__"]

register_environments()
