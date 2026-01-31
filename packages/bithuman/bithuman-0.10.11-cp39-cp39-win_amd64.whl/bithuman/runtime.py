"""Bithuman Runtime."""

from __future__ import annotations

import asyncio
import copy
import logging
import os
import threading
import time
from functools import cached_property
from pathlib import Path
from queue import Empty, Queue
from threading import Event
from typing import Callable, Generic, Iterable, Optional, Tuple, TypeVar

import numpy as np
from loguru import logger

from . import audio as audio_utils
from .api import AudioChunk, VideoControl, VideoFrame
from .config import load_settings
from .lib.generator import BithumanGenerator
from .utils import calculate_file_hash
from .video_graph import Frame as FrameMeta
from .video_graph import VideoGraphNavigator

logging.getLogger("numba").setLevel(logging.WARNING)

T = TypeVar("T")

BufferEmptyCallback = Callable[[], bool]


class _ActionDebouncer:
    """Prevent redundant action playback across consecutive frames."""

    __slots__ = ("_lock", "_last_signature")

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last_signature: Optional[Tuple[str, str]] = None

    def prepare(self, control: VideoControl) -> None:
        if not control.action:
            return

        signature = (control.action, control.target_video or "")
        with self._lock:
            if not control.force_action and signature == self._last_signature:
                logger.debug("Suppressing repeated action: %s", signature)
                control.action = None
            else:
                self._last_signature = signature

    def reset(self) -> None:
        with self._lock:
            self._last_signature = None


