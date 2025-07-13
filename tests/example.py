from gymnasium_procgen.registration import (
    EXPLORATION_LEVEL_SEEDS,
    make_procgen_env,
    make_procgen_vector_env,
)


if __name__ == "__main__":
    # Single environment with different distribution modes
    print("Creating environments with different distribution modes...")

    # Easy mode - good for initial learning
    env_easy = make_procgen_env(
        "coinrun", distribution_mode="easy", lib_dir="./procgen_libs"
    )

    # Hard mode - standard training mode
    env_hard = make_procgen_env(
        "coinrun", distribution_mode="hard", num_levels=100, lib_dir="./procgen_libs"
    )

    # Exploration mode - uses specific seed for reproducible exploration
    env_explore = make_procgen_env(
        "coinrun", distribution_mode="exploration", lib_dir="./procgen_libs"
    )
    # Note: exploration mode automatically sets num_levels=1 and
    # start_level=EXPLORATION_LEVEL_SEEDS["coinrun"]

    # Test single environment
    obs, info = env_hard.reset()
    print(f"Observation shape: {obs.shape}")
    print(f"Action space: {env_hard.action_space}")
    print(f"Action combinations: {env_hard.get_combos()[:5]}...")  # Show first 5

    for _ in range(10):
        action = env_hard.action_space.sample()
        obs, reward, terminated, truncated, info = env_hard.step(action)
        if terminated or truncated:
            obs, info = env_hard.reset()

    env_easy.close()
    env_hard.close()
    env_explore.close()

    # Vector environment
    print("\nCreating vectorized environment...")
    vec_env = make_procgen_vector_env(
        "coinrun",
        num_envs=4,
        distribution_mode="hard",
        num_levels=50,
        start_level=0,
        lib_dir="./procgen_libs",
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
