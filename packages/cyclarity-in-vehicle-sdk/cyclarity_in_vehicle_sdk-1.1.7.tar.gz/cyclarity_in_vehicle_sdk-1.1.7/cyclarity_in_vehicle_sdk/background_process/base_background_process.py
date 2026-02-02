"""Base class for spawning background processes with RPyC communication."""
from __future__ import annotations

import importlib
import logging
import multiprocessing
import signal
from logging.handlers import QueueHandler, QueueListener
from typing import Any, ClassVar, Generic, TypeVar

from pydantic import PrivateAttr
from rpyc.utils.server import ThreadedServer

from cyclarity_sdk.expert_builder.runnable.runnable import Runnable

from cyclarity_in_vehicle_sdk.background_process.process_handle import ProcessHandle
from cyclarity_in_vehicle_sdk.background_process.base_rpyc_service import BaseServiceArgs, BaseCyclarityRpycService


# Type variable for service arguments
S = TypeVar("S", bound=BaseServiceArgs)


def _run_background_process(
    service_class_path: str,
    service_args: BaseServiceArgs,
    service_name: str,
    log_queue: multiprocessing.Queue | None,
    logger_name: str,
    logger_level: int,
) -> None:
    """Entry point for the background subprocess.
    
    This function runs in the spawned subprocess. It:
    1. Sets up logging via QueueHandler (if log_queue provided)
    2. Dynamically imports and instantiates the RPyC service class
    3. Starts the ThreadedServer with auto_register=True
    
    Args:
        service_class_path: Fully qualified path to the service class
            (e.g., "mypackage.module.MyService").
        service_args: Arguments to pass to the service constructor (Pydantic model).
        service_name: RPyC service name for registry.
        log_queue: Queue for sending log records to parent process.
        logger_name: Name for the subprocess logger.
        logger_level: Logging level for the subprocess logger.
    """
    # Set up logging via queue
    logger: logging.Logger | None = None
    if log_queue is not None:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logger_level)
        logger.handlers.clear()
        queue_handler = QueueHandler(log_queue)
        logger.addHandler(queue_handler)
        logger.propagate = False
        logger.info(f"Background process started with service name: {service_name}")
    
    server: ThreadedServer | None = None
    service: Any = None
    
    def shutdown_handler(signum: int, frame: Any) -> None:
        """Handle SIGTERM/SIGINT by gracefully closing the server."""
        nonlocal server, service
        if logger:
            logger.info(f"Received signal {signum}, shutting down...")
        
        # Call service.shutdown() if available (for cleanup like FreshnessServer.stop())
        if service is not None and hasattr(service, "shutdown"):
            try:
                service.shutdown()
            except Exception:
                if logger:
                    logger.exception("Error during service shutdown")
        
        # Close the RPyC server (unregisters from registry, closes sockets)
        if server is not None:
            try:
                server.close()
            except Exception:
                if logger:
                    logger.exception("Error closing server")
    
    # Install signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    try:
        # Dynamically import the service class
        module_path, class_name = service_class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        service_class = getattr(module, class_name)
        
        # Instantiate the service, set logger, and initialize
        service = service_class(args=service_args)
        if logger is not None:
            service.set_logger(logger)
        # Initialize service
        service.initialize()
        
        # Create and start the RPyC server
        # Using port=0 for dynamic port assignment, auto_register for service discovery
        server = ThreadedServer(
            service,
            port=0,
            auto_register=True,
            protocol_config={"allow_public_attrs": True},
        )
        
        if logger:
            logger.info(f"RPyC server starting on port {server.port}")
        
        # This blocks until the server is stopped (via server.close())
        server.start()
        
        if logger:
            logger.info("RPyC server stopped")
        
    except Exception as e:
        if logger:
            logger.exception(f"Background process error: {e}")
        raise
    finally:
        # Ensure cleanup happens even on unexpected errors
        if service is not None and hasattr(service, "shutdown"):
            try:
                service.shutdown()
            except Exception:
                pass
        if server is not None:
            try:
                server.close()
            except Exception:
                pass


