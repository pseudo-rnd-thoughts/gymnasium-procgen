import numpy as np
import pytest

from gymnasium_procgen import ProcgenGym3Env
from gymnasium_procgen.env import ENV_NAMES


@pytest.mark.parametrize("env_name", ENV_NAMES)
def test_seeding(env_name):
    num_envs = 1

    def make_env(level_num):
        venv = ProcgenGym3Env(
            num_envs=num_envs, env_name=env_name, num_levels=1, start_level=level_num
        )
        return venv

    env1 = make_env(0)
    env2 = make_env(0)
    env3 = make_env(1)

    env1.act(np.zeros(num_envs))
    env2.act(np.zeros(num_envs))
    env3.act(np.zeros(num_envs))

    _, obs1, _ = env1.observe()
    _, obs2, _ = env2.observe()
    _, obs3, _ = env3.observe()

    assert np.array_equal(obs1["rgb"], obs2["rgb"])
    assert not np.array_equal(obs1["rgb"], obs3["rgb"])


@pytest.mark.parametrize("env_name", ENV_NAMES)
def test_determinism(env_name):
    def collect_observations():
        rng = np.random.RandomState(0)
        env = ProcgenGym3Env(num_envs=2, env_name=env_name, rand_seed=23)
        _, obs, _ = env.observe()
        obses = [obs["rgb"]]
        for _ in range(128):
            env.act(
                rng.randint(
                    low=0, high=env.ac_space.eltype.n, size=(env.num,), dtype=np.int32
                )
            )
            _, obs, _ = env.observe()
            obses.append(obs["rgb"])
        return np.array(obses)

    obs1 = collect_observations()
    obs2 = collect_observations()
    assert np.array_equal(obs1, obs2)
