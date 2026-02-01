# pycodify

Python source code as a serialization format with automatic import resolution.

## Quick Start

```python
from pycodify import Assignment, generate_python_source
from dataclasses import dataclass

@dataclass
class Config:
    name: str = "default"
    value: int = 42

config = Config(name="production", value=100)
code = generate_python_source(Assignment("config", config), clean_mode=True)
print(code)
# Output:
# from __main__ import Config
# config = Config(name='production', value=100)
```

## Why Python Source?

| Format | Diffable | Inspectable | Editable | Type-preserving | Cross-version |
|--------|:--------:|:-----------:|:--------:|:---------------:|:-------------:|
| pickle | ✗ | ✗ | ✗ | ✓ | ✗ |
| JSON/YAML | ✓ | ✓ | ✓ | ✗ | ✓ |
| Python source | ✓ | ✓ | ✓ | ✓ | ✓ |

Binary formats like `pickle` cannot be diffed, inspected, or edited. Text formats like JSON lose type information. Python source code has all desired properties: it is diffable, inspectable, editable, type-preserving, and cross-version stable.

## Features

- **Complete Executable Source**: Generates imports + code, not just expressions
- **Type-Preserving**: Enums, Paths, callables serialize as themselves
- **Collision Handling**: Automatic aliasing for name collisions across modules
- **Clean Mode**: Omit fields matching defaults for concise output
- **Extensible**: Register custom formatters for domain-specific types

## Documentation

Full documentation available at [pycodify.readthedocs.io](https://pycodify.readthedocs.io)

## Installation

```bash
pip install pycodify
```

## License

MIT