class BaseBackgroundProcess(Runnable[ProcessHandle], Generic[S]):
    """Base class for spawning background processes with RPyC communication.
    
    This is a generic class parameterized by S (service args type).
    Subclasses must:
    - Set service_class: ClassVar pointing to the RPyC service class
    - Define service_args: S attribute with the service arguments
    
    The spawned process will:
    - Register with the RPyC registry using service_name (derived from service_class)
    - Forward logs to the parent process via QueueHandler/QueueListener
    - Pass service_args (serialized) to the service constructor
    
    Example:
        from mypackage.services import MyService
        
        class MyServiceArgs(BaseServiceArgs):
            settings: MySettings
        
        class MyServerProcess(BaseBackgroundProcess[MyServiceArgs]):
            service_class = MyService
            service_args: MyServiceArgs
        
        with MyServerProcess(service_args=MyServiceArgs(settings=...)) as process:
            handle = process()  # Spawns subprocess, returns ProcessHandle
            # ... use handle ...
            handle.terminate()
    """
    
    # Subclasses must set this to the RPyC service class
    service_class: ClassVar[type[BaseCyclarityRpycService]]
    
    # Class attributes for RPyC configuration
    ip: ClassVar[str] = "localhost"
    
    # Service arguments - must be defined by subclass
    service_args: S
    
    # Private attributes
    _handle: ProcessHandle = PrivateAttr(default=None)
    _log_queue: multiprocessing.Queue = PrivateAttr(default=None)
    _log_listener: QueueListener = PrivateAttr(default=None)
    
    @classmethod
    def _get_service_class_path(cls) -> str:
        """Derive the fully qualified path from service_class."""
        return f"{cls.service_class.__module__}.{cls.service_class.__name__}"
    
    @classmethod
    def _get_service_name(cls) -> str:
        """Get service name from the service class."""
        return cls.service_class.service_name
    
    def setup(self) -> None:
        """Setup before spawning the process."""
        self.logger.debug(f"Setting up {self.__class__.__name__}")
    
    def run(self) -> ProcessHandle:
        """Spawn the background process and return a handle.
        
        Returns:
            ProcessHandle with process metadata and control methods.
        """
        # Set up cross-process logging
        self._setup_log_forwarding()
        
        # Get logger info for subprocess
        logger_name = f"{self.logger.name}"
        logger_level = self.logger.getEffectiveLevel()
        
        # Get service configuration (derived from service_class)
        service_class_path = self._get_service_class_path()
        service_name = self._get_service_name()
        
        # Spawn the subprocess
        process = multiprocessing.Process(
            target=_run_background_process,
            args=(
                service_class_path,
                self.service_args,
                service_name,
                self._log_queue,
                logger_name,
                logger_level,
            ),
            name=f"bg-{service_name.lower()}",
            daemon=True,
        )
        process.start()
        
        self.logger.info(f"Spawned background process (pid={process.pid}, service={service_name})")
        
        # Create the handle
        handle = ProcessHandle(
            pid=process.pid,
            service_name=service_name,
        )
        handle.set_process(process)
        
        self._handle = handle
        return handle
    
    def teardown(self, exception_type=None, exception_value=None, traceback=None) -> bool:
        """Teardown - terminate the process if still running."""
        if self._handle is not None and self._handle.is_alive():
            self.logger.info("Terminating background process in teardown")
            self._handle.terminate()
        return False
    
    def _setup_log_forwarding(self) -> None:
        """Set up QueueListener to forward logs from subprocess."""
        # Collect all handlers from logger hierarchy
        handlers: list[logging.Handler] = []
        current: logging.Logger | None = self.logger
        
        while current:
            handlers.extend(current.handlers)
            if not current.propagate:
                break
            current = current.parent  # type: ignore[assignment]
        
        if handlers:
            self._log_queue = multiprocessing.Queue(-1)
            self._log_listener = QueueListener(
                self._log_queue,
                *handlers,
                respect_handler_level=True,
            )
            self._log_listener.start()
            self.logger.debug("Log forwarding configured")
