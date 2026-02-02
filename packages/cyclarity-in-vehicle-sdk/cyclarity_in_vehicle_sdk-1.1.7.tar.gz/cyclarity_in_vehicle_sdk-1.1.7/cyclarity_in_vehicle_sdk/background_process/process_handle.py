"""Process handle for background processes spawned via RPyC."""
from __future__ import annotations

import multiprocessing

from pydantic import PrivateAttr

from cyclarity_sdk.expert_builder.runnable.runnable import BaseResultsModel


class ProcessHandle(BaseResultsModel):
    """Result returned by BaseBackgroundProcess.run().
    
    Contains the process metadata and provides methods for lifecycle management.
    This is a Pydantic model that can be serialized/deserialized.
    
    Attributes:
        pid: Process ID of the spawned subprocess.
        service_name: RPyC service name for registry-based discovery.
    """
    
    pid: int
    service_name: str
    
    # Private attributes (not serialized)
    _process: multiprocessing.Process | None = PrivateAttr(default=None)
    
    def is_alive(self) -> bool:
        """Check if the subprocess is still running.
        
        Returns:
            True if the process is alive, False otherwise.
        """
        return self._process is not None and self._process.is_alive()
    
    def terminate(self, timeout: float = 5.0) -> None:
        """Terminate the subprocess.
        
        Attempts graceful termination first, then kills if necessary.
        
        Args:
            timeout: Seconds to wait for graceful shutdown before killing.
        """
        if self._process is not None and self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout=timeout)
            
            if self._process.is_alive():
                self._process.kill()
                self._process.join(timeout=1.0)
    
    def set_process(self, process: multiprocessing.Process) -> None:
        """Set the process reference (called internally after spawn).
        
        Args:
            process: The multiprocessing.Process instance.
        """
        self._process = process
