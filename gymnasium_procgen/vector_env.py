import os
import platform
from typing import Any

import numpy as np
from cffi import FFI
from gymnasium import spaces
from gymnasium.vector import VectorEnv

from gymnasium_procgen import (
    DISTRIBUTION_MODE_DICT,
    ENV_NAMES,
    EXPLORATION_LEVEL_SEEDS,
)
from gymnasium_procgen.utils import Spec, create_random_seed


__all__ = ["ProcgenVectorEnv"]


class ProcgenVectorEnv(VectorEnv):
    """Vectorized Procgen environment for Gymnasium"""

    def __init__(
        self,
        env_name: str,
        num_envs: int,
        start_level: int = 0,
        num_levels: int = 0,
        seed: int | None = None,
        distribution_mode: str = "hard",
        # Procgen-specific visual options
        center_agent: bool = True,
        use_backgrounds: bool = True,
        use_monochrome_assets: bool = False,
        restrict_themes: bool = False,
        use_generated_assets: bool = False,
        paint_vel_info: bool = False,
        **options,
    ):
        # Validate environment name
        assert (
            env_name in ENV_NAMES
        ), f"Unknown environment: {env_name}. Valid options: {ENV_NAMES}"

        # Validate and process distribution mode (same logic as single env)
        assert (
            distribution_mode in DISTRIBUTION_MODE_DICT
        ), f'"{distribution_mode}" is not a valid distribution mode. Valid options: {list(DISTRIBUTION_MODE_DICT.keys())}'

        if distribution_mode == "exploration":
            assert (
                env_name in EXPLORATION_LEVEL_SEEDS
            ), f"{env_name} does not support exploration mode"
            distribution_mode_int = DISTRIBUTION_MODE_DICT["hard"]
            assert "num_levels" not in options, "exploration mode overrides num_levels"
            num_levels = 1
            assert (
                "start_level" not in options
            ), "exploration mode overrides start_level"
            start_level = EXPLORATION_LEVEL_SEEDS[env_name]
        else:
            distribution_mode_int = DISTRIBUTION_MODE_DICT[distribution_mode]

        self.env_name = env_name
        self.num_envs = num_envs
        self.lib_dir = "src"

        # Initialize C interface for vectorized environments
        self._ffi = FFI()
        with open(os.path.join(os.path.dirname(__file__), "src", "libenv.h")) as f:
            self._ffi.cdef(f.read())

        # Load shared library
        self._c_lib = self._ffi.dlopen(os.path.join(self.lib_dir, self._get_lib_name()))

        # Configure options
        self._configure_options(
            start_level=start_level,
            num_levels=num_levels,
            seed=seed or create_random_seed(),
            distribution_mode=distribution_mode_int,
            center_agent=center_agent,
            use_backgrounds=use_backgrounds,
            use_monochrome_assets=use_monochrome_assets,
            restrict_themes=restrict_themes,
            use_generated_assets=use_generated_assets,
            paint_vel_info=paint_vel_info,
            **options,
        )

        # Create vectorized environment
        self._create_vector_environment()

        # Setup spaces
        single_observation_space = spaces.Box(
            low=0, high=255, shape=(64, 64, 3), dtype=np.uint8
        )
        single_action_space = spaces.Discrete(15)

        super().__init__(
            num_envs=num_envs,
            observation_space=spaces.Box(
                low=0, high=255, shape=(num_envs, 64, 64, 3), dtype=np.uint8
            ),
            action_space=spaces.MultiDiscrete([15] * num_envs),
            single_observation_space=single_observation_space,
            single_action_space=single_action_space,
        )

        # Initialize buffers
        self._initialize_vector_buffers()

    def _get_lib_name(self) -> str:
        """Get platform-specific library name"""
        system = platform.system()
        if system == "Linux":
            return "libenv.so"
        elif system == "Darwin":
            return "libenv.dylib"
        elif system == "Windows":
            return "env.dll"
        else:
            raise RuntimeError(f"Unsupported platform: {system}")

    def _get_space(self, space_type: int) -> tuple[spaces.Space, list[Spec]]:
        """Query C environment for space specification (same as single env)"""
        count = self._c_lib.libenv_get_tensortypes(
            self._c_env, space_type, self._ffi.NULL
        )
        if count == 0:
            return spaces.Dict({}), []

        c_tensortypes = self._ffi.new(f"struct libenv_tensortype[{count:d}]")
        self._c_lib.libenv_get_tensortypes(self._c_env, space_type, c_tensortypes)

        space_dict = {}
        specs = []

        for i in range(count):
            c_tt = c_tensortypes[i]
            name = self._ffi.string(c_tt.name).decode("utf8")
            shape = tuple(c_tt.shape[j] for j in range(c_tt.ndim))

            if c_tt.scalar_type == self._c_lib.LIBENV_SCALAR_TYPE_REAL:
                if c_tt.dtype == self._c_lib.LIBENV_DTYPE_FLOAT32:
                    dtype = np.dtype("float32")
                    low = c_tt.low.float32
                    high = c_tt.high.float32
                    gym_space = spaces.Box(low=low, high=high, shape=shape, dtype=dtype)
                else:
                    raise ValueError("Unrecognized dtype for real scalar type")
            elif c_tt.scalar_type == self._c_lib.LIBENV_SCALAR_TYPE_DISCRETE:
                if c_tt.dtype == self._c_lib.LIBENV_DTYPE_UINT8:
                    dtype = np.dtype("uint8")
                    low = c_tt.low.uint8
                    high = c_tt.high.uint8
                elif c_tt.dtype == self._c_lib.LIBENV_DTYPE_INT32:
                    dtype = np.dtype("int32")
                    low = c_tt.low.int32
                    high = c_tt.high.int32
                else:
                    raise ValueError("Unrecognized dtype for discrete scalar type")

                if shape == ():
                    gym_space = spaces.Discrete(high + 1)
                else:
                    gym_space = spaces.Box(low=low, high=high, shape=shape, dtype=dtype)
            else:
                raise ValueError("Unknown scalar type")

            space_dict[name] = gym_space
            specs.append(Spec(name=name, shape=shape, dtype=dtype))

        if len(space_dict) == 1:
            return list(space_dict.values())[0], specs
        else:
            return spaces.Dict(space_dict), specs

    def _dict_to_c_options(self, options: dict) -> tuple[Any, list[Any]]:
        """Convert Python dict to C options (same as single env)"""
        if not options:
            c_options = self._ffi.new("struct libenv_options *")
            c_options.items = self._ffi.NULL
            c_options.count = 0
            return c_options, []

        keepalives = []
        c_options = self._ffi.new("struct libenv_options *")
        c_option_array = self._ffi.new("struct libenv_option[%d]" % len(options))

        for i, (key, value) in enumerate(options.items()):
            name = str(key).encode("utf8")
            assert len(name) < 128 - 1, f"Option key too long: {key}"

            if isinstance(value, str):
                value_bytes = value.encode("utf8")
                c_data = self._ffi.new("char[]", value_bytes)
                dtype = self._c_lib.LIBENV_DTYPE_UINT8
                count = len(value_bytes)
            elif isinstance(value, bool):
                c_data = self._ffi.new("uint8_t*", int(value))
                dtype = self._c_lib.LIBENV_DTYPE_UINT8
                count = 1
            elif isinstance(value, int):
                assert -(2**31) <= value < 2**31, f"Integer out of range: {value}"
                c_data = self._ffi.new("int32_t*", value)
                dtype = self._c_lib.LIBENV_DTYPE_INT32
                count = 1
            elif isinstance(value, float):
                c_data = self._ffi.new("float*", value)
                dtype = self._c_lib.LIBENV_DTYPE_FLOAT32
                count = 1
            else:
                raise ValueError(
                    f"Unsupported option type: {type(value)} for key {key}"
                )

            c_option_array[i].name = name
            c_option_array[i].dtype = dtype
            c_option_array[i].count = count
            c_option_array[i].data = c_data
            keepalives.append(c_data)

        keepalives.append(c_option_array)
        c_options.items = c_option_array
        c_options.count = len(options)

        return c_options, keepalives

    def _create_vector_environment(self):
        """Create vectorized C environment"""
        self._c_options, self._options_keepalives = self._dict_to_c_options(
            self.options
        )
        self._c_env = self._c_lib.libenv_make(self.num_envs, self._c_options)
        if self._c_env == self._ffi.NULL:
            raise RuntimeError("Failed to create vectorized environment")

        version = self._c_lib.libenv_version()
        assert version == 1, f"libenv version mismatch, got {version} but expected 1"

    def _create_aligned_array(
        self, shape: tuple[int, ...], dtype: np.dtype, align: int = 64
    ) -> np.ndarray:
        """Create memory-aligned numpy array (same as single env)"""
        n_bytes = np.prod(shape) * dtype.itemsize if shape else dtype.itemsize
        arr = np.zeros(n_bytes + (align - 1), dtype=np.uint8)
        data_align = arr.ctypes.data % align
        offset = 0 if data_align == 0 else (align - data_align)
        view = arr[offset : offset + n_bytes].view(dtype)
        return view.reshape(shape) if shape else view.reshape(())

    def _configure_options(self, **kwargs):
        """Configure vectorized environment options"""
        # Resource root for assets
        resource_root = kwargs.pop("resource_root", None)
        if resource_root is None:
            resource_root = os.path.join(self.lib_dir, "data", "assets") + os.sep
            assert os.path.exists(
                resource_root
            ), f"Asset directory not found: {resource_root}"

        self.options = {
            # Core environment settings
            "env_name": self.env_name,
            "num_actions": 15,
            "render_human": False,  # Vector envs typically don't render
            "resource_root": resource_root,
            # Procgen-specific options
            "start_level": kwargs.get("start_level", 0),
            "num_levels": kwargs.get("num_levels", 0),
            "distribution_mode": kwargs.get("distribution_mode", 1),
            "use_sequential_levels": bool(kwargs.get("use_sequential_levels", False)),
            "debug_mode": kwargs.get("debug_mode", 0),
            "rand_seed": kwargs.get("seed", create_random_seed()),
            "num_threads": kwargs.get("num_threads", 4),
            # Visual options
            "center_agent": bool(kwargs.get("center_agent", True)),
            "use_generated_assets": bool(kwargs.get("use_generated_assets", False)),
            "use_monochrome_assets": bool(kwargs.get("use_monochrome_assets", False)),
            "restrict_themes": bool(kwargs.get("restrict_themes", False)),
            "use_backgrounds": bool(kwargs.get("use_backgrounds", True)),
            "paint_vel_info": bool(kwargs.get("paint_vel_info", False)),
        }

        # Add any additional options
        for key, value in kwargs.items():
            if key not in self.options:
                self.options[key] = value

        self._c_options = self._dict_to_c_options(self.options)

    def _initialize_vector_buffers(self):
        """Initialize vectorized buffers using structure-of-arrays format"""
        # Get space specifications
        _, ob_specs = self._get_space(self._c_lib.LIBENV_SPACE_OBSERVATION)
        _, ac_specs = self._get_space(self._c_lib.LIBENV_SPACE_ACTION)
        _, info_specs = self._get_space(self._c_lib.LIBENV_SPACE_INFO)

        # Allocate vectorized buffers
        self._ob_dict, self._c_ob_buffers = self._allocate_vector_space_buffers(
            ob_specs
        )
        self._ac_dict, self._c_ac_buffers = self._allocate_vector_space_buffers(
            ac_specs
        )
        self._info_dict, self._c_info_buffers = self._allocate_vector_space_buffers(
            info_specs
        )

        # Allocate reward and done buffers for all environments
        self._rewards, self._c_rew_buffer = self._allocate_vector_single_buffer(
            np.dtype("float32")
        )
        self._dones, self._c_done_buffer = self._allocate_vector_single_buffer(
            np.dtype("bool")
        )

        # Create C buffers struct
        self._c_buffers = self._ffi.new("struct libenv_buffers *")
        self._c_buffers.ob = self._c_ob_buffers
        self._c_buffers.ac = self._c_ac_buffers
        self._c_buffers.info = self._c_info_buffers
        self._c_buffers.rew = self._ffi.cast("float *", self._c_rew_buffer)
        self._c_buffers.first = self._ffi.cast("uint8_t *", self._c_done_buffer)

        # Set buffers in C environment
        self._c_lib.libenv_set_buffers(self._c_env, self._c_buffers)

    def _allocate_vector_space_buffers(
        self, specs: list[Spec]
    ) -> tuple[dict[str, np.ndarray], Any]:
        """Allocate vectorized buffers for a space using structure-of-arrays format"""
        result = {}
        if not specs:
            return result, self._ffi.NULL

        # Total number of buffer pointers = len(specs) * num_envs
        length = len(specs) * self.num_envs
        buffers = self._ffi.new(f"void *[{length}]")

        for space_idx, spec in enumerate(specs):
            # Shape for vectorized environment: (num_envs, *original_shape)
            vector_shape = (self.num_envs,) + spec.shape
            arr = self._create_aligned_array(vector_shape, spec.dtype)
            result[spec.name] = arr

            # Set buffer pointers for each environment
            # Layout: space0_env0, space0_env1, ..., space0_envN, space1_env0, ...
            for env_idx in range(self.num_envs):
                buffer_idx = space_idx * self.num_envs + env_idx
                # Point to the specific environment's slice of the array
                buffers[buffer_idx] = self._ffi.from_buffer(
                    arr.data[env_idx : env_idx + 1]
                )

        return result, buffers

    def _allocate_vector_single_buffer(self, dtype: np.dtype) -> tuple[np.ndarray, Any]:
        """Allocate buffer for single array type across all environments"""
        arr = self._create_aligned_array((self.num_envs,), dtype)
        return arr, self._ffi.from_buffer(arr.data)

    def reset(self, *, seed=None, options=None):
        """Reset all environments"""
        if seed is not None:
            # For vectorized environments, seeding is handled at creation time
            pass

        # Get initial observations for all environments
        self._c_lib.libenv_observe(self._c_env)

        # Extract observations - return vectorized format
        if "rgb" in self._ob_dict:
            observations = self._ob_dict["rgb"].copy()
        else:
            observations = {key: arr.copy() for key, arr in self._ob_dict.items()}

        # Extract info for all environments
        infos = {}
        for key, arr in self._info_dict.items():
            infos[key] = arr.copy()

        return observations, infos

    def step(self, actions):
        """Step all environments"""
        # Validate action shape
        if len(actions) != self.num_envs:
            raise ValueError(f"Expected {self.num_envs} actions, got {len(actions)}")

        # Set actions in buffer
        if "action" in self._ac_dict:
            action_array = np.array(actions, dtype=np.int32)
            self._ac_dict["action"][:] = action_array
        else:
            raise ValueError("Action space does not contain 'action' key")

        # Execute actions and get new observations
        self._c_lib.libenv_act(self._c_env)
        self._c_lib.libenv_observe(self._c_env)

        # Extract results
        if "rgb" in self._ob_dict:
            observations = self._ob_dict["rgb"].copy()
        else:
            observations = {key: arr.copy() for key, arr in self._ob_dict.items()}

        rewards = self._rewards.copy()
        terminated = self._dones.copy().astype(bool)
        truncated = np.zeros_like(terminated)  # Procgen doesn't use truncation

        # Extract info
        infos = {}
        for key, arr in self._info_dict.items():
            infos[key] = arr.copy()

        return observations, rewards, terminated, truncated, infos

    def get_state(self, env_idx: int = None):
        """Get serialized state for specific environment or all environments"""
        MAX_STATE_SIZE = 2**20

        if env_idx is not None:
            # Get state for specific environment
            buf = self._ffi.new(f"char[{MAX_STATE_SIZE}]")
            state_size = self._c_lib.get_state(
                self._c_env, env_idx, buf, MAX_STATE_SIZE
            )
            return bytes(self._ffi.buffer(buf, state_size))
        else:
            # Get states for all environments
            states = []
            for i in range(self.num_envs):
                buf = self._ffi.new(f"char[{MAX_STATE_SIZE}]")
                state_size = self._c_lib.get_state(self._c_env, i, buf, MAX_STATE_SIZE)
                states.append(bytes(self._ffi.buffer(buf, state_size)))
            return states

    def set_state(self, states):
        """Set environment states from serialized bytes"""
        if isinstance(states, bytes):
            # Single state for environment 0
            self._c_lib.set_state(self._c_env, 0, states, len(states))
        else:
            # Multiple states
            assert (
                len(states) == self.num_envs
            ), f"Expected {self.num_envs} states, got {len(states)}"
            for i, state in enumerate(states):
                self._c_lib.set_state(self._c_env, i, state, len(state))

        # Update observation buffers
        self._c_lib.libenv_observe(self._c_env)

    def close(self):
        """Close all environments"""
        if hasattr(self, "_c_env") and self._c_env != self._ffi.NULL:
            self._c_lib.libenv_close(self._c_env)
            self._c_env = self._ffi.NULL

        if hasattr(self, "_options_keepalives"):
            self._options_keepalives = None
