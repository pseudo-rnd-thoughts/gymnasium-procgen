import gymnasium as gym

from gymnasium_procgen import ProcgenEnv
from gymnasium_procgen.vector_env import ProcgenVectorEnv


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


for env_name in ENV_NAMES:
    gym.register(
        id=f"procgen/{env_name}-v1",
        entry_point="gymnasium_procgen.envs:ProcgenEnv",
        vector_entry_point="gymnasium_procgen.vector_env:ProcgenVectorEnv",
    )


# Convenience functions
def make_procgen_env(
    env_name: str,
    distribution_mode: str = "hard",
    start_level: int = 0,
    num_levels: int = 0,
    **kwargs,
) -> ProcgenEnv:
    """Create single Procgen environment

    Args:
        env_name: Name of the Procgen environment (e.g., 'coinrun', 'bigfish')
        distribution_mode: Difficulty mode ('easy', 'hard', 'extreme', 'memory', 'exploration')
        start_level: Starting level for training
        num_levels: Number of levels to use (0 = unlimited)
        **kwargs: Additional options (render_mode, visual settings, etc.)
    """
    return ProcgenEnv(
        env_name=env_name,
        distribution_mode=distribution_mode,
        start_level=start_level,
        num_levels=num_levels,
        **kwargs,
    )


def make_procgen_vector_env(
    env_name: str,
    num_envs: int,
    distribution_mode: str = "hard",
    start_level: int = 0,
    num_levels: int = 0,
    **kwargs,
) -> ProcgenVectorEnv:
    """Create vectorized Procgen environment

    Args:
        env_name: Name of the Procgen environment
        num_envs: Number of parallel environments
        distribution_mode: Difficulty mode ('easy', 'hard', 'extreme', 'memory', 'exploration')
        start_level: Starting level for training
        num_levels: Number of levels to use (0 = unlimited)
        **kwargs: Additional options
    """
    return ProcgenVectorEnv(
        env_name=env_name,
        num_envs=num_envs,
        distribution_mode=distribution_mode,
        start_level=start_level,
        num_levels=num_levels,
        **kwargs,
    )
