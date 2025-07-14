"""Procgen2 - Procedurally Generated Game-Like RL Environments."""

import importlib.metadata

import gymnasium as gym


# Procgen constants
ENV_NAMES = [
    "bigfish",
    "bossfight",
    "caveflyer",
    "chaser",
    "climber",
    "coinrun",
    "dodgeball",
    "fruitbot",
    "heist",
    "jumper",
    "leaper",
    "maze",
    "miner",
    "ninja",
    "plunder",
    "starpilot",
]

EXPLORATION_LEVEL_SEEDS = {
    "coinrun": 1949448038,
    "caveflyer": 1259048185,
    "leaper": 1318677581,
    "jumper": 1434825276,
    "maze": 158988835,
    "heist": 876640971,
    "climber": 1561126160,
    "ninja": 1123500215,
}

# Maps string distribution modes to C library integer constants
DISTRIBUTION_MODE_DICT = {
    "easy": 0,
    "hard": 1,
    "extreme": 2,
    "memory": 10,
    "exploration": 20,  # Handled specially - converted to hard mode with specific seeds
}

__version__ = importlib.metadata.version("gymnasium_procgen")
__all__ = ["__version__", "ENV_NAMES", "EXPLORATION_LEVEL_SEEDS", "DISTRIBUTION_MODE_DICT"]


for env_name in ENV_NAMES:
    gym.register(
        id=f"procgen/{env_name}-v1",
        # entry_point="gymnasium_procgen.envs:ProcgenEnv",
        vector_entry_point="gymnasium_procgen.vector_env:ProcgenVectorEnv",
    )
