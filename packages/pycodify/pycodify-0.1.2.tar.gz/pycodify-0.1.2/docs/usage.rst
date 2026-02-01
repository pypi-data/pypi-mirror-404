Usage Guide
===========

Basic Usage
-----------

The simplest way to use pycodify is to generate source code for an object:

.. code-block:: python

   from pycodify import Assignment, generate_python_source
   from dataclasses import dataclass

   @dataclass
   class ProcessingConfig:
       input_path: str = "/data/input"
       output_path: str = "/data/output"
       num_workers: int = 4

   config = ProcessingConfig(
       input_path="/data/production",
       num_workers=8
   )

   code = generate_python_source(
       Assignment("config", config),
       clean_mode=True
   )
   print(code)

Clean Mode vs Explicit Mode
----------------------------

**Clean mode** (default) omits fields that match their default values:

.. code-block:: python

   # Clean mode - concise
   code = generate_python_source(assignment, clean_mode=True)
   # Output: config = ProcessingConfig(input_path='/data/production', num_workers=8)

**Explicit mode** includes all fields for complete reproducibility:

.. code-block:: python

   # Explicit mode - complete
   code = generate_python_source(assignment, clean_mode=False)
   # Output: config = ProcessingConfig(
   #     input_path='/data/production',
   #     output_path='/data/output',
   #     num_workers=8
   # )

Working with Enums
------------------

Enums are serialized with their full qualified names:

.. code-block:: python

   from enum import Enum

   class ImageFormat(Enum):
       JPEG = "jpeg"
       PNG = "png"
       TIFF = "tiff"

   @dataclass
   class ImageConfig:
       format: ImageFormat = ImageFormat.JPEG

   config = ImageConfig(format=ImageFormat.PNG)
   code = generate_python_source(Assignment("config", config))
   # Output includes: from __main__ import ImageFormat
   # config = ImageConfig(format=ImageFormat.PNG)

Handling Import Collisions
---------------------------

When multiple modules have classes with the same name, pycodify automatically aliases them:

.. code-block:: python

   from module_a import Config as ConfigA
   from module_b import Config as ConfigB

   # pycodify detects the collision and generates:
   # from module_a import Config as Config_1
   # from module_b import Config as Config_2
   # obj = Config_1(...)

Nested Dataclasses
-------------------

Nested dataclasses are properly serialized with all necessary imports:

.. code-block:: python

   @dataclass
   class DatabaseConfig:
       host: str = "localhost"
       port: int = 5432

   @dataclass
   class AppConfig:
       database: DatabaseConfig = DatabaseConfig()
       debug: bool = False

   config = AppConfig(
       database=DatabaseConfig(host="prod.db.internal"),
       debug=True
   )

   code = generate_python_source(Assignment("config", config))
   # Generates imports for both DatabaseConfig and AppConfig

Executing Generated Code
------------------------

The generated code is executable Python:

.. code-block:: python

   code = generate_python_source(assignment)
   namespace = {}
   exec(code, namespace)
   recreated_config = namespace["config"]
   assert recreated_config == original_config

