API Reference
=============

Core API
--------

.. automodule:: pycodify.core
   :members:
   :undoc-members:
   :show-inheritance:

Formatters
----------

.. automodule:: pycodify.formatters
   :members:
   :undoc-members:
   :show-inheritance:

Import Resolution
-----------------

.. automodule:: pycodify.imports
   :members:
   :undoc-members:
   :show-inheritance:

Main Functions
--------------

.. py:function:: generate_python_source(assignment: Assignment, clean_mode: bool = True) -> str

   Generate executable Python source code from an object.

   :param assignment: Assignment object specifying variable name and value
   :type assignment: Assignment
   :param clean_mode: If True, omit fields matching defaults. If False, include all fields.
   :type clean_mode: bool
   :return: Executable Python source code with imports
   :rtype: str

   **Example:**

   .. code-block:: python

      from pycodify import Assignment, generate_python_source
      from dataclasses import dataclass

      @dataclass
      class Config:
          name: str = "default"
          value: int = 42

      config = Config(name="production", value=100)
      code = generate_python_source(Assignment("config", config))
      print(code)

.. py:class:: Assignment

   Represents a variable assignment for code generation.

   .. py:method:: __init__(name: str, value: Any)

      Create an assignment.

      :param name: Variable name
      :type name: str
      :param value: Value to serialize
      :type value: Any

.. py:class:: SourceFormatter

   Base class for custom formatters.

   .. py:method:: can_format(value: Any) -> bool

      Check if this formatter can handle the value.

      :param value: Value to check
      :type value: Any
      :return: True if this formatter can format the value
      :rtype: bool

   .. py:method:: format(value: Any, context: FormatContext) -> SourceFragment

      Format a value to source code.

      :param value: Value to format
      :type value: Any
      :param context: Formatting context with state
      :type context: FormatContext
      :return: Source code fragment with imports
      :rtype: SourceFragment

.. py:class:: SourceFragment

   Represents generated source code with its imports.

   .. py:attribute:: code

      The generated Python source code.

   .. py:attribute:: imports

      Set of (module, name) tuples required for the code.

