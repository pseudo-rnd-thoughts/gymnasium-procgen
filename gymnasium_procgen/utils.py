"""
Helper classes for managing C interface and buffer allocation
This shows the detailed implementation of the buffer management from the original CEnv
"""

from __future__ import annotations

import random
from typing import NamedTuple

import numpy as np


__all__ = ["Spec", "create_random_seed"]


class Spec(NamedTuple):
    """Specification for a tensor/buffer"""

    name: str
    shape: tuple[int, ...]
    dtype: np.dtype


def create_random_seed():
    """Create a random seed, accounting for MPI if available"""
    rand_seed = random.SystemRandom().randint(0, 2**31 - 1)
    try:
        # Force MPI processes to choose different random seeds
        from mpi4py import MPI

        rand_seed = rand_seed - (rand_seed % MPI.COMM_WORLD.size) + MPI.COMM_WORLD.rank
    except ModuleNotFoundError:
        pass
    return rand_seed
