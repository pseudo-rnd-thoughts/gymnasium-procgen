"""Procgen2 - Procedurally Generated Game-Like RL Environments."""

__version__ = "1.0.0"

from env import ProcgenEnv, ProcgenGym3Env
from registration import register_environments

register_environments()

__all__ = ["ProcgenEnv", "ProcgenGym3Env", "__version__"]
