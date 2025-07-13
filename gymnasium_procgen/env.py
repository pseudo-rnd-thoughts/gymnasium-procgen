from __future__ import annotations

import os
import platform
from typing import Any

import gymnasium as gym
import numpy as np
from cffi import FFI
from gymnasium import spaces

from gymnasium_procgen.registration import (
    DISTRIBUTION_MODE_DICT,
    ENV_NAMES,
    EXPLORATION_LEVEL_SEEDS,
)


__all__ = ["ProcgenEnv"]

from gymnasium_procgen.utils import Spec, create_random_seed


class ProcgenEnv(gym.Env):
    """Single Procgen environment for Gymnasium"""

    def __init__(
        self,
        env_name: str,
        lib_dir: str,
        start_level: int = 0,
        num_levels: int = 0,
        seed: int | None = None,
        distribution_mode: str = "hard",
        render_mode: str | None = None,
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

        # Validate and process distribution mode
        assert (
            distribution_mode in DISTRIBUTION_MODE_DICT
        ), f'"{distribution_mode}" is not a valid distribution mode. Valid options: {list(DISTRIBUTION_MODE_DICT.keys())}'

        self.env_name = env_name
        self.lib_dir = lib_dir
        self.render_mode = render_mode

        # Handle exploration mode specially
        if distribution_mode == "exploration":
            assert (
                env_name in EXPLORATION_LEVEL_SEEDS
            ), f"{env_name} does not support exploration mode"

            # Exploration mode is actually hard mode with specific level settings
            distribution_mode_int = DISTRIBUTION_MODE_DICT["hard"]
            assert "num_levels" not in options, "exploration mode overrides num_levels"
            num_levels = 1
            assert (
                "start_level" not in options
            ), "exploration mode overrides start_level"
            start_level = EXPLORATION_LEVEL_SEEDS[env_name]
        else:
            distribution_mode_int = DISTRIBUTION_MODE_DICT[distribution_mode]

        # Initialize C library interface
        self._init_c_interface()

        # Configure environment options with proper distribution mode
        self._configure_options(
            start_level=start_level,
            num_levels=num_levels,
            seed=seed or create_random_seed(),
            distribution_mode=distribution_mode_int,  # Pass integer to C library
            center_agent=center_agent,
            use_backgrounds=use_backgrounds,
            use_monochrome_assets=use_monochrome_assets,
            restrict_themes=restrict_themes,
            use_generated_assets=use_generated_assets,
            paint_vel_info=paint_vel_info,
            **options,
        )

        # Create single environment instance
        self._create_environment()

        # Set up spaces
        self._setup_spaces()

        # Initialize state
        self._initialize_buffers()

    def _init_c_interface(self):
        """Initialize CFFI interface to C library"""
        self._ffi = FFI()

        # Load C definitions (simplified)
        self._ffi.cdef(
            """
            typedef struct libenv_env libenv_env;
            typedef struct {
                char name[64];
                int dtype;
                int shape[8];
                int ndim;
                // ... other fields
            } libenv_tensortype;

            libenv_env* libenv_make(int num_envs, void* options);
            void libenv_close(libenv_env* env);
            void libenv_observe(libenv_env* env);
            void libenv_act(libenv_env* env);
            void libenv_set_buffers(libenv_env* env, void* buffers);
            int libenv_get_tensortypes(libenv_env* env, int space_type, void* types);
        """
        )

        # Load shared library
        lib_name = self._get_lib_name()
        lib_path = os.path.join(self.lib_dir, lib_name)
        self._c_lib = self._ffi.dlopen(lib_path)

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

    def _configure_options(self, **kwargs):
        """Configure environment options for the C library"""
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
            "num_actions": 15,  # Procgen always uses 15 actions
            "render_human": self.render_mode == "rgb_array",
            "resource_root": resource_root,
            # Procgen-specific options (all get passed to C library)
            "start_level": kwargs.get("start_level", 0),
            "num_levels": kwargs.get("num_levels", 0),
            "distribution_mode": kwargs.get(
                "distribution_mode", 1
            ),  # Should be integer
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

        # Add any additional options passed in
        for key, value in kwargs.items():
            if key not in self.options:
                self.options[key] = value

        # Convert to C options (simplified)
        self._c_options = self._dict_to_c_options(self.options)

    def _dict_to_c_options(self, options: dict) -> tuple[Any, list[Any]]:
        """Convert Python dict to C options struct - based on vecoptions.cpp logic"""
        if not options:
            c_options = self._ffi.new("struct libenv_options *")
            c_options.items = self._ffi.NULL
            c_options.count = 0
            return c_options, []

        # Keep objects alive after function returns
        keepalives = []

        # Allocate options array
        c_options = self._ffi.new("struct libenv_options *")
        c_option_array = self._ffi.new("struct libenv_option[%d]" % len(options))

        for i, (key, value) in enumerate(options.items()):
            name = str(key).encode("utf8")
            assert len(name) < 128 - 1, f"Option key too long: {key}"

            # Convert value based on type - following vecoptions.cpp logic
            if isinstance(value, str):
                # String values are stored as uint8 arrays
                value_bytes = value.encode("utf8")
                c_data = self._ffi.new("char[]", value_bytes)
                dtype = self._c_lib.LIBENV_DTYPE_UINT8
                count = len(value_bytes)
            elif isinstance(value, bytes):
                c_data = self._ffi.new("char[]", value)
                dtype = self._c_lib.LIBENV_DTYPE_UINT8
                count = len(value)
            elif isinstance(value, bool):
                # Boolean values stored as uint8
                c_data = self._ffi.new("uint8_t*", int(value))
                dtype = self._c_lib.LIBENV_DTYPE_UINT8
                count = 1
            elif isinstance(value, int):
                # Integer values stored as int32
                assert -(2**31) <= value < 2**31, f"Integer out of range: {value}"
                c_data = self._ffi.new("int32_t*", value)
                dtype = self._c_lib.LIBENV_DTYPE_INT32
                count = 1
            elif isinstance(value, float):
                # Float values stored as float32
                c_data = self._ffi.new("float*", value)
                dtype = self._c_lib.LIBENV_DTYPE_FLOAT32
                count = 1
            elif isinstance(value, np.ndarray):
                # Numpy arrays converted to bytes
                c_data = self._ffi.new("char[]", value.tobytes())
                if value.dtype == np.dtype("uint8"):
                    dtype = self._c_lib.LIBENV_DTYPE_UINT8
                elif value.dtype == np.dtype("int32"):
                    dtype = self._c_lib.LIBENV_DTYPE_INT32
                elif value.dtype == np.dtype("float32"):
                    dtype = self._c_lib.LIBENV_DTYPE_FLOAT32
                else:
                    raise ValueError(f"Unsupported numpy dtype: {value.dtype}")
                count = value.size
            else:
                raise ValueError(
                    f"Unsupported option type: {type(value)} for key {key}"
                )

            # Fill C option struct
            c_option_array[i].name = name
            c_option_array[i].dtype = dtype
            c_option_array[i].count = count
            c_option_array[i].data = c_data
            keepalives.append(c_data)

        keepalives.append(c_option_array)
        c_options.items = c_option_array
        c_options.count = len(options)

        return c_options, keepalives

    def _create_environment(self):
        """Create single C environment instance"""
        self._c_options, self._options_keepalives = self._dict_to_c_options(
            self.options
        )
        self._c_env = self._c_lib.libenv_make(1, self._c_options)
        if self._c_env == self._ffi.NULL:
            raise RuntimeError("Failed to create environment")

        # Verify library version
        version = self._c_lib.libenv_version()
        assert version == 1, f"libenv version mismatch, got {version} but expected 1"

    def _setup_spaces(self):
        """Setup observation and action spaces by querying the C environment"""
        # Query the C environment for actual space specifications
        ob_space, ob_specs = self._get_space(self._c_lib.LIBENV_SPACE_OBSERVATION)
        ac_space, ac_specs = self._get_space(self._c_lib.LIBENV_SPACE_ACTION)

        # Set gymnasium spaces
        self.observation_space = ob_space
        self.action_space = ac_space

        # Store specs for buffer allocation
        self._ob_specs = ob_specs
        self._ac_specs = ac_specs

    def _get_space(self, space_type: int) -> tuple[spaces.Space, list]:
        """Query C environment for space specification and convert to gymnasium space"""
        # Get number of tensortypes in this space
        count = self._c_lib.libenv_get_tensortypes(
            self._c_env, space_type, self._ffi.NULL
        )
        if count == 0:
            return spaces.Dict({}), []

        # Allocate and get tensortype specifications
        c_tensortypes = self._ffi.new("struct libenv_tensortype[%d]" % count)
        self._c_lib.libenv_get_tensortypes(self._c_env, space_type, c_tensortypes)

        # Convert to gymnasium spaces
        space_dict = {}
        specs = []

        for i in range(count):
            c_tt = c_tensortypes[i]

            name = self._ffi.string(c_tt.name).decode("utf8")
            shape = tuple(c_tt.shape[j] for j in range(c_tt.ndim))

            # Convert C types to numpy types
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

                if shape == ():  # Scalar discrete space
                    gym_space = spaces.Discrete(high + 1)
                else:  # Multi-dimensional discrete space
                    gym_space = spaces.Box(low=low, high=high, shape=shape, dtype=dtype)
            else:
                raise ValueError("Unknown scalar type")

            space_dict[name] = gym_space
            specs.append(Spec(name=name, shape=shape, dtype=dtype))

        # Return Dict space if multiple tensors, otherwise single space
        if len(space_dict) == 1:
            return list(space_dict.values())[0], specs
        else:
            return spaces.Dict(space_dict), specs

    def get_combos(self):
        """Get the 15 action combinations used by Procgen"""
        return [
            ("LEFT", "DOWN"),  # 0
            ("LEFT",),  # 1
            ("LEFT", "UP"),  # 2
            ("DOWN",),  # 3
            (),  # 4 - no action
            ("UP",),  # 5
            ("RIGHT", "DOWN"),  # 6
            ("RIGHT",),  # 7
            ("RIGHT", "UP"),  # 8
            ("D",),  # 9
            ("A",),  # 10
            ("W",),  # 11
            ("S",),  # 12
            ("Q",),  # 13
            ("E",),  # 14
        ]

    def keys_to_act(self, keys_list):
        """Convert list of keys being pressed to actions (for interactive mode)"""
        result = []
        for keys in keys_list:
            action = None
            max_len = -1
            for i, combo in enumerate(self.get_combos()):
                pressed = True
                for key in combo:
                    if key not in keys:
                        pressed = False

                if pressed and (max_len < len(combo)):
                    action = i
                    max_len = len(combo)

            if action is not None:
                action = np.array([action])
            result.append(action)
        return result

    def _initialize_buffers(self):
        """Initialize memory buffers for C interface using actual space specs"""
        # Get info space specs
        _, info_specs = self._get_space(self._c_lib.LIBENV_SPACE_INFO)

        # Allocate buffers for each space
        self._ob_dict, self._c_ob_buffers = self._allocate_space_buffers(self._ob_specs)
        self._ac_dict, self._c_ac_buffers = self._allocate_space_buffers(self._ac_specs)
        self._info_dict, self._c_info_buffers = self._allocate_space_buffers(info_specs)

        # Allocate reward and done buffers
        self._rewards, self._c_rew_buffer = self._allocate_single_buffer(
            np.dtype("float32")
        )
        self._dones, self._c_done_buffer = self._allocate_single_buffer(
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

    def _allocate_space_buffers(self, specs: list) -> tuple[dict[str, np.ndarray], Any]:
        """Allocate buffers for a space (observation, action, or info)"""
        result = {}
        if not specs:
            return result, self._ffi.NULL

        length = len(specs)  # Single environment
        buffers = self._ffi.new(f"void *[{length}]")

        for space_idx, spec in enumerate(specs):
            # Single environment shape
            arr = self._create_aligned_array(spec.shape, spec.dtype)
            result[spec.name] = arr
            buffers[space_idx] = self._ffi.from_buffer(arr.data)

        return result, buffers

    def _allocate_single_buffer(self, dtype: np.dtype) -> tuple[np.ndarray, Any]:
        """Allocate buffer for single array (rewards or dones)"""
        arr = self._create_aligned_array((), dtype)  # Scalar for single env
        return arr, self._ffi.from_buffer(arr.data)

    def _create_aligned_array(
        self, shape: tuple[int, ...], dtype: np.dtype, align: int = 64
    ) -> np.ndarray:
        """Create memory-aligned numpy array for better performance"""
        n_bytes = np.prod(shape) * dtype.itemsize if shape else dtype.itemsize
        arr = np.zeros(n_bytes + (align - 1), dtype=np.uint8)
        data_align = arr.ctypes.data % align
        offset = 0 if data_align == 0 else (align - data_align)
        view = arr[offset : offset + n_bytes].view(dtype)
        return view.reshape(shape) if shape else view.reshape(())

    def reset(self, *, seed=None, options=None):
        """Reset environment"""
        if seed is not None:
            # Procgen handles seeding through the start_level/num_levels mechanism
            # For dynamic seeding, you'd need to recreate the environment
            pass

        # Get initial observation by calling observe
        self._c_lib.libenv_observe(self._c_env)

        # Extract observation - for Procgen, this is the "rgb" tensor
        if "rgb" in self._ob_dict:
            obs = self._ob_dict["rgb"].copy()
        else:
            # If observation space is a dict, return the full dict
            obs = {key: arr.copy() for key, arr in self._ob_dict.items()}

        # Extract info
        info = {key: arr.copy() for key, arr in self._info_dict.items()}

        return obs, info

    def step(self, action):
        """Step environment"""
        # Set action in buffer - for Procgen, this is the "action" tensor
        if "action" in self._ac_dict:
            if isinstance(action, (int, np.integer)):
                action = np.array(action, dtype=np.int32)
            self._ac_dict["action"].flat[0] = action
        else:
            raise ValueError("Action space does not contain 'action' key")

        # Execute action and get new observation
        self._c_lib.libenv_act(self._c_env)
        self._c_lib.libenv_observe(self._c_env)

        # Extract results
        if "rgb" in self._ob_dict:
            obs = self._ob_dict["rgb"].copy()
        else:
            obs = {key: arr.copy() for key, arr in self._ob_dict.items()}

        reward = float(self._rewards.flat[0])
        terminated = bool(self._dones.flat[0])
        truncated = False  # Procgen typically doesn't use truncation
        info = {key: arr.copy() for key, arr in self._info_dict.items()}

        return obs, reward, terminated, truncated, info

    def render(self):
        """Render environment"""
        if self.render_mode == "rgb_array":
            # For Procgen, the RGB observation is the rendered frame
            if "rgb" in self._ob_dict:
                return self._ob_dict["rgb"].copy()
            else:
                raise ValueError("RGB observation not available")
        elif self.render_mode == "human":
            # For human rendering, you'd typically display the image
            # This would require additional display libraries (cv2, pygame, etc.)
            pass

    def get_state(self):
        """Get serialized environment state for reproducibility"""
        # Based on the C++ implementation, max state size is used
        MAX_STATE_SIZE = 2**20  # 1MB buffer
        buf = self._ffi.new(f"char[{MAX_STATE_SIZE}]")

        # Call C function to serialize state for environment 0 (single env)
        state_size = self._c_lib.get_state(self._c_env, 0, buf, MAX_STATE_SIZE)

        # Return as bytes
        return bytes(self._ffi.buffer(buf, state_size))

    def set_state(self, state_bytes):
        """Set environment state from serialized bytes"""
        # Call C function to deserialize state for environment 0
        self._c_lib.set_state(self._c_env, 0, state_bytes, len(state_bytes))

        # After deserializing, update observation buffers
        self._c_lib.libenv_observe(self._c_env)

    def close(self):
        """Close environment and free resources"""
        if hasattr(self, "_c_env") and self._c_env != self._ffi.NULL:
            self._c_lib.libenv_close(self._c_env)
            self._c_env = self._ffi.NULL

        # Clear references to help with cleanup
        if hasattr(self, "_options_keepalives"):
            self._options_keepalives = None

    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, "close"):
            self.close()
