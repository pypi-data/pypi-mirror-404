Architecture
============

Two-Pass Algorithm
-------------------

Generating executable source requires knowing import aliases before emitting code. But aliases depend on detecting collisions, which requires visiting all types first. This creates a dependency: code generation requires alias resolution, but alias resolution requires traversing the object graph.

pycodify solves this with two passes:

1. **Collection Pass**: Traverse the object, emit code fragments, collect ``(module, name)`` import pairs
2. **Resolution**: Detect collisions (same name, different modules), generate deterministic aliases
3. **Regeneration Pass**: Re-traverse with resolved ``name_mappings``, emit final code

This is not an optimization—it is structurally necessary. A single-pass algorithm cannot know whether ``Config`` needs aliasing until it has seen all types that might also be named ``Config``.

Extensible Formatter Registry
------------------------------

Each type maps to a ``SourceFormatter`` that emits a ``SourceFragment(code, imports)``. Formatters register via ``__init_subclass__``—defining a formatter class automatically adds it to the registry:

.. code-block:: python

   class EnumFormatter(SourceFormatter):
       priority = 70

       def can_format(self, value: Any) -> bool:
           return isinstance(value, Enum)

       def format(self, value: Enum, context: FormatContext) -> SourceFragment:
           cls = value.__class__
           import_pair = (cls.__module__, cls.__name__)
           name = context.name_mappings.get(import_pair, cls.__name__)
           return SourceFragment(f"{name}.{value.name}", frozenset([import_pair]))

Priority-based dispatch selects the most specific formatter. Domain extensions add formatters without modifying core code.

Core Components
---------------

**SourceFormatter**
  Base class for all formatters. Subclasses implement ``can_format()`` and ``format()`` methods.

**SourceFragment**
  Represents a piece of generated code with its required imports.

**FormatContext**
  Carries state during formatting: ``name_mappings``, ``visited_objects``, etc.

**ImportResolver**
  Detects collisions and generates deterministic aliases for imports.

**SourceGenerator**
  Orchestrates the two-pass algorithm and produces final executable code.

Clean Mode
----------

Clean mode omits fields matching their default values. This requires:

1. Accessing the dataclass field defaults
2. Comparing current values to defaults
3. Omitting fields where ``current_value == default_value``

Explicit mode includes all fields for complete reproducibility.

Lazy Dataclass Integration
---------------------------

For dataclasses with ``__getattribute__`` interception (used for hierarchical config inheritance), formatters use ``object.__getattribute__`` to access raw field values without triggering lazy resolution:

.. code-block:: python

   # In DataclassFormatter
   if hasattr(instance, "_resolve_field_value"):
       # Bypass __getattribute__ to get raw None vs concrete value
       current_value = object.__getattribute__(instance, field_name)
   else:
       current_value = getattr(instance, field_name)

This distinguishes explicitly-set values from inherited ones during serialization.

Module Structure
----------------

- **core.py**: Main API (``Assignment``, ``generate_python_source``)
- **formatters.py**: Built-in formatters (dataclass, enum, primitive types)
- **imports.py**: Import resolution and collision handling

