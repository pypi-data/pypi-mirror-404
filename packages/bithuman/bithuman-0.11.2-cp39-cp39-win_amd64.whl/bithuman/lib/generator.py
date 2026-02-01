from __future__ import annotations

import ctypes
import os
import sys
from typing import Optional, Union

import numpy as np
from loguru import logger


def _preload_onnxruntime() -> None:
    """Preload the onnxruntime shared library into the global symbol namespace.

    When the Python ``onnxruntime`` package is installed, its native library
    (``libonnxruntime.so.1`` on Linux, ``libonnxruntime.*.dylib`` on macOS) is
    loaded into the process.  The bithuman C++ extension (``_bithuman_py``) also
    links against the same library via its ``NEEDED`` / ``LC_LOAD_DYLIB`` entry.

    Without this preload, the dynamic linker may load a *second* copy of the
    ONNX Runtime library — one from the Python package and one bundled with
    bithuman — into the same process.  Two copies of ONNX Runtime initialise
    independent global state (memory pools, thread pools, ORT environment
    singletons) while sharing a single glibc/CRT heap, which causes
    non-deterministic ``malloc(): corrupted top size`` crashes.

    By preloading the Python package's copy with ``RTLD_GLOBAL`` *before*
    ``_bithuman_py`` is imported, the dynamic linker sees that a library with
    the matching SONAME is already resident and reuses it instead of loading the
    bundled copy.

    If the ``onnxruntime`` Python package is **not** installed this function is
    a no-op and the extension will fall back to any bundled copy found via its
    RPATH/RUNPATH.
    """
    try:
        import onnxruntime  # noqa: F811
    except ImportError:
        return  # onnxruntime not installed — nothing to preload

    ort_dir = os.path.join(os.path.dirname(onnxruntime.__file__), "capi")
    if not os.path.isdir(ort_dir):
        return

    if sys.platform == "linux":
        # Look for libonnxruntime.so.1* (e.g. libonnxruntime.so.1.20.1)
        candidates = sorted(
            (f for f in os.listdir(ort_dir) if f.startswith("libonnxruntime.so.1")),
            reverse=True,  # prefer the most-versioned name
        )
    elif sys.platform == "darwin":
        candidates = sorted(
            (f for f in os.listdir(ort_dir) if f.startswith("libonnxruntime.") and f.endswith(".dylib")),
            reverse=True,
        )
    else:
        return  # Windows DLL loading doesn't suffer from the same issue

    for name in candidates:
        lib_path = os.path.join(ort_dir, name)
        try:
            ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)
            logger.debug(f"Preloaded onnxruntime library: {lib_path}")
            return
        except OSError:
            continue


_preload_onnxruntime()

from ._bithuman_py import (  # noqa: E402
    BithumanRuntime as LibBithuman,
)
from ._bithuman_py import (  # noqa: E402
    CompressionType,
    LoadingMode,
)


def _parse_compression_type(compression_type: CompressionType | str) -> CompressionType:
    if isinstance(compression_type, CompressionType):
        return compression_type
    maps = {
        "NONE": CompressionType.NONE,
        "JPEG": CompressionType.JPEG,
        "LZ4": CompressionType.LZ4,
        "TEMP_FILE": CompressionType.TEMP_FILE,
    }
    if isinstance(compression_type, str):
        if compression_type not in maps:
            raise ValueError(f"Invalid compression type: {compression_type}")
        compression_type = maps[compression_type]
    return compression_type


def _parse_loading_mode(loading_mode: LoadingMode | str) -> LoadingMode:
    if isinstance(loading_mode, LoadingMode):
        return loading_mode
    maps = {
        "SYNC": LoadingMode.SYNC,
        "ASYNC": LoadingMode.ASYNC,
        "ON_DEMAND": LoadingMode.ON_DEMAND,
    }
    return maps[loading_mode]


