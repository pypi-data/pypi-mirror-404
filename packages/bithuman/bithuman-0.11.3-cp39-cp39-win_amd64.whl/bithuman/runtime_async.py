"""Asynchronous wrapper for Bithuman Runtime."""

from __future__ import annotations

import asyncio
import queue
import threading
import time
from pathlib import Path
from typing import AsyncIterator, Optional, Union

from loguru import logger

from .api import VideoControl, VideoFrame
from .runtime import Bithuman, BufferEmptyCallback

# Sentinel to signal end of frame stream
_STREAM_END = object()


class AsyncBithuman(Bithuman):
    """Asynchronous wrapper for Bithuman Runtime.

    This class wraps the synchronous BithumanRuntime to provide an asynchronous interface.
    It runs the runtime in a separate thread to avoid blocking the asyncio event loop.
    """

    def __init__(
        self,
        *,
        model_path: Optional[str] = None,
        token: Optional[str] = None,
        api_secret: Optional[str] = None,
        api_url: str = "https://auth.api.bithuman.ai/v1/runtime-tokens/request",
        tags: Optional[str] = "bithuman",
        insecure: bool = True,
        input_buffer_size: int = 0,
        output_buffer_size: int = 5,
        load_model: bool = False,
        num_threads: int = 0,
        verbose: Optional[bool] = None,
    ) -> None:
        """Initialize the async runtime with a BithumanRuntime instance.

        Args:
            model_path: The path to the avatar model.
            token: The token for the Bithuman Runtime. Either token or api_secret must be provided.
            api_secret: API Secret for API authentication. Either token or api_secret must be provided.
            api_url: API endpoint URL for token requests.
            tags: Optional tags for token request.
            insecure: Disable SSL certificate verification (not recommended for production use).
            input_buffer_size: Size of the input buffer.
            output_buffer_size: Size of the output buffer.
            load_model: If True, load the model synchronously.
            num_threads: Number of threads for processing, 0 = single-threaded, >0 = use specified number of threads, <0 = auto-detect optimal thread count
            verbose: Enable verbose logging for token validation. If None, reads from BITHUMAN_VERBOSE environment variable.
        """
        # Call parent init WITHOUT the model_path parameter
        # This prevents parent's __init__ from calling set_model()
        logger.debug(
            f"Initializing AsyncBithuman with token={token is not None}, api_secret={api_secret is not None}, verbose={verbose}"
        )
        super().__init__(
            input_buffer_size=input_buffer_size,
            token=token,
            model_path=None,  # Important: Pass None here
            api_secret=api_secret,
            api_url=api_url,
            tags=tags,
            insecure=insecure,
            verbose=verbose,
            num_threads=num_threads,
        )

        # Store the model path for later use
        self._model_path = model_path

        self._model_hash = None

        # Thread management
        self._stop_event = threading.Event()
        self._thread = None

        # Thread-safe queue for cross-thread frame passing (producer thread → async consumer)
        # Using queue.Queue avoids per-frame Future creation overhead of asyncio.run_coroutine_threadsafe
        self._frame_queue: queue.Queue[Union[VideoFrame, Exception, object]] = queue.Queue(
            maxsize=output_buffer_size
        )

        # State
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        if load_model:
            self._initialize_token_sync()
            super().set_model(model_path)

    @classmethod
    async def create(
        cls,
        *,
        model_path: Optional[str] = None,
        token: Optional[str] = None,
        api_secret: Optional[str] = None,
        api_url: str = "https://auth.api.bithuman.ai/v1/runtime-tokens/request",
        tags: Optional[str] = "bithuman",
        insecure: bool = True,
        input_buffer_size: int = 0,
        output_buffer_size: int = 5,
        num_threads: int = 0,
        verbose: Optional[bool] = None,
    ) -> "AsyncBithuman":
        """Create a fully initialized AsyncBithuman instance asynchronously.
        
        Token refresh will start lazily when start() is called if api_secret is provided.
        This prevents unnecessary token requests during prewarm/initialization.
        """
        # Create instance with initial parameters but defer model setting
        instance = cls(
            model_path=None,  # Will set model later
            token=token,
            api_secret=api_secret,
            api_url=api_url,
            tags=tags,
            insecure=insecure,
            input_buffer_size=input_buffer_size,
            output_buffer_size=output_buffer_size,
            verbose=verbose,
        )

        if model_path:
            instance._model_path = model_path
            await instance._initialize_token()
            await instance.set_model(model_path)

        return instance

    async def set_model(self, model_path: str | None = None) -> "AsyncBithuman":
        """Set the avatar model for the runtime.

        Args:
            model_path: The path to the avatar model. If None, uses the model_path provided during initialization.
        """
        # Use the model path provided during initialization if none is provided
        model_path = model_path or self._model_path

        if not model_path:
            logger.error("No model path provided for set_model")
            raise ValueError(
                "Model path must be provided either during initialization or when calling set_model"
            )

        # Store the model path for token requests
        self._model_path = model_path

        # Now run the set_model in the executor and wait for it to finish
        loop = self._loop or asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, super().set_model, model_path)
        except Exception as e:
            logger.error(f"Error in parent set_model: {e}")
            raise

        return self

    async def push_audio(
        self, data: bytes, sample_rate: int, last_chunk: bool = True
    ) -> None:
        """Push audio data to the runtime asynchronously.

        Args:
            data: Audio data in bytes.
            sample_rate: Sample rate of the audio.
            last_chunk: Whether this is the last chunk of the speech.
        """
        control = VideoControl.from_audio(data, sample_rate, last_chunk)
        await self._input_buffer.aput(control)

    async def push(self, control: VideoControl) -> None:
        """Push a VideoControl to the runtime asynchronously.

        Args:
            control: The VideoControl to push.
        """
        await self._input_buffer.aput(control)

    async def flush(self) -> None:
        """Flush the audio buffer, indicating end of speech."""
        await self._input_buffer.aput(VideoControl(end_of_speech=True))

    async def run(
        self,
        out_buffer_empty: Optional[BufferEmptyCallback] = None,
        *,
        idle_timeout: float | None = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> AsyncIterator[VideoFrame]:
        """Stream video frames asynchronously.

        Yields:
            VideoFrame objects from the runtime.
        """
        # Start the runtime if not already running
        await self.start(
            out_buffer_empty=out_buffer_empty,
            idle_timeout=idle_timeout,
            loop=loop,
        )

        try:
            loop = asyncio.get_running_loop()
            while True:
                # Get the next frame from the thread-safe queue via executor
                # This avoids per-frame Future creation overhead
                item = await loop.run_in_executor(None, self._frame_queue.get)

                # Check for stream end sentinel
                if item is _STREAM_END:
                    break

                # If we got an exception, raise it
                if isinstance(item, Exception):
                    # Check if it's a token validation error
                    # Use parent class's unified error handler
                    if isinstance(item, RuntimeError):
                        try:
                            # Try to use unified error handler
                            # If it's a token error, returns standardized error; otherwise re-raises
                            standardized_error = self._handle_token_validation_error(item, "async run loop")
                            # If we get here, it's a token validation error
                            logger.error(f"Token validation failed: {str(item)}, stopping runtime")
                            await self.stop()
                            raise standardized_error from item
                        except RuntimeError as e:
                            # If handler re-raised (not a token error), check if it's the same exception
                            if e is item:
                                # Not a token error, re-raise original
                                raise
                            # Otherwise it's a different RuntimeError from the handler, raise it
                            raise

                    # For non-RuntimeError exceptions, just re-raise
                    raise item

                # Yield the frame
                yield item

        except asyncio.CancelledError:
            # Stream was cancelled, stop the runtime
            await self.stop()
            raise

    async def _initialize_token(self) -> None:
        """Initialize token if provided by user.
        
        If user provided a token, validate and set it.
        If user provided api_secret, token refresh is handled automatically.
        """
        if self._token:
            logger.debug("Token provided, validating...")
            try:
                loop = self._loop or asyncio.get_running_loop()
                is_valid = await loop.run_in_executor(
                    None, 
                    lambda: self.generator._generator.validate_token(self._token, self._verbose)
                )
                if not is_valid:
                    raise ValueError("Token validation failed")
                logger.debug("Token validated and set successfully")
            except Exception as e:
                logger.warning(f"Token validation failed: {e}")
                raise
        # If api_secret is provided, token refresh is handled automatically

    def _initialize_token_sync(self) -> None:
        """Initialize token if provided by user (synchronous version).
        
        If user provided a token, validate and set it.
        If user provided api_secret, token refresh is handled automatically.
        """
        if self._token:
            is_valid = self.generator._generator.validate_token(self._token, self._verbose)
            if not is_valid:
                logger.warning("Token validation failed")
                raise ValueError("Token validation failed")
        # If api_secret is provided, token refresh is handled automatically

    async def start(
        self,
        out_buffer_empty: Optional[BufferEmptyCallback] = None,
        *,
        idle_timeout: float | None = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        """Start the runtime thread."""
        if self._running:
            logger.debug("Runtime already running, skipping start")
            return

        # Start token refresh if api_secret is provided and refresh is not already running
        # This ensures token is available before runtime starts processing
        if self._api_secret and self._api_url and self._model_path:
            if not self.generator.is_token_refresh_running():
                try:
                    # Generate transaction ID before starting token refresh
                    if not self.transaction_id:
                        self._regenerate_transaction_id()
                    
                    # Run token refresh start in executor since it's synchronous
                    loop_exec = loop or asyncio.get_running_loop()
                    success = await loop_exec.run_in_executor(
                        None,
                        self.generator.start_token_refresh,
                        self._api_url,
                        self._api_secret,
                        self._model_path,
                        self._tags,
                        60,  # refresh_interval
                        self._insecure,
                        30.0  # timeout
                    )
                    if success:
                        logger.debug("Token refresh started in start()")
                        self._token_refresh_started = True
                        # startTokenRefresh does synchronous initial token request,
                        # so token is already validated when run_in_executor returns
                    else:
                        logger.error("Failed to start token refresh in start()")
                        raise RuntimeError("Failed to start token refresh")
                except Exception as e:
                    logger.error(f"Failed to start token refresh in start(): {e}")
                    raise
            else:
                # Token refresh already running - just ensure transaction ID is set
                if not self.transaction_id:
                    self._regenerate_transaction_id()
        else:
            # Generate transaction ID only if not already set (prevents bypassing billing)
            if not self.transaction_id:
                self._regenerate_transaction_id()

        # Store the current event loop
        self._loop = loop or asyncio.get_running_loop()
        self._input_buffer.set_loop(self._loop)

        # Clear the stop event
        self._stop_event.clear()

        # Start the runtime thread
        self._running = True
        self._thread = threading.Thread(
            target=self._frame_producer,
            kwargs={"out_buffer_empty": out_buffer_empty, "idle_timeout": idle_timeout},
        )
        self._thread.daemon = True
        self._thread.start()

    async def stop(self) -> None:
        """Stop the runtime thread and token refresh task."""
        if not self._running:
            return

        # Set the stop event
        self._stop_event.set()

        # Token refresh is automatically stopped (BithumanRuntime destructor)
        # Wait for the thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

        # Reset state
        self._running = False

    def _frame_producer(
        self,
        out_buffer_empty: Optional[BufferEmptyCallback] = None,
        *,
        idle_timeout: float | None = None,
    ) -> None:
        """Run the runtime in a separate thread and produce frames."""
        try:
            # Run the runtime and process frames
            out_buffer_empty = out_buffer_empty or self._frame_queue.empty
            frame_iterator = None
            try:
                frame_iterator = super().run(
                    out_buffer_empty, idle_timeout=idle_timeout
                )
            except RuntimeError as e:
                # Catch token validation errors during initialization
                error_msg = str(e)
                if ("Token has expired" in error_msg or 
                    "Token validation failed" in error_msg or
                    "token has expired" in error_msg.lower() or
                    "validation failed" in error_msg.lower()):
                    logger.error(f"Token validation failed during frame iterator initialization: {error_msg}")
                    # Put exception in queue
                    try:
                        self._frame_queue.put(
                            RuntimeError("Token validation failed: token has expired")
                        )
                    except Exception as e2:
                        logger.error(f"Error putting token validation error in frame queue: {e2}")
                    return
                raise
            except Exception as e:
                logger.error(f"Error initializing frame iterator in run(): {e}")
                raise

            if frame_iterator:
                for frame in frame_iterator:
                    if self._stop_event.is_set():
                        logger.debug("Stop event set, stopping frame producer")
                        break

                    # Put the frame in the thread-safe queue (blocks if full for backpressure)
                    try:
                        self._frame_queue.put(frame)
                    except RuntimeError as e:
                        # Catch token validation errors
                        error_msg = str(e).lower()
                        if ("token has expired" in error_msg or
                            "token validation failed" in error_msg or
                            "validation failed" in error_msg):
                            logger.error(f"Token validation failed in frame producer: {str(e)}")
                            self._frame_queue.put(
                                RuntimeError("Token validation failed: token has expired")
                            )
                            logger.debug("Frame producer stopped due to token validation error")
                            break
                        raise

                # Log when frame iterator completes
                logger.debug("Frame iterator completed")
            else:
                logger.error("Frame iterator is None")

        except Exception as e:
            logger.error(f"Exception in frame producer: {e}")
            # If an exception occurs, put it in the frame queue
            try:
                self._frame_queue.put(e)
            except Exception as e2:
                logger.error(f"Error putting exception in frame queue: {e2}")
        finally:
            # Signal end of stream
            try:
                self._frame_queue.put(_STREAM_END)
            except Exception:
                pass
    
    async def load_data_async(self) -> None:
        """Load the workspace and set up related components asynchronously."""
        if self._video_loaded:
            return
        if self.video_graph is None:
            logger.error("Video graph is None. Model may not be set properly.")
            raise ValueError("Video graph is not set. Call set_avatar_model() first.")

        # Run the synchronous load_data in a thread pool
        loop = self._loop or asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, super().load_data)
            self._video_loaded = True
        except Exception as e:
            logger.error(f"Error in load_data: {e}")
            raise