class Bithuman:
    """Bithuman Runtime."""

    def __init__(
        self,
        *,
        input_buffer_size: int = 0,
        token: Optional[str] = None,
        model_path: Optional[str] = None,
        api_secret: Optional[str] = None,
        api_url: str = "https://auth.api.bithuman.ai/v1/runtime-tokens/request",
        tags: Optional[str] = None,
        insecure: bool = True,
        num_threads: int = 0,
        verbose: Optional[bool] = None,
    ) -> None:
        """Initialize the Bithuman Runtime.

        Args:
            input_buffer_size: The size of the input buffer.
            token: The token for the Bithuman Runtime. Either token or api_secret must be provided.
            model_path: The path to the avatar model.
            api_secret: API Secret for API authentication. Either token or api_secret must be provided.
            api_url: API endpoint URL for token requests.
            tags: Optional tags for token request.
            insecure: Disable SSL certificate verification (not recommended for production use).
            num_threads: Number of threads for processing, 0 = single-threaded, >0 = use specified number of threads, <0 = auto-detect optimal thread count
            verbose: Enable verbose logging for token validation. If None, reads from BITHUMAN_VERBOSE environment variable.
        """
        # Set verbose from parameter or environment variable
        if verbose is None:
            verbose = os.getenv("BITHUMAN_VERBOSE", "false").lower() in ("true", "1", "yes", "on")
        self._verbose = verbose
        self._num_threads = num_threads

        # Transaction ID will be generated in C++ layer at start() to prevent user tampering
        self.transaction_id = ""

        logger.debug(
            f"Initializing Bithuman runtime with: model_path={model_path}, token={token is not None}, api_secret={api_secret is not None}, verbose={verbose}"
        )
        
        # Log environment variables for debugging
        logger.debug(f"BITHUMAN_VERBOSE env var: {os.getenv('BITHUMAN_VERBOSE', 'not set')}")
        logger.debug(f"LOADING_MODE env var: {os.getenv('LOADING_MODE', 'not set')}")
        
        # Mask sensitive information in logs
        if api_secret:
            masked_secret = f"{api_secret[:5]}...{api_secret[-5:] if len(api_secret) > 10 else '***'}"
            logger.debug(f"API secret provided: {masked_secret}")
        if token:
            masked_token = f"{token[:10]}...{token[-10:] if len(token) > 20 else '***'}"
            logger.debug(f"Token provided: {masked_token}")

        if not token and not api_secret:
            logger.error("Neither token nor api_secret provided")
            raise ValueError("Either token or api_secret must be provided")

        self.settings = copy.deepcopy(load_settings())

        try:
            # Initialize generator with token refresh parameters if provided
            # Token refresh will start automatically
            self.generator = BithumanGenerator(
                audio_encoder_path=str(self.settings.AUDIO_ENCODER_PATH),
                api_secret=api_secret if api_secret else None,
                api_url=api_url if api_secret else None,
                model_path=model_path if api_secret else None,
                tags=tags if api_secret else None,
                insecure=insecure if api_secret else False,
            )
        except Exception as e:
            logger.error(f"Failed to initialize BithumanGenerator: {e}")
            raise

        self.video_graph: Optional[VideoGraphNavigator] = None

        # Store token request parameters
        # Note: These are stored as private attributes to prevent direct modification
        # after initialization. Token refresh parameters are locked once refresh starts.
        self._model_path = model_path
        self._api_secret = api_secret
        self._api_url = api_url
        self._tags = tags
        self._insecure = insecure
        self._token = token
        # Track if token refresh has been started to prevent parameter changes
        self._token_refresh_started = False

        # Token refresh state
        self._action_debouncer = _ActionDebouncer()
        
        # Account status flag - set to True when account has issues (402, 403, etc.)
        self._account_status_error = threading.Event()

        try:
            self._warmup()
        except Exception as e:
            logger.error(f"Warmup failed: {e}")
            raise

        # Ignore audios when muted
        self.muted = Event()
        self.interrupt_event = Event()
        self._input_buffer = ThreadSafeAsyncQueue[VideoControl](
            maxsize=input_buffer_size
        )

        # Video
        self.audio_batcher = audio_utils.AudioStreamBatcher(
            output_sample_rate=self.settings.INPUT_SAMPLE_RATE
        )
        self._video_loaded = False
        self._sample_per_video_frame = (
            self.settings.INPUT_SAMPLE_RATE / self.settings.FPS
        )
        self._idle_timeout: float = 0.001

        self._model_hash = None
        if self._model_path:
            # load model if provided
            self._initialize_token()
            self.set_model(self._model_path)

    def set_idle_timeout(self, idle_timeout: float) -> None:
        """Set the idle timeout for the Bithuman Runtime.

        Args:
            idle_timeout: The idle timeout in seconds.
        """
        self._idle_timeout = idle_timeout

    def _regenerate_transaction_id(self) -> None:
        """Generate transaction ID for new runtime sessions.

        This method is called when starting the runtime to ensure each session
        has a unique transaction identifier. Once token refresh starts, transaction ID
        is locked and cannot be regenerated to prevent billing bypass.
        """
        old_id = self.transaction_id
        self.transaction_id = self.generator.generate_transaction_id()
        logger.debug(f"Generated transaction ID: {old_id} -> {self.transaction_id}")

    def set_token(self, token: str, verbose: Optional[bool] = None) -> bool:
        """Set and validate the token for the Bithuman Runtime.

        This method validates the provided token and sets it for subsequent operations if valid.

        Args:
            token: The token to validate and set.
            verbose: Enable verbose logging for token validation. If None, uses instance default.

        Returns:
            bool: True if token is valid and set successfully, False otherwise.

        Raises:
            ValueError: If the token is invalid.
        """
        if verbose is None:
            verbose = self._verbose
            
        logger.debug(f"Attempting to set token: {token[:10]}...{token[-10:] if len(token) > 20 else '***'}")
        
        is_valid = self.generator._generator.validate_token(token, verbose)
        if not is_valid:
            logger.error("Token validation failed - token is invalid")
            raise ValueError("Invalid token")

        logger.debug("Token validated and set successfully")
        return True

    def is_token_validated(self) -> bool:
        """Check if the token is validated."""
        return self.generator.is_token_validated()

    def get_expiration_time(self) -> int:
        """Get the expiration time of the token."""
        return self.generator.get_expiration_time()
    
    
    def _handle_token_validation_error(self, e: RuntimeError, context: str = "") -> RuntimeError:
        """Handle token validation errors.
        
        This method checks if a RuntimeError is related to token validation failure
        and converts it to a standardized exception that can be caught by callers.
        
        Args:
            e: The RuntimeError exception to check
            context: Additional context about where the error occurred
            
        Returns:
            RuntimeError: A standardized token validation error, or re-raises the original exception
        """
        error_msg = str(e).lower()
        token_expired_indicators = [
            "token has expired",
            "validation failed: token has expired",
            "validation failed: token not validated",
        ]
        
        for indicator in token_expired_indicators:
            if indicator in error_msg:
                logger.error(
                    f"Token validation failed{(' during ' + context) if context else ''}: {str(e)}"
                )
                # Return a standardized exception that can be caught by callers
                return RuntimeError("Token validation failed: token has expired")
        
        # Not a token expiration error, re-raise the original exception
        raise

    def _initialize_token(self) -> None:
        """Initialize token if provided by user.
        
        If user provided a token, validate and set it.
        If user provided api_secret, token refresh is handled automatically.
        """
        if self._token:
            logger.debug("Token provided, validating...")
            try:
                is_valid = self.generator._generator.validate_token(self._token, self._verbose)
                if not is_valid:
                    raise ValueError("Token validation failed")
                logger.debug("Token validated and set successfully")
            except Exception as e:
                logger.warning(f"Token validation failed: {e}")
                raise
        # If api_secret is provided, token refresh is handled automatically


    def set_model(self, model_path: str) -> "Bithuman":
        """Set the video file or workspace directory.

        Args:
            model_path: The workspace directory.
        """
        if not model_path:
            logger.error("No model path provided to set_model()")
            raise ValueError("Model path cannot be empty")

        if model_path == self._model_path and self._video_loaded:
            logger.debug("Model path is the same as the current model path, skipping")
            return

        if not Path(model_path).exists():
            raise FileNotFoundError(f"Model path {model_path} does not exist")

        # Security check: If token refresh is already running, verify model_path matches
        # This prevents users from changing model_path after token refresh has started
        if self._api_secret and self._api_url:
            if self.generator.is_token_refresh_running():
                # Token refresh is already running - verify model_path hasn't changed
                if self._model_path and model_path != self._model_path:
                    logger.error(
                        f"Security violation: Cannot change model_path from '{self._model_path}' "
                        f"to '{model_path}' after token refresh has started. "
                        "Token refresh parameters are locked for security."
                    )
                    raise RuntimeError(
                        "Cannot change model_path after token refresh has started. "
                        "This is a security restriction."
                    )
            else:
                # Token refresh not started yet - request initial token for validation (not refresh)
                # This is needed for load_data() validation, but doesn't start background refresh thread
                try:
                    # Generate transaction ID before requesting token
                    if not self.transaction_id:
                        self._regenerate_transaction_id()
                    
                    # Request initial token (single request, no background refresh thread)
                    initial_token = self.generator.request_token(
                        api_url=self._api_url,
                        api_secret=self._api_secret,
                        model_path=model_path,
                        tags=self._tags,
                        transaction_id=self.transaction_id,
                        insecure=self._insecure,
                        timeout=30.0
                    )
                    
                    # Validate and set the token
                    is_valid = self.generator._generator.validate_token(initial_token, self._verbose)
                    if not is_valid:
                        logger.error("Initial token validation failed in set_model()")
                        raise RuntimeError("Initial token validation failed")
                    
                    logger.debug("Initial token requested and validated in set_model()")
                except Exception as e:
                    logger.error(f"Failed to request initial token in set_model(): {e}")
                    raise

        # Store the model path for token requests
        self._model_path = model_path

        if Path(model_path).is_file():
            # Set model hash for JWT validation (used by add_video)
            try:
                model_hash = self.generator.set_model_hash_from_file(model_path)
                self._model_hash = model_hash
            except Exception as e:
                logger.error(f"Failed to calculate model hash: {e}")
                raise
        else:
            logger.info(
                "Skip model hash verification for non-file avatar model, "
                "make sure the token is valid for kind of usage."
            )
            self._model_hash = None

        try:
            self.video_graph = VideoGraphNavigator.from_workspace(
                model_path, extract_to_local=self.settings.EXTRACT_WORKSPACE_TO_LOCAL
            ).load_workspace()
        except Exception as e:
            logger.error(f"Failed to create VideoGraphNavigator or load workspace: {e}")
            raise

        try:
            self.video_graph.update_runtime_configs(self.settings)
        except Exception as e:
            logger.error(f"Failed to update runtime configs: {e}")
            raise

        try:
            self.generator.set_output_size(self.settings.OUTPUT_WIDTH)
        except Exception as e:
            logger.error(f"Failed to set output size: {e}")
            raise

        self._video_loaded = False

        try:
            self.load_data()
        except Exception as e:
            logger.error(f"load_data() failed: {e}")
            raise

        return self

    @property
    def model_hash(self) -> Optional[str]:
        """Get the model hash (read-only).

        Returns the unique model hash that was generated during model loading.
        This property is read-only and cannot be modified after initialization
        after initialization.

        Returns:
            Optional[str]: The model hash if a file model was loaded, None otherwise.
        """
        return self._model_hash

    def load_data(self) -> None:
        """Load the workspace and set up related components."""
        if self._video_loaded:
            return
        if self.video_graph is None:
            logger.error("Video graph is None. Model may not be set properly.")
            raise ValueError("Video graph is not set. Call set_model() first.")

        models_path = Path(self.video_graph.avatar_model_path)

        def find_avatar_data_file(video_path: str) -> Optional[str]:
            video_name = Path(video_path).stem
            for type in ["feature-first", "time-first"]:
                files = list(models_path.glob(f"*/{video_name}.{type}.*"))
                if files:
                    return str(files[0])
            return None

        try:
            audio_feature_files = list(models_path.glob("*/feature_centers.npy"))
            audio_feature_file = audio_feature_files[0]
        except IndexError:
            logger.error(f"Audio features file not found in {models_path}")
            raise FileNotFoundError(f"Audio features file not found in {models_path}")

        try:
            audio_features = np.load(audio_feature_file)
        except Exception as e:
            logger.error(f"Failed to load audio features: {e}")
            raise

        try:
            self.generator.set_audio_feature(audio_features)
        except Exception as e:
            logger.error(f"Failed to set audio feature in generator: {e}")
            raise

        videos = list(self.video_graph.videos.items())
        filler_videos = list(self.video_graph.filler_videos.items())
        logger.info(
            f"Loading model data: {len(videos)} models and {len(filler_videos)} fillers"
        )

        for name, video in videos + filler_videos:
            video_data_path = video.video_data_path
            avatar_data_path = find_avatar_data_file(video.video_path)

            if video.lip_sync_required:
                if not (video_data_path and avatar_data_path):
                    logger.error(f"Model data not found for video {name}")
                    raise ValueError(f"Model data not found for video {name}")
            else:
                video_data_path, avatar_data_path = "", ""

            # Process the video data file if needed
            try:
                video_data_path = self._process_video_data_file(video_data_path)
            except Exception as e:
                logger.error(f"Failed to process video data file for {name}: {e}")
                raise

            try:
                self.generator.add_video(
                    name,
                    video_path=video.video_path,
                    video_data_path=video_data_path,
                    avatar_data_path=avatar_data_path,
                    compression_type=self.settings.COMPRESS_METHOD,
                    loading_mode=self.settings.LOADING_MODE,
                    thread_count=self._num_threads,
                )
            except Exception as e:
                logger.error(f"Failed to add video {name} to generator: {e}")
                raise

        logger.info("Model data loaded successfully")
        self._video_loaded = True

    def get_first_frame(self) -> Optional[np.ndarray]:
        """Get the first frame of the video."""
        if not self.video_graph:
            logger.error("Model is not set. Call set_model() first.")
            return None
        try:
            frame = self.video_graph.get_first_frame(self.settings.OUTPUT_WIDTH)
            return frame
        except Exception as e:
            logger.error(f"Failed to get the first frame: {e}")
            return None

    def get_frame_size(self) -> tuple[int, int]:
        """Get the frame size in width and height."""
        image = self.get_first_frame()
        if image is None:
            logger.error("Failed to get the first frame")
            raise ValueError("Failed to get the first frame")
        size = (image.shape[1], image.shape[0])
        return size

    def interrupt(self) -> None:
        """Interrupt the daemon."""
        # clear the input buffer
        while not self._input_buffer.empty():
            try:
                self._input_buffer.get_nowait()
            except Empty:
                break
        self.audio_batcher.reset()
        self.interrupt_event.set()

    def set_muted(self, mute: bool) -> None:
        """Set the muted state."""
        if mute:
            self.muted.set()
        else:
            self.muted.clear()

    def push_audio(
        self, data: bytes, sample_rate: int, last_chunk: bool = True
    ) -> None:
        """Push the audio to the input buffer."""
        self._input_buffer.put(VideoControl.from_audio(data, sample_rate, last_chunk))

    def flush(self) -> None:
        """Flush the input buffer."""
        self._input_buffer.put(VideoControl(end_of_speech=True))

    def push(self, control: VideoControl) -> None:
        """Push the control (with audio, text, action, etc.) to the input buffer."""
        self._input_buffer.put(control)

    def run(
        self,
        out_buffer_empty: Optional[BufferEmptyCallback] = None,
        *,
        idle_timeout: float | None = None,
    ) -> Iterable[VideoFrame]:
        # Start token refresh if api_secret is provided and refresh is not already running
        # This ensures token is available before runtime starts processing
        if self._api_secret and self._api_url and self._model_path:
            if not self.generator.is_token_refresh_running():
                try:
                    # Generate transaction ID before starting token refresh
                    if not self.transaction_id:
                        self._regenerate_transaction_id()
                    
                    success = self.generator.start_token_refresh(
                        api_url=self._api_url,
                        api_secret=self._api_secret,
                        model_path=self._model_path,
                        tags=self._tags,
                        refresh_interval=60,
                        insecure=self._insecure,
                        timeout=30.0
                    )
                    if success:
                        logger.debug("Token refresh started in run()")
                        self._token_refresh_started = True
                        # startTokenRefresh does synchronous initial token request, so token should be ready
                        import time
                        time.sleep(0.2)  # Give a moment for token validation state to be set
                    else:
                        logger.error("Failed to start token refresh in run()")
                        raise RuntimeError("Failed to start token refresh")
                except Exception as e:
                    logger.error(f"Failed to start token refresh in run(): {e}")
                    raise
            else:
                # Token refresh already running - just ensure transaction ID is set
                if not self.transaction_id:
                    self._regenerate_transaction_id()
        else:
            # Generate transaction ID only if not already set (prevents bypassing billing)
            if not self.transaction_id:
                self._regenerate_transaction_id()

        # Current frame index, reset for every new audio
        if self.video_graph is None:
            raise ValueError("Model is not set. Call set_model() first.")

        curr_frame_index = 0
        action_played = False  # Whether the action is played in this speech
        token_expired = False  # Flag to track token expiration
        
        while True:
            # Check if token has expired - if so, stop immediately
            if token_expired:
                logger.error("Token has expired, stopping runtime")
                # Stop token refresh if running
                if self.generator.is_token_refresh_running():
                    try:
                        self.generator._generator.stop_token_refresh()
                    except Exception as stop_error:
                        logger.warning(f"Error stopping token refresh: {stop_error}")
                break
                
            try:
                if self.interrupt_event.is_set():
                    # Clear the interrupt event for the next loop
                    self.interrupt_event.clear()
                    action_played = False
                control = self._input_buffer.get(
                    timeout=idle_timeout or self._idle_timeout
                )
                if control.action:
                    logger.debug(f"Action: {control.action}")
                if self.muted.is_set():
                    # Consume and skip the audio when muted
                    control = VideoControl(message_id="MUTED")
                    action_played = False  # Reset the action played flag
            except Empty:
                if out_buffer_empty and not out_buffer_empty():
                    continue
                control = VideoControl(message_id="IDLE")  # idle

            if self.video_graph is None:
                # cleanup is called
                logger.debug("Stopping runtime after cleanup")
                break

            # Edit the video based on script if the input is None
            if not control.target_video and not control.action:
                control.target_video, control.action, reset_action = (
                    self.video_graph.videos_script.get_video_and_actions(
                        curr_frame_index,
                        control.emotion_preds,
                        text=control.text,
                        is_idle=control.is_idle,
                        settings=self.settings,
                    )
                )
                if reset_action:
                    action_played = False
                    
            if not control.is_idle:
                # Avoid playing the action multiple times in a conversation
                if action_played and not control.force_action:
                    control.action = None
                elif control.action:
                    action_played = True

            try:
                frames_yielded = False
                for frame in self.process(control):
                    yield frame
                    curr_frame_index += 1
                    frames_yielded = True
                    
            except RuntimeError as e:
                # Catch token validation errors
                error_msg = str(e).lower()
                if ("token has expired" in error_msg or 
                    "token validation failed" in error_msg or
                    "validation failed" in error_msg):
                    logger.error(f"Token validation failed in run() loop: {str(e)}, stopping video stream")
                    token_expired = True
                    # Stop token refresh if running
                    if self.generator.is_token_refresh_running():
                        try:
                            self.generator._generator.stop_token_refresh()
                        except Exception as stop_error:
                            logger.warning(f"Error stopping token refresh: {stop_error}")
                    break
                # Re-raise other RuntimeErrors
                raise

            if control.end_of_speech:
                self.audio_batcher.reset()
                # Passthrough the end flag of the speech
                yield VideoFrame(
                    source_message_id=control.message_id,
                    end_of_speech=control.end_of_speech,
                )

                # Reset the action played flag
                action_played = False
                curr_frame_index = 0
                self.video_graph.videos_script.last_nonidle_frame = 0
                self._action_debouncer.reset()

                # Reset the video graph if needed
                self.video_graph.next_n_frames(num_frames=0, on_user_speech=True)

    def process(self, control: VideoControl) -> Iterable[VideoFrame]:
        """Process the audio or control data."""

        def _get_next_frame() -> FrameMeta:
            if control.action or control.target_video:
                self._action_debouncer.prepare(control)
                if control.action:
                    logger.debug(f"Getting next frame for control: {control.target_video} {control.action}")

            return self.video_graph.next_n_frames(
                num_frames=1,
                target_video_name=control.target_video,
                actions_name=control.action,
                on_agent_speech=control.is_speaking,
                stop_on_user_speech_override=control.stop_on_user_speech,
                stop_on_agent_speech_override=control.stop_on_agent_speech,
            )[0]

        frame_index = 0
        for padded_chunk in self.audio_batcher.push(control.audio):
            audio_array = padded_chunk.array

            # get the mel chunks on padded audio
            mel_chunks = audio_utils.get_mel_chunks(
                audio_utils.int16_to_float32(audio_array), fps=self.settings.FPS
            )
            # unpad the audio and mel chunks
            audio_array = self.audio_batcher.unpad(audio_array)
            start = self.audio_batcher.pre_pad_video_frames
            valid_frames = int(len(audio_array) / self._sample_per_video_frame)
            mel_chunks = mel_chunks[start : start + valid_frames]

            num_frames = len(mel_chunks)
            samples_per_frame = len(audio_array) // max(num_frames, 1)
            for i, mel_chunk in enumerate(mel_chunks):
                if self.muted.is_set():
                    return
                if self.interrupt_event.is_set():
                    self.interrupt_event.clear()
                    return

                try:
                    frame_meta = _get_next_frame()
                    frame = self._process_talking_frame(frame_meta, mel_chunk)
                except RuntimeError as e:
                    # Catch token validation errors
                    error_msg = str(e).lower()
                    if ("token has expired" in error_msg or 
                        "token validation failed" in error_msg or
                        "validation failed" in error_msg):
                        logger.error(f"Token validation failed during frame processing: {str(e)}, stopping video stream")
                        # Re-raise to stop the generator and runtime
                        raise
                    # Re-raise other RuntimeErrors
                    raise

                audio_start = i * samples_per_frame
                audio_end = (
                    audio_start + samples_per_frame
                    if i < num_frames - 1
                    else len(audio_array)
                )
                yield VideoFrame(
                    bgr_image=frame,
                    audio_chunk=AudioChunk(
                        data=audio_array[audio_start:audio_end],
                        sample_rate=padded_chunk.sample_rate,
                        last_chunk=i == num_frames - 1,
                    ),
                    frame_index=frame_index,
                    source_message_id=control.message_id,
                )
                frame_index += 1

        if frame_index == 0 and not control.audio:
            # generate idle frame if no frame is generated
            try:
                frame_meta = _get_next_frame()
                frame = self._process_idle_frame(frame_meta)
            except RuntimeError as e:
                # Catch token validation errors
                error_msg = str(e).lower()
                if ("token has expired" in error_msg or 
                    "token validation failed" in error_msg or
                    "validation failed" in error_msg):
                    logger.error("Token validation failed during idle frame processing, stopping video stream")
                    # Re-raise to stop the generator and runtime
                    raise
                # Re-raise other RuntimeErrors
                raise
            
            yield VideoFrame(
                bgr_image=frame,
                frame_index=frame_index,
                source_message_id=control.message_id,
            )

    def _process_talking_frame(
        self, frame: FrameMeta, mel_chunk: np.ndarray
    ) -> np.ndarray:
        """Process a talking frame with audio-driven lip sync.
        
        This method processes audio and generates a frame. Token validation is checked
        internally. If token validation fails, RuntimeError will be raised.
        
        Args:
            frame: Frame metadata
            mel_chunk: Mel spectrogram chunk
            
        Returns:
            Processed frame as numpy array
            
        Raises:
            RuntimeError: If token validation fails
        """
        try:
            frame_np = self.generator.process_audio(
                mel_chunk, frame.video_name, frame.frame_index
            )
            return frame_np
        except RuntimeError as e:
            # Handle token validation errors
            raise self._handle_token_validation_error(e, "talking frame processing") from e

    def _process_idle_frame(self, frame: FrameMeta) -> np.ndarray:
        """Get the idle frame with cache.
        
        This method gets an idle frame. Token validation is checked automatically.
        
        Args:
            frame: Frame metadata
            
        Returns:
            Processed frame as numpy array
            
        Raises:
            RuntimeError: If token validation fails
        """
        try:
            if not self.settings.PROCESS_IDLE_VIDEO:
                frame_np = self.generator.get_original_frame(
                    frame.video_name, frame.frame_index
                )
            else:
                frame_np = self.generator.process_audio(
                    self.silent_mel_chunk, frame.video_name, frame.frame_index
                )
            
            return frame_np
        except RuntimeError as e:
            # Handle token validation errors
            raise self._handle_token_validation_error(e, "idle frame processing") from e

    @cached_property
    def silent_mel_chunk(self) -> np.ndarray:
        """The mel chunk for silent audio."""
        audio_np = np.zeros(self.settings.INPUT_SAMPLE_RATE * 1, dtype=np.float32)
        return audio_utils.get_mel_chunks(audio_np, fps=self.settings.FPS)[0]

    def _process_video_data_file(self, video_data_path: str) -> str:
        """Process the video data file."""
        if not video_data_path:
            return video_data_path

        if video_data_path.endswith(".pth"):
            logger.debug(f"Converting pth to h5, torch is required: {video_data_path}")
            from .lib.pth2h5 import convert_pth_to_h5

            return convert_pth_to_h5(video_data_path)
        return video_data_path

    def _warmup(self) -> None:
        """Warm up the audio processing."""
        audio_utils.get_mel_chunks(
            np.zeros(16000, dtype=np.float32), fps=self.settings.FPS
        )


    def cleanup(self) -> None:
        """Clean up the video graph."""
        if self.video_graph:
            self.video_graph.cleanup()
            self.video_graph = None

    def __del__(self) -> None:
        """Clean up the video graph."""
        self.cleanup()

    @classmethod
    def create(
        cls,
        *,
        model_path: Optional[str] = None,
        token: Optional[str] = None,
        api_secret: Optional[str] = None,
        api_url: str = "https://auth.api.bithuman.ai/v1/runtime-tokens/request",
        tags: Optional[str] = None,
        insecure: bool = True,
        input_buffer_size: int = 0,
        verbose: Optional[bool] = None,
    ) -> "Bithuman":
        """Create a fully initialized Bithuman instance.
        
        Token validation and refresh are handled automatically:
        - If token is provided, it will be validated
        - If api_secret and model_path are provided, token refresh will start when run() is called
        """
        # Create instance - token refresh will start lazily when run() is called
        instance = cls(
            input_buffer_size=input_buffer_size,
            token=token,
            model_path=model_path,
            api_secret=api_secret,
            api_url=api_url,
            tags=tags,
            insecure=insecure,
            verbose=verbose,
        )

        # Validate token if provided (validation happens in _initialize_token during start/set_model)
        # Token refresh will start lazily when run() is called if api_secret is provided
        
        # Set model if provided
        if model_path:
            try:
                instance.set_model(model_path)
            except Exception as e:
                logger.error(f"Failed to set model: {e}")
                raise
        else:
            logger.warning("No model path provided to factory method")

        # Verify initialization success
        try:
            if instance.video_graph is None:
                raise ValueError("Video graph not initialized")
        except Exception as e:
            logger.error(f"Initialization verification failed: {e}")
            raise

        return instance



