# Copyright (c) Microsoft. All rights reserved.

"""Put components in this file to make them available to the Trainer.

Currently only used for ExecutionStrategy.
"""

ExecutionStrategyRegistry = {
    "shm": "mantisdk.execution.shared_memory.SharedMemoryExecutionStrategy",
    # "ipc": "mantisdk.execution.inter_process.InterProcessExecutionStrategy",
    "cs": "mantisdk.execution.client_server.ClientServerExecutionStrategy",
}
