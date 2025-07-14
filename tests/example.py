from gymnasium_procgen import (
    EXPLORATION_LEVEL_SEEDS
)
from gymnasium_procgen.vector_env import ProcgenVectorEnv


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


if __name__ == "__main__":
    # Single environment with different distribution modes
    print("Creating environments with different distribution modes...")

    # Vector environment
    print("Creating vectorized environment...")
    vec_env = make_procgen_vector_env(
        "coinrun",
        num_envs=4,
        distribution_mode="hard",
        num_levels=50,
        start_level=0,
    )

    obs, infos = vec_env.reset()
    print(f"Vector obs shape: {obs.shape}")
    print(f"Vector action space: {vec_env.action_space}")

    for _ in range(10):
        actions = [vec_env.single_action_space.sample() for _ in range(4)]
        obs, rewards, terminated, truncated, infos = vec_env.step(actions)
        print(f"Rewards: {rewards}")
        # Vectorized environments auto-reset terminated episodes

    vec_env.close()

    # Demonstrate exploration mode for different environments
    print("\nTesting exploration mode...")
    for env_name in ["coinrun", "maze", "heist"]:
        if env_name in EXPLORATION_LEVEL_SEEDS:
            print(f"{env_name} exploration seed: {EXPLORATION_LEVEL_SEEDS[env_name]}")
        else:
            print(f"{env_name} does not support exploration mode")
