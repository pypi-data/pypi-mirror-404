pycodify Documentation
======================

**pycodify** serializes Python objects to executable Python source code with automatic import resolution.

The key insight: **Python source code is a serialization format.** Rather than inventing a format and writing loaders, pycodify emits code that Python itself interprets. The import system becomes the deserializer.

Quick Start
-----------

.. code-block:: python

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

Features
--------

- **Complete Executable Source**: Generates imports + code, not just expressions
- **Type-Preserving**: Enums, Paths, callables serialize as themselves
- **Collision Handling**: Automatic aliasing for name collisions across modules
- **Clean Mode**: Omit fields matching defaults for concise output
- **Extensible**: Register custom formatters for domain-specific types

Why Python Source?
------------------

| Format | Diffable | Inspectable | Editable | Type-preserving | Cross-version |
|--------|:--------:|:-----------:|:--------:|:---------------:|:-------------:|
| pickle | ✗ | ✗ | ✗ | ✓ | ✗ |
| JSON/YAML | ✓ | ✓ | ✓ | ✗ | ✓ |
| Python source | ✓ | ✓ | ✓ | ✓ | ✓ |

Contents
--------

.. toctree::
   :maxdepth: 2

   usage
   api
   architecture

API Reference
-------------

.. autosummary::
   :toctree: _autosummary

   pycodify.core
   pycodify.formatters
   pycodify.imports

Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