class BithumanGenerator:
    """High-level Python wrapper for Bithuman Runtime Generator."""

    # Re-export CompressionType enum
    CompressionType = CompressionType

    def __init__(
        self,
        audio_encoder_path: Optional[str] = None,
        output_size: int = -1,
        api_secret: Optional[str] = None,
        api_url: Optional[str] = None,
        model_path: Optional[str] = None,
        tags: Optional[str] = None,
        insecure: bool = False,
    ):
        """Initialize the generator.

        Args:
            audio_encoder_path: Path to the ONNX audio encoder model
            output_size: Output size for frames
            api_secret: Optional API secret for automatic token refresh
            api_url: Optional API endpoint URL for token requests
            model_path: Optional model file path (for token refresh)
            tags: Optional tags for token requests
            insecure: Whether to disable SSL verification
        """
        if audio_encoder_path is not None:
            audio_encoder_path = str(audio_encoder_path)

        # Validate audio encoder model file before passing to C++ layer.
        # A missing or unreadable file would crash the C++ ONNX session
        # creation, potentially killing the process with no Python exception.
        if audio_encoder_path:
            if not os.path.isfile(audio_encoder_path):
                raise FileNotFoundError(
                    f"Audio encoder model not found: {audio_encoder_path}"
                )
            file_size = os.path.getsize(audio_encoder_path)
            if file_size == 0:
                raise ValueError(
                    f"Audio encoder model is empty (0 bytes): {audio_encoder_path}"
                )
            logger.debug(
                f"Audio encoder model validated: {audio_encoder_path} "
                f"({file_size / 1024:.1f} KB)"
            )

        try:
            self._generator = LibBithuman(audio_encoder_path or "", output_size)
        except Exception as e:
            logger.error(
                f"Failed to initialize C++ runtime with audio encoder "
                f"'{audio_encoder_path}': {e}"
            )
            raise RuntimeError(
                f"ONNX audio encoder initialization failed: {e}. "
                f"This may indicate CPU incompatibility with the INT8 quantized "
                f"model. Check that the deployment environment supports the "
                f"required instruction set."
            ) from e

        # Store initialization parameters for security checks
        # This prevents users from modifying parameters after initialization
        self._initialized_api_secret = api_secret
        self._initialized_api_url = api_url
        self._initialized_model_path = model_path
        self._initialized_tags = tags
        self._initialized_insecure = insecure

        # Token refresh will be started lazily when run() or start() is called
        # This prevents unnecessary token requests during prewarm/initialization

    def set_model_hash_from_file(self, model_path: str) -> str:
        """Set the model hash for verification against the token from a file.

        Args:
            model_path: Path to the model file

        Returns:
            str: The model hash
        """
        return self._generator.set_model_hash_from_file(model_path)

    def get_instance_id(self) -> str:
        """Get the instance ID of this runtime.

        Returns:
            Instance ID
        """
        return self._generator.get_instance_id()
    
    def is_token_refresh_running(self) -> bool:
        """Check if token refresh thread is running.

        Returns:
            bool: True if token refresh is running, False otherwise
        """
        return self._generator.is_token_refresh_running()
    
    def is_account_status_error(self) -> bool:
        """Check if account status error occurred (402, 403, 400).

        This flag is set when token refresh encounters permanent errors.
        When set, runtime operations will fail immediately even if token is valid.

        Returns:
            bool: True if account status error occurred, False otherwise
        """
        return self._generator.is_account_status_error()
    
    def generate_transaction_id(self) -> str:
        """Generate and set a new transaction ID in C++ layer.

        This method generates a new UUID-based transaction ID in C++ layer
        to prevent user tampering. Should be called at the start of each runtime session.

        Returns:
            str: The newly generated transaction ID
        """
        return self._generator.generate_transaction_id()
    
    def get_transaction_id(self) -> str:
        """Get current transaction ID.

        Returns:
            str: The current transaction ID, or empty string if not generated yet
        """
        return self._generator.get_transaction_id()

    def set_audio_encoder(self, audio_encoder_path: str) -> None:
        """Set the audio encoder model path.

        Args:
            audio_encoder_path: Path to the ONNX audio encoder model
        """
        self._generator.set_audio_encoder(str(audio_encoder_path))

    def set_audio_feature(self, audio_feature: Union[str, np.ndarray]) -> None:
        """Set the audio feature.

        Args:
            audio_feature: Path to HDF5 file or numpy array of features
        """
        if isinstance(audio_feature, str):
            self._generator.set_audio_feature(audio_feature)
        else:
            self._generator.set_audio_feature(audio_feature.astype(np.float32))

    def set_output_size(self, output_size: int) -> None:
        """Set the output size.

        Args:
            output_size: Output size
        """
        self._generator.set_output_size(output_size)

    def add_video(
        self,
        video_name: str,
        video_path: str,
        video_data_path: str,
        avatar_data_path: str,
        compression_type: CompressionType | str = CompressionType.JPEG,
        loading_mode: LoadingMode | str = LoadingMode.ASYNC,
        thread_count: int = 0,
    ) -> None:
        """Add a video to the generator.

        Args:
            video_name: Name to identify the video
            video_path: Path to the original video
            video_data_path: Path to the video data HDF5 file
            avatar_data_path: Path to the avatar data file
            compression_type: Type of compression to use (default: JPEG)
            loading_mode: Loading mode to use (default: ASYNC)
            thread_count: Number of threads for processing (default: 0)
        """
        compression_type = _parse_compression_type(compression_type)
        loading_mode = _parse_loading_mode(loading_mode)
        self._generator.add_video(
            str(video_name),
            str(video_path),
            str(video_data_path),
            str(avatar_data_path),
            compression_type,
            loading_mode,
            thread_count,
        )

    def process_audio(
        self, mel_chunk: np.ndarray, video_name: str, frame_idx: int
    ) -> np.ndarray:
        """Process audio chunk and return blended frame.

        Args:
            mel_chunk: Mel spectrogram chunk of shape (80, 16)
            video_name: Name of the video to use
            frame_idx: Frame index in the video

        Returns:
            np.ndarray: Blended frame as RGB image
        """
        return self._generator.process_audio(
            mel_chunk.astype(np.float32), str(video_name), frame_idx
        )

    def get_original_frame(self, video_name: str, frame_idx: int) -> np.ndarray:
        """Get the original frame.

        Args:
            video_name: Name of the video
            frame_idx: Frame index in the video
        """
        return self._generator.get_original_frame(str(video_name), frame_idx)

    def get_num_frames(self, video_name: str) -> int:
        """Get the number of frames in the video.

        Args:
            video_name: Name of the video

        Returns:
            int: Number of frames in the video, -1 if video not found
        """
        return self._generator.get_num_frames(str(video_name))

    def is_token_validated(self) -> bool:
        """Check if the token is validated.

        Returns:
            bool: True if the token is validated, False otherwise
        """
        return self._generator.is_token_validated()

    def get_expiration_time(self) -> int:
        """Get the expiration time of the token.

        Returns:
            int: Expiration time in seconds, -1 if token is not validated
        """
        return self._generator.get_expiration_time()
    
    @staticmethod
    def get_runtime_version() -> str:
        """Get the runtime version.
        
        Returns:
            str: The runtime version string (e.g., "1.2.0")
        """
        from . import _bithuman_py
        return _bithuman_py.BithumanRuntime.get_runtime_version()
    
    
    def request_token(
        self,
        api_url: str,
        api_secret: str,
        model_path: Optional[str] = None,
        tags: Optional[str] = None,
        transaction_id: Optional[str] = None,
        insecure: bool = False,
        timeout: float = 30.0,
    ) -> str:
        """Request a token from the authentication server.
        
        If model_path is provided, the model hash is calculated internally
        from the file.
        
        Args:
            api_url: The API endpoint URL
            api_secret: The API secret for authentication
            model_path: Optional path to model file (hash calculated internally)
            tags: Optional tags
            transaction_id: Optional transaction ID
            insecure: Whether to disable SSL verification (not recommended)
            timeout: Request timeout in seconds
            
        Returns:
            str: The JWT token string if successful
            
        Raises:
            RuntimeError: If request fails (402, 403, 400, etc.)
        """
        from . import _bithuman_py
        return self._generator.request_token(
            api_url,
            api_secret,
            model_path,
            tags,
            transaction_id,
            insecure,
            timeout
        )
    
    def start_token_refresh(
        self,
        api_url: str,
        api_secret: str,
        model_path: Optional[str] = None,
        tags: Optional[str] = None,
        refresh_interval: int = 60,
        insecure: bool = False,
        timeout: float = 30.0,
    ) -> bool:
        """Start token refresh thread.
        
        This method starts a background thread that periodically
        refreshes the token every refresh_interval seconds. If model_path
        is provided, the model hash is calculated internally from the file.
        
        **Security Note**: This method should only be called internally by the runtime.
        Direct calls by users may bypass security checks. If token refresh is already
        running, this method will return False.
        
        Args:
            api_url: The API endpoint URL
            api_secret: The API secret for authentication
            model_path: Optional path to model file (hash calculated internally)
            tags: Optional tags
            refresh_interval: Refresh interval in seconds (default: 60)
            insecure: Whether to disable SSL verification (not recommended)
            timeout: Request timeout in seconds
            
        Returns:
            bool: True if refresh thread started successfully, False if already running
        """
        # Security check: If token refresh is already running, prevent restart
        if self.is_token_refresh_running():
            logger.warning(
                "Security: Token refresh is already running. "
                "Cannot restart with different parameters. "
                "This prevents security bypass attempts."
            )
            return False
        
        # Security check: Verify parameters match initialization parameters if they were set
        # This prevents users from modifying parameters after initialization
        if hasattr(self, '_initialized_api_secret') and self._initialized_api_secret:
            if api_secret != self._initialized_api_secret:
                logger.error(
                    "Security violation: api_secret does not match initialization parameter. "
                    "This prevents security bypass attempts."
                )
                raise RuntimeError(
                    "Cannot change api_secret after initialization. "
                    "This is a security restriction."
                )
            if api_url != self._initialized_api_url:
                logger.error(
                    "Security violation: api_url does not match initialization parameter. "
                    "This prevents security bypass attempts."
                )
                raise RuntimeError(
                    "Cannot change api_url after initialization. "
                    "This is a security restriction."
                )
        
        from . import _bithuman_py
        return self._generator.start_token_refresh(
            api_url,
            api_secret,
            model_path,
            tags,
            refresh_interval,
            insecure,
            timeout
        )
    