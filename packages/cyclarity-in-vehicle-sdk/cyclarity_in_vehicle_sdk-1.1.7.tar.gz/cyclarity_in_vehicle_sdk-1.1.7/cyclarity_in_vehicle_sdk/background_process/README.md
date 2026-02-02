# Background Process Module

This module provides a framework for spawning and controlling background processes within the Cyclarity platform. It leverages [RPyC](https://rpyc.readthedocs.io/) (Remote Python Call) for inter-process communication, enabling test scenarios to interact with long-running background tasks.

## Motivation

Automotive security testing often requires **background services** that must run continuously while test steps execute sequentially. Examples include:

- **Periodic Message Generators** – Send UDS Tester Present to keep sessions alive
- **Traffic Simulators** – Generate CAN/DoIP traffic patterns during tests

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TEST PROCESS                                │
│  ┌────────────────────────┐      ┌────────────────────────────────┐ │
│  │  BaseBackgroundProcess │─────▶│       ProcessHandle            │ │
│  │  (Runnable)            │      │  - pid, service_name           │ │
│  │  - run() → spawns ─────┼──────│  - terminate()                 │ │
│  └────────────────────────┘      └────────────────────────────────┘ │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  BaseBackgroundProcessController (ContextParsable)           │   │
│  │  - setup()    → connects via RPyC registry                   │   │
│  │  - teardown() → disconnects                                  │   │
│  │  - root       → access to exposed_* methods                  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
        │                                    ▲
        │ spawn (multiprocessing)            │ RPyC (connect_by_service)
        ▼                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKGROUND SUBPROCESS                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  BaseCyclarityRpycService (rpyc.Service)                     │   │
│  │  - exposed_*() methods callable by controller                │   │
│  │  - shutdown() called on SIGTERM/SIGINT                       |   |
|  |  - initialize() called after instanciation                   │   │
│  │  - auto_register=True → registers with RPyC registry         │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Purpose |
|-----------|---------|
| `BaseBackgroundProcess[S]` | Runnable that spawns the subprocess, parameterized by service args type `S` |
| `BaseCyclarityRpycService` | Abstract RPyC service base class with lifecycle hooks |
| `BaseServiceArgs` | Pydantic model for service constructor arguments  |
| `BaseBackgroundProcessController` | Client-side controller that connects to the service via RPyC registry |
| `ProcessHandle` | Result model with process metadata and `terminate()` method |

### Service Discovery

The module uses **RPyC's service registry** for discovery:

1. Background process starts `ThreadedServer` with `auto_register=True` and a unique `service_name`
2. The server registers itself with the RPyC registry daemon
3. Controllers connect via `rpyc.connect_by_service(service_name)`


---

## Implementation Guide

To create a background process for the Cyclarity platform, implement these four components:

### 1. Service Arguments (Pydantic Model)

Define what configuration your service needs:

```python
from cyclarity_in_vehicle_sdk.background_process import BaseServiceArgs

class TesterPresentServiceArgs(BaseServiceArgs):
    """Arguments for the Tester Present background service."""
    
    channel: str = "can0"
    txid: int = 0x713
    interval_ms: int = 2000  # Send every 2 seconds
```

### 2. RPyC Service (Runs in Subprocess)

The actual service that runs in the background:

```python
import threading
import time

from cyclarity_in_vehicle_sdk.background_process import BaseCyclarityRpycService
from cyclarity_in_vehicle_sdk.communication.can.impl.can_communicator_socketcan import (
    CanCommunicatorSocketCan,
)

class TesterPresentService(BaseCyclarityRpycService):
    """Background service that periodically sends UDS Tester Present (0x3E 0x80)."""
    
    # Service name auto-derived: TESTER_PRESENT_SERVICE
    # Logger is injected automatically by the spawning function
    
    def __init__(self, args: TesterPresentServiceArgs) -> None:
        super().__init__()
        self._args = args  # Pydantic model passed directly (picklable)
        
        self._running = False
        self._thread: threading.Thread | None = None
        self._can: CanCommunicatorSocketCan | None = None
    
    def initialize(self) -> None:
        pass  # No initialization needed for this simple example
    
    def _send_loop(self) -> None:
        """Background thread that sends Tester Present periodically."""
        tester_present = bytes([0x3E, 0x80])  # UDS Tester Present (suppress response)
        
        while self._running:
            try:
                self._can.send(self._args.txid, tester_present, is_fd=False)
                self.logger.debug(f"Sent Tester Present to 0x{self._args.txid:03X}")
            except Exception:
                self.logger.exception("Failed to send Tester Present")
            
            time.sleep(self._args.interval_ms / 1000.0)
    
    def shutdown(self) -> None:
        """Stop the service (called on SIGTERM/SIGINT)."""
        self.logger.info("Shutting down Tester Present service")
        self._running = False
        
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        
        if self._can is not None:
            self._can.close()
            self._can = None
    
    # --- Exposed RPyC methods (callable by controller) ---
    
    def exposed_start(self) -> None:
        """Start sending Tester Present messages."""
        if self._running:
            return
        
        self._can = CanCommunicatorSocketCan(channel=self._args.channel)
        self._can.setup()
        
        self._running = True
        self._thread = threading.Thread(target=self._send_loop, daemon=True)
        self._thread.start()
        self.logger.info(f"Started Tester Present on {self._args.channel}")
    
    def exposed_stop(self) -> None:
        """Stop sending Tester Present messages."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        self.logger.info("Stopped Tester Present")
    
    def exposed_is_running(self) -> bool:
        """Check if the service is actively sending."""
        return self._running
    
    def exposed_set_interval(self, interval_ms: int) -> None:
        """Change the send interval dynamically."""
        self._args.interval_ms = interval_ms
        self.logger.info(f"Interval changed to {interval_ms}ms")
```

### 3. Background Process (Runnable Spawner)

A `Runnable` that spawns the service in a subprocess:

```python
from cyclarity_in_vehicle_sdk.background_process import BaseBackgroundProcess
from my_package.services.tester_present import TesterPresentService

class TesterPresentProcess(BaseBackgroundProcess[TesterPresentServiceArgs]):
    """Spawns the Tester Present background service."""
    
    # Direct reference to service class - service_name is derived automatically
    service_class = TesterPresentService
    service_args: TesterPresentServiceArgs
```

### 4. Controller (Client-Side Interface)

A controller for test steps to interact with the service:

```python
from cyclarity_in_vehicle_sdk.background_process import BaseBackgroundProcessController

class TesterPresentController(BaseBackgroundProcessController):
    """Client controller for the Tester Present background service."""
    
    service_name = "TESTER_PRESENT_SERVICE"
    
    def start(self) -> None:
        """Start sending Tester Present."""
        self.root.start()
    
    def stop(self) -> None:
        """Stop sending Tester Present."""
        self.root.stop()
    
    def is_running(self) -> bool:
        """Check if actively sending."""
        return self.root.is_running()
    
    def set_interval(self, interval_ms: int) -> None:
        """Adjust the send interval."""
        self.root.set_interval(interval_ms)
```

---

## Summary

| You Implement | Base Class | Purpose |
|---------------|------------|---------|
| `MyServiceArgs` | `BaseServiceArgs` | Configuration for your service |
| `MyService` | `BaseCyclarityRpycService` | The actual background service logic |
| `MyProcess` | `BaseBackgroundProcess[MyServiceArgs]` | Spawns the subprocess |
| `MyController` | `BaseBackgroundProcessController` | Client interface for test steps |

The framework handles:
- Process spawning and lifecycle management
- Cross-process log forwarding
- RPyC service registration and discovery
- Graceful shutdown on signals (SIGTERM/SIGINT)
- Pydantic serialization for cross-process argument passing
