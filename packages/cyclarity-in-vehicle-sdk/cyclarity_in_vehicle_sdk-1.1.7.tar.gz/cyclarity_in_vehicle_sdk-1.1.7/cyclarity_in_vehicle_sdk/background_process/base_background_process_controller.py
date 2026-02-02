"""Base class for connecting to background RPyC processes."""
from __future__ import annotations

from typing import ClassVar

import rpyc
from pydantic import Field, PrivateAttr

from cyclarity_sdk.expert_builder.runnable.runnable import ContextParsable


class BaseBackgroundProcessController(ContextParsable):
    """Base class for connecting to and controlling background RPyC processes.
    
    This class provides the foundation for client-side controllers that
    connect to RPyC services spawned by BaseBackgroundProcess.
    
    Subclasses should:
    - Set the service_name class attribute to match the server's service name
    - Implement methods that delegate to self._conn.root
    
    The connection is established in setup() and closed in teardown().
    Use as a context manager for automatic resource management.
    
    Example:
        class MyController(BaseBackgroundProcessController):
            service_name: ClassVar[str] = "MY_SERVICE"
            
            def do_something(self) -> str:
                return self._conn.root.do_something()
        
        with MyController() as ctrl:
            result = ctrl.do_something()
    
    Attributes:
        ip: IP address of the RPyC server (default: localhost).
        service_name: RPyC service name for registry-based discovery.
    """
    
    # Class attributes for connection configuration
    ip: ClassVar[str] = Field(default="localhost", description="IP address of the RPyC server")
    service_name: ClassVar[str] = Field(default="BACKGROUND_PROCESS", description="RPyC service name for registry-based discovery")
    
    # Private attribute for the RPyC connection
    _conn: rpyc.Connection | None = PrivateAttr(default=None)
    
    def setup(self) -> None:
        """Connect to the RPyC server.
        
        Uses service registry for discovery based on service_name.
        """
        self.logger.debug(
            f"Connecting to service '{self.service_name}' via registry"
        )
        
        try:
            self._conn = rpyc.connect_by_service(self.service_name)
            self.logger.info(
                f"Connected to service '{self.service_name}'"
            )
        except Exception as e:
            self.logger.error(f"Failed to connect to service '{self.service_name}': {e}")
            raise
        
    def run(self):
        pass

    def teardown(self, exception_type=None, exception_value=None, traceback=None) -> bool:
        """Disconnect from the RPyC server."""
        if self._conn is not None:
            try:
                self._conn.close()
                self.logger.debug(f"Disconnected from service '{self.service_name}'")
            except Exception as e:
                self.logger.warning(f"Error closing connection: {e}")
            finally:
                self._conn = None
        return False
    
    def is_connected(self) -> bool:
        """Check if the connection to the RPyC server is active.
        
        Returns:
            True if connected, False otherwise.
        """
        return self._conn is not None and not self._conn.closed
    
    @property
    def root(self) -> rpyc.core.netref.BaseNetref:
        """Access the remote service root object.
        
        Returns:
            The RPyC proxy to the remote service.
        
        Raises:
            RuntimeError: If not connected.
        """
        if self._conn is None:
            raise RuntimeError(
                f"Not connected to service '{self.service_name}'. "
                "Call setup() first or use as context manager."
            )
        return self._conn.root

