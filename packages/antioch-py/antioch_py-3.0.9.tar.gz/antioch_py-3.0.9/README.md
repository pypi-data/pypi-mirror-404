# antioch-py

The Antioch Python Module SDK for building deterministic robotic modules.

## Overview

`antioch-py` provides the Python client library for implementing Antioch modules - the core computational units that run inside Arks. Modules contain nodes that execute callbacks on a deterministic schedule, communicating via tokens.

## Installation

```bash
pip install antioch-py
```

## Quick Start

```python
from antioch import Module, Execution

def my_callback(execution: Execution) -> None:
    """Process inputs and produce outputs."""
    # Read input data
    input_data = execution.input("sensor_data")
    
    # Process data
    result = process(input_data)
    
    # Write output
    execution.output("processed", result)

# Create and run module
module = Module()
module.register("my_node", my_callback)
module.spin()
```

## Key Concepts

### Module

The `Module` class is the main entry point for implementing Antioch modules. It handles:
- Configuration loading from environment (container mode) or explicit parameters (local mode)
- Node registration and lifecycle management
- Startup handshake and synchronization

### Node

Nodes are the computational units within a module. Each node:
- Runs in its own thread
- Executes on a deterministic schedule
- Receives input tokens and produces output tokens

### Execution

The `Execution` object is passed to node callbacks and provides:
- Access to input data via `input(name)`
- Output publishing via `output(name, data)`
- Hardware read/write for simulation mode
- Logging via `execution.logger`

## Modes of Operation

### Container Mode (Default)

When running inside an Ark pod, the module automatically loads configuration from environment variables:
- `_MODULE_NAME`: Module name
- `_ARK`: Ark configuration JSON
- `_ENVIRONMENT`: Execution environment (sim/real)
- `_DEBUG`: Debug mode flag

### Local Mode

For testing and development, provide configuration explicitly:

```python
from antioch import Module, Environment

module = Module(
    module_name="my_module",
    ark=my_ark_config,
    environment=Environment.SIM,
    debug=True,
)
```

## API Reference

### Module

- `Module(module_name=None, ark=None, environment=Environment.REAL, debug=False)`: Create a module
- `register(name, callback)`: Register a node callback
- `spin()`: Start the module and wait for shutdown
- `join(timeout=None)`: Wait for all nodes to finish

### Execution

- `input(name) -> list[Token]`: Get input tokens for an input
- `output(name, data)`: Set output data for an output
- `hardware_read(name) -> bytes`: Read hardware data (sim mode)
- `hardware_write(name, data)`: Write hardware data (sim mode)
- `logger`: Logger for telemetry and debugging

## License

MIT
