# Mantisdk

[![PyPI version](https://badge.fury.io/py/mantisdk.svg)](https://badge.fury.io/py/mantisdk)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**AI Agent Training and Evaluation Platform**

Mantisdk is a comprehensive toolkit for training and evaluating AI agents using reinforcement learning, automatic prompt optimization, and supervised fine-tuning.

## Core Features

- Turn your agent into an optimizable beast with **minimal code changes**
- Build with **any** agent framework (LangChain, OpenAI Agent SDK, AutoGen, CrewAI, and more)
- **Selectively** optimize one or more agents in a multi-agent system
- Embraces **algorithms** like Reinforcement Learning, Automatic Prompt Optimization, Supervised Fine-tuning and more

## Installation

```bash
pip install mantisdk
```

For optional dependencies:

```bash
# For APO (Automatic Prompt Optimization)
pip install mantisdk[apo]

# For VERL integration
pip install mantisdk[verl]

# For Weave integration
pip install mantisdk[weave]

# For MongoDB store
pip install mantisdk[mongo]
```

## Quick Start

```python
import mantisdk as msk

# Initialize the client
client = msk.MantisdkClient()

# Your agent code here...
```

## CLI Usage

```bash
# Start the Mantisdk server
msk store serve

# Run with vLLM
msk vllm start
```

## Documentation

For full documentation, visit [https://withmetis.github.io/mantis/mantisdk/](https://withmetis.github.io/mantis/mantisdk/)

## License

MIT License - see [LICENSE](LICENSE) for details.
