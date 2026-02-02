"""Base class for RPyC services used with BaseBackgroundProcess."""
from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from typing import ClassVar

import rpyc
from pydantic import BaseModel
from rpyc.core import Connection


class BaseServiceArgs(BaseModel):
    """Base class for RPyC service constructor arguments."""
    pass


def _camel_to_screaming_snake(name: str) -> str:
    """Convert CamelCase to SCREAMING_SNAKE_CASE.
    
    Examples:
        SokFreshnessServerService -> SOK_FRESHNESS_SERVER_SERVICE
        MyService -> MY_SERVICE
    """
    # Insert underscore before uppercase letters (except at start)
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    # Insert underscore before uppercase letters followed by lowercase
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.upper()


class BaseCyclarityRpycService(rpyc.Service, ABC):
    """Base class for RPyC services spawned by BaseBackgroundProcess.
    
    Provides:
    - Automatic service name derivation (or explicit override)
    - Logger injection via set_logger() (called by spawning function)
    - on_connect/on_disconnect hooks with logging
    - Abstract initialize() and shutdown() methods for lifecycle management
    
    Subclasses must implement:
    - initialize(): Called after logger is set, before RPyC server starts
    - shutdown(): Called when the process receives SIGTERM/SIGINT
    
    The service_name is automatically derived from the class name if not set:
        SokFreshnessServerService -> SOK_FRESHNESS_SERVER_SERVICE
    
    Example:
        class MyService(BaseCyclarityRpycService):
            def __init__(self, args: MyServiceArgs):
                super().__init__()
                self._args = args
                # Initialize your service...
            
            def shutdown(self) -> None:
                # Cleanup resources...
                pass
    """
    
    # Override to set explicit service name, otherwise derived from class name
    service_name: ClassVar[str] = ""
    
    # Logger is set by spawning function via set_logger()
    _logger: logging.Logger | None = None
    
    def __init_subclass__(cls, **kwargs: object) -> None:
        """Auto-derive service_name and set ALIASES when subclass is defined."""
        super().__init_subclass__(**kwargs)
        
        # Auto-derive service_name if not explicitly set
        if not cls.service_name:
            cls.service_name = _camel_to_screaming_snake(cls.__name__)
        
        # Set ALIASES for RPyC registry
        cls.ALIASES = [cls.service_name]
    
    @property
    def logger(self) -> logging.Logger:
        """Get the service logger. Creates default if not set."""
        if self._logger is None:
            self._logger = logging.getLogger(self.__class__.__name__)
        return self._logger
    
    def set_logger(self, logger: logging.Logger) -> None:
        """Set the service logger. Called by spawning function."""
        self._logger = logger
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the service
        """
        ...
    
    def on_connect(self, conn: Connection) -> None:
        """Called when a client connects."""
        self.logger.info("Client connected")
    
    def on_disconnect(self, conn: Connection) -> None:
        """Called when a client disconnects."""
        self.logger.info("Client disconnected")
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the service and release all resources.
        
        Called when the RPyC server is being closed (e.g., on SIGTERM/SIGINT).
        Implementations should stop any running tasks, close connections,
        and release resources.
        """
        ...