class ThreadSafeAsyncQueue(Generic[T]):
    """A thread-safe queue that can be used from both async and sync contexts.

    This queue uses a standard threading.Queue internally for thread safety,
    but provides async methods for use in async contexts.
    """

    def __init__(
        self, maxsize: int = 0, event_loop: Optional[asyncio.AbstractEventLoop] = None
    ):
        """Initialize the queue.

        Args:
            maxsize: Maximum size of the queue. 0 means unlimited.
            event_loop: The event loop to use.
        """
        self._queue = Queue[T](maxsize=maxsize)
        self._loop = event_loop

    def put_nowait(self, item: T) -> None:
        """Put an item into the queue without blocking."""
        self._queue.put_nowait(item)

    async def aput(self, item: T, *args, **kwargs) -> None:
        """Put an item into the queue asynchronously."""
        # Use run_in_executor to avoid blocking the event loop
        if not self._loop:
            self._loop = asyncio.get_event_loop()
        await self._loop.run_in_executor(None, self._queue.put, item, *args, **kwargs)

    def put(self, item: T, *args, **kwargs) -> None:
        """Put an item into the queue."""
        self._queue.put(item, *args, **kwargs)

    def get_nowait(self) -> T:
        """Get an item from the queue without blocking."""
        return self._queue.get_nowait()

    async def aget(self, *args, **kwargs) -> T:
        """Get an item from the queue asynchronously."""
        # Use run_in_executor to avoid blocking the event loop
        if not self._loop:
            self._loop = asyncio.get_event_loop()
        return await self._loop.run_in_executor(None, self._queue.get, *args, **kwargs)

    def get(self, *args, **kwargs) -> T:
        """Get an item from the queue."""
        return self._queue.get(*args, **kwargs)

    def task_done(self) -> None:
        """Mark a task as done."""
        self._queue.task_done()

    def empty(self) -> bool:
        """Check if the queue is empty."""
        return self._queue.empty()

    def qsize(self) -> int:
        """Get the size of the queue."""
        return self._queue.qsize()

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Set the event loop."""
        self._loop = loop
